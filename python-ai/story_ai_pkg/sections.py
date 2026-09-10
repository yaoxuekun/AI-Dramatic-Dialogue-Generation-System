# 分卷小节业务模块
# 本文件负责将某一卷大纲拆解为多个小节并逐节生成具体故事细节。
# 包含一个 FastAPI 端点和一个内部生成函数：
# - POST /api/story/volume-sections：HTTP 调试入口
# - generate_volume_sections：内部生成函数，被 RabbitMQ Worker 和 HTTP 端点共用

# time：用于计算请求耗时
import time

# uuid：用于生成请求追踪 ID
import uuid

# Callable：用于声明回调函数类型（逐节增量回传）
from collections.abc import Callable

# HTTPException：FastAPI HTTP 异常
from fastapi import HTTPException

# 从 ai_runtime 导入共享的 LLM 实例和工具函数
from ai_runtime import (
    ConsoleStreamingCallback,
    invoke_llm_with_retry,
    invoke_structured_output_with_guard,
    llm_temperature_0,
    log_progress,
    streaming_text_llm_base,
)

# 从 formatters 导入文本格式化工具
from .formatters import (
    build_characters_text,                  # 角色设定转文本
    extract_llm_text,                       # 提取 LLM 纯文本响应
    format_volume_section_context,          # 已生成小节转上下文
    parse_volume_section_text,              # 解析标签格式小节文本
)

# 从 models 导入数据模型
from .models import (
    StoryVolumeSectionGenerateRequest,      # 小节生成请求
    StoryVolumeSectionGenerateResponse,     # 小节生成响应
    VolumeSectionCountOutput,               # 小节数量规划输出
    VolumeSectionItem,                      # 单个小节
)

# 从 router 导入路由器
from .router import router

# 从 templates 导入提示词模板加载函数
from .templates import load_prompt_template


@router.post("/api/story/volume-sections", response_model=StoryVolumeSectionGenerateResponse)
def generate_volume_sections_endpoint(request: StoryVolumeSectionGenerateRequest) -> StoryVolumeSectionGenerateResponse:
    """HTTP 调试入口，实际生成逻辑委托给 generate_volume_sections 内部函数。

    Args:
        request: 小节生成请求体。

    Returns:
        StoryVolumeSectionGenerateResponse: 小节列表。
    """
    return generate_volume_sections(request)


def generate_volume_sections(
    request: StoryVolumeSectionGenerateRequest,
    on_section_generated: Callable[[VolumeSectionItem], None] | None = None,
) -> StoryVolumeSectionGenerateResponse:
    """先规划某一卷的小节数量，再逐小节生成具体故事细节。

    两阶段生成流程：
    第一阶段：使用温度为 0 的模型判断小节数量（4-12 节）
    第二阶段：按节号循环，逐节生成故事细节，每节携带前序节作为上下文

    Args:
        request:              小节生成请求体。
        on_section_generated: 可选的逐节进度回调，每生成一节就调用一次（用于 RabbitMQ 增量回传）。

    Returns:
        StoryVolumeSectionGenerateResponse: 包含所有小节的列表。
    """
    # 生成追踪 ID
    trace_id = uuid.uuid4().hex[:8]
    started_at = time.perf_counter()
    scope = "volume-sections"

    # 校验必填参数
    if not request.outline or not request.outline.strip():
        raise HTTPException(status_code=400, detail="Story outline is required before generating volume sections")
    if not request.volume_outline.content or not request.volume_outline.content.strip():
        raise HTTPException(status_code=400, detail="Volume outline content is required before generating sections")

    # 打印请求接收日志
    log_progress(
        trace_id,
        (
            f"request accepted, user_id={request.user_id}, story_id={request.story_id}, "
            f"volume_id={request.volume_id}, volume={request.volume_outline.volume_number}"
        ),
        started_at,
        scope,
    )

    # 将角色设定转为提示词文本
    characters_text = build_characters_text(request.main_characters)

    # ── 第一阶段：规划小节数量 ──────────────────────────────────────────
    count_llm = llm_temperature_0.with_structured_output(VolumeSectionCountOutput)
    count_chain = load_prompt_template(
        "generate_volume_section_count",
        genre=request.genre,
        story_style=request.story_style,
    ) | count_llm
    log_progress(trace_id, "planning section count with temperature=0 structured output", started_at, scope)

    count_result = invoke_structured_output_with_guard(
        count_chain,
        {
            "Title": request.title,
            "Theme": request.genre or "未指定",
            "StoryStyle": request.story_style or "高质量国漫/漫剧视觉",
            "StorySummary": request.story_summary or "",
            "Outline": request.outline,
            "Characters": characters_text,
            "VolumeNumber": request.volume_outline.volume_number,
            "VolumeTitle": request.volume_outline.title,
            "VolumeSummary": request.volume_outline.summary or "",
            "VolumeContent": request.volume_outline.content,
            "EndingHook": request.volume_outline.ending_hook or "",
        },
        VolumeSectionCountOutput,
        config={"callbacks": [ConsoleStreamingCallback(trace_id, scope)]},
        trace_id=trace_id,
        started_at=started_at,
        scope=scope,
    )
    total_sections = count_result.section_count
    log_progress(trace_id, f"section count planned: {total_sections}", started_at, scope)

    # ── 第二阶段：逐节生成故事细节 ──────────────────────────────────────
    # 使用流式文本 LLM，小节内容使用纯文本标签格式输出
    section_chain = load_prompt_template(
        "generate_volume_section_single",
        genre=request.genre,
        story_style=request.story_style,
    ) | streaming_text_llm_base

    # 存储已生成的小节列表
    generated_sections: list[VolumeSectionItem] = []

    # 按节号循环生成
    for section_number in range(1, total_sections + 1):
        log_progress(trace_id, f"generating section {section_number}/{total_sections}", started_at, scope)

        # 调用大模型生成当前节（纯文本输出）
        raw_section = invoke_llm_with_retry(
            section_chain,
            {
                "Title": request.title,
                "Theme": request.genre or "未指定",
                "StoryStyle": request.story_style or "高质量国漫/漫剧视觉",
                "StorySummary": request.story_summary or "",
                "Outline": request.outline,
                "Characters": characters_text,
                "VolumeNumber": request.volume_outline.volume_number,
                "VolumeTitle": request.volume_outline.title,
                "VolumeSummary": request.volume_outline.summary or "",
                "VolumeContent": request.volume_outline.content,
                "EndingHook": request.volume_outline.ending_hook or "",
                "TotalSections": total_sections,
                "CurrentSectionNumber": section_number,
                # 将已生成的前序节作为上下文传入
                "GeneratedSections": format_volume_section_context(generated_sections),
            },
            config={"callbacks": [ConsoleStreamingCallback(trace_id, scope)]},
            trace_id=trace_id,
            started_at=started_at,
            scope=scope,
        )

        # 从纯文本响应中提取并解析小节结构
        # 使用标签格式（<title>、<content> 等）而非 JSON，避免长正文转义问题
        section = parse_volume_section_text(extract_llm_text(raw_section), section_number)

        # 添加到已生成列表
        generated_sections.append(section)

        log_progress(trace_id, f"section {section_number}/{total_sections} generated: {section.title}", started_at, scope)

        # 如果注册了逐节回调，立即通知调用方
        if on_section_generated:
            on_section_generated(section)

    # 校验是否生成了小节
    if not generated_sections:
        raise HTTPException(status_code=502, detail="Tongyi model returned no volume sections")

    # 构建响应
    log_progress(trace_id, f"model returned {len(generated_sections)} sections, preparing response", started_at, scope)
    response = StoryVolumeSectionGenerateResponse(sections=generated_sections)
    log_progress(trace_id, "volume sections response ready", started_at, scope)
    return response
