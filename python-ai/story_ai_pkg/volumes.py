# 分卷大纲业务模块
# 本文件负责分卷大纲的生成、修改和分卷正文生成，包含三个 FastAPI 端点：
# - POST /api/story/volume-outline：生成分卷大纲（两阶段：先规划卷数，再逐卷生成）
# - POST /api/story/volume-outline/revise：修改分卷大纲
# - POST /api/story/volume-story：生成分卷正文

# time：用于计算请求耗时
import time

# uuid：用于生成请求追踪 ID
import uuid

# Callable：用于声明回调函数类型（逐卷增量回传）
from collections.abc import Callable

# HTTPException：FastAPI HTTP 异常
from fastapi import HTTPException

# 从 ai_runtime 导入共享的 LLM 实例和工具函数
from ai_runtime import (
    ConsoleStreamingCallback,
    invoke_llm_with_retry,
    invoke_structured_output_with_guard,
    log_progress,
    llm_temperature_0,
    structured_llm_base,
)

# 从 formatters 导入文本格式化工具
from .formatters import build_characters_text, extract_llm_text, format_volume_outline_context

# 从 models 导入数据模型
from .models import (
    StoryVolumeOutlineGenerateRequest,       # 分卷大纲生成请求
    StoryVolumeOutlineGenerateResponse,      # 分卷大纲生成响应
    StoryVolumeOutlineReviseRequest,         # 分卷大纲修改请求
    StoryVolumeStoryGenerateRequest,         # 分卷正文生成请求
    StoryVolumeStoryGenerateResponse,        # 分卷正文生成响应
    VolumeCountOutput,                       # 分卷数量规划输出
    VolumeOutlineItem,                       # 单卷大纲条目
    VolumeOutlineOutput,                     # 分卷大纲结构化输出
)

# 从 router 导入路由器
from .router import router

# 从 templates 导入提示词模板加载函数
from .templates import load_prompt_template


@router.post("/api/story/volume-outline", response_model=StoryVolumeOutlineGenerateResponse)
def generate_volume_outline(
    request: StoryVolumeOutlineGenerateRequest,
    on_volume_generated: Callable[[VolumeOutlineItem], None] | None = None,
) -> StoryVolumeOutlineGenerateResponse:
    """先规划总分卷数，再逐卷生成连续一致的详细分卷大纲。

    两阶段生成流程：
    第一阶段：使用温度为 0 的模型判断总分卷数（5-20 卷）
    第二阶段：按卷号循环，逐卷生成详细大纲，每卷携带前序卷作为上下文

    Args:
        request:             分卷大纲生成请求体。
        on_volume_generated: 可选的逐卷进度回调，每生成一卷就调用一次（用于 RabbitMQ 增量回传）。

    Returns:
        StoryVolumeOutlineGenerateResponse: 包含所有分卷大纲的列表。
    """
    # 生成追踪 ID
    trace_id = uuid.uuid4().hex[:8]
    started_at = time.perf_counter()
    scope = "volume-outline"

    # 校验故事大纲是否存在
    if not request.outline or not request.outline.strip():
        raise HTTPException(status_code=400, detail="Story outline is required before generating volume outlines")

    # 打印请求接收日志
    log_progress(
        trace_id,
        f"request accepted, user_id={request.user_id}, story_id={request.story_id}, title={request.title}",
        started_at,
        scope,
    )

    # 将角色设定转为提示词文本
    characters_text = build_characters_text(request.main_characters)

    # ── 第一阶段：规划总分卷数 ──────────────────────────────────────────
    # 使用温度为 0 的模型，输出最确定性的分卷数量
    count_llm = llm_temperature_0.with_structured_output(VolumeCountOutput)
    count_chain = load_prompt_template(
        "generate_volume_count",
        genre=request.genre,
        story_style=request.story_style,
    ) | count_llm
    log_progress(trace_id, "planning total volume count with temperature=0 structured output", started_at, scope)

    count_result = invoke_structured_output_with_guard(
        count_chain,
        {
            "Title": request.title,
            "Theme": request.genre or "未指定",
            "StoryStyle": request.story_style or "高质量国漫/漫剧视觉",
            "StorySummary": request.story_summary or "",
            "Outline": request.outline,
            "Characters": characters_text,
        },
        VolumeCountOutput,
        config={"callbacks": [ConsoleStreamingCallback(trace_id, scope)]},
        trace_id=trace_id,
        started_at=started_at,
        scope=scope,
    )
    total_volumes = count_result.volume_count
    log_progress(trace_id, f"volume count planned: {total_volumes}", started_at, scope)

    # ── 第二阶段：逐卷生成详细大纲 ──────────────────────────────────────
    # 创建单卷生成 LLM，绑定 VolumeOutlineItem 模型
    single_volume_llm = structured_llm_base.with_structured_output(VolumeOutlineItem)
    single_volume_chain = load_prompt_template(
        "generate_volume_outline_single",
        genre=request.genre,
        story_style=request.story_style,
    ) | single_volume_llm

    # 存储已生成的分卷列表
    generated_volumes: list[VolumeOutlineItem] = []

    # 按卷号循环生成
    for volume_number in range(1, total_volumes + 1):
        log_progress(trace_id, f"generating volume {volume_number}/{total_volumes}", started_at, scope)

        # 调用大模型生成当前卷
        volume = invoke_structured_output_with_guard(
            single_volume_chain,
            {
                "Title": request.title,
                "Theme": request.genre or "未指定",
                "StoryStyle": request.story_style or "高质量国漫/漫剧视觉",
                "StorySummary": request.story_summary or "",
                "Outline": request.outline,
                "Characters": characters_text,
                "TotalVolumes": total_volumes,
                "CurrentVolumeNumber": volume_number,
                # 将已生成的前序分卷作为上下文传入，保证连续性
                "GeneratedVolumeOutlines": format_volume_outline_context(generated_volumes),
            },
            VolumeOutlineItem,
            config={"callbacks": [ConsoleStreamingCallback(trace_id, scope)]},
            trace_id=trace_id,
            started_at=started_at,
            scope=scope,
        )

        # 设置卷号（大模型可能返回错误的卷号）
        volume.volume_number = volume_number

        # 添加到已生成列表
        generated_volumes.append(volume)

        log_progress(trace_id, f"volume {volume_number}/{total_volumes} generated: {volume.title}", started_at, scope)

        # 如果注册了逐卷回调，立即通知调用方（用于 RabbitMQ 增量回传）
        if on_volume_generated:
            on_volume_generated(volume)

    # 校验是否生成了分卷
    if not generated_volumes:
        raise HTTPException(status_code=502, detail="Tongyi model returned no volume outlines")

    # 构建响应
    log_progress(trace_id, f"model returned {len(generated_volumes)} volume outlines, preparing HTTP response", started_at, scope)
    response = StoryVolumeOutlineGenerateResponse(volumes=generated_volumes)
    log_progress(trace_id, "response ready", started_at, scope)
    return response


@router.post("/api/story/volume-outline/revise", response_model=StoryVolumeOutlineGenerateResponse)
def revise_volume_outline(request: StoryVolumeOutlineReviseRequest) -> StoryVolumeOutlineGenerateResponse:
    """根据用户修改意见、原分卷大纲和故事上下文自动重写分卷大纲。

    处理流程：
    1. 校验必填参数
    2. 将角色设定和现有分卷大纲转为提示词文本
    3. 创建结构化输出链，调用大模型重写
    4. 返回修改后的分卷大纲列表

    Args:
        request: 分卷大纲修改请求体。

    Returns:
        StoryVolumeOutlineGenerateResponse: 修改后的分卷大纲列表。
    """
    # 生成追踪 ID
    trace_id = uuid.uuid4().hex[:8]
    started_at = time.perf_counter()
    scope = "volume-outline-revise"

    # 校验必填参数
    if not request.outline or not request.outline.strip():
        raise HTTPException(status_code=400, detail="Story outline is required before revising volume outlines")
    if not request.volume_outlines:
        raise HTTPException(status_code=400, detail="Existing volume outlines are required before revision")
    if not request.suggestion or not request.suggestion.strip():
        raise HTTPException(status_code=400, detail="Modification request is required")

    # 打印请求接收日志
    log_progress(
        trace_id,
        f"revision request accepted, user_id={request.user_id}, story_id={request.story_id}, title={request.title}",
        started_at,
        scope,
    )

    # 将角色设定转为文本
    characters_text = build_characters_text(request.main_characters)

    # 将现有分卷大纲转为上下文文本
    existing_volume_outline = format_volume_outline_context(request.volume_outlines)

    # 创建结构化输出 LLM
    structured_llm = structured_llm_base.with_structured_output(VolumeOutlineOutput)

    # 构建链
    chain = load_prompt_template(
        "revise_volume_outline",
        genre=request.genre,
        story_style=request.story_style,
    ) | structured_llm
    log_progress(trace_id, "structured volume revision chain created, invoking Tongyi model in non-streaming mode", started_at, scope)

    # 调用大模型
    result = invoke_structured_output_with_guard(
        chain,
        {
            "Title": request.title,
            "Theme": request.genre or "未指定",
            "StoryStyle": request.story_style or "高质量国漫/漫剧视觉",
            "StorySummary": request.story_summary or "",
            "Outline": request.outline,
            "Characters": characters_text,
            "ExistingVolumeOutline": existing_volume_outline,   # 现有分卷大纲
            "ModificationRequest": request.suggestion,          # 用户修改意见
        },
        VolumeOutlineOutput,
        config={"callbacks": [ConsoleStreamingCallback(trace_id, scope)]},
        trace_id=trace_id,
        started_at=started_at,
        scope=scope,
    )

    # 校验结果
    if not result.volumes:
        raise HTTPException(status_code=502, detail="Tongyi model returned no revised volume outlines")

    # 构建响应
    log_progress(trace_id, f"model returned {len(result.volumes)} revised volume outlines", started_at, scope)
    response = StoryVolumeOutlineGenerateResponse(volumes=result.volumes)
    log_progress(trace_id, "revision response ready", started_at, scope)
    return response


@router.post("/api/story/volume-story", response_model=StoryVolumeStoryGenerateResponse)
def generate_volume_story(request: StoryVolumeStoryGenerateRequest) -> StoryVolumeStoryGenerateResponse:
    """根据指定分卷大纲生成该卷详细完整故事正文。

    使用纯文本输出（不使用 structured output），避免长篇正文的 JSON 转义问题。

    Args:
        request: 分卷正文生成请求体。

    Returns:
        StoryVolumeStoryGenerateResponse: 包含分卷故事正文。
    """
    # 生成追踪 ID
    trace_id = uuid.uuid4().hex[:8]
    started_at = time.perf_counter()
    scope = "volume-story"

    # 校验必填参数
    if not request.outline or not request.outline.strip():
        raise HTTPException(status_code=400, detail="Story outline is required before generating volume story")
    if not request.volume_outline.content or not request.volume_outline.content.strip():
        raise HTTPException(status_code=400, detail="Volume outline content is required before generating volume story")

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

    # 构建链：提示词模板 → LLM（纯文本输出）
    chain = load_prompt_template(
        "generate_volume_story",
        genre=request.genre,
        story_style=request.story_style,
    ) | structured_llm_base
    log_progress(trace_id, "plain text volume story chain created, invoking Tongyi model", started_at, scope)

    # 调用大模型
    raw_result = invoke_llm_with_retry(
        chain,
        {
            "Title": request.title,
            "Theme": request.genre or "未指定",
            "StoryStyle": request.story_style or "高质量国漫/漫剧视觉",
            "StorySummary": request.story_summary or "",
            "Outline": request.outline,
            "Characters": build_characters_text(request.main_characters),
            "VolumeNumber": request.volume_outline.volume_number,
            "VolumeTitle": request.volume_outline.title,
            "VolumeSummary": request.volume_outline.summary or "",
            "VolumeContent": request.volume_outline.content,
            "EndingHook": request.volume_outline.ending_hook or "",
        },
        config={"callbacks": [ConsoleStreamingCallback(trace_id, scope)]},
        trace_id=trace_id,
        started_at=started_at,
        scope=scope,
    )

    # 从响应中提取纯文本
    volume_story = extract_llm_text(raw_result)
    if not volume_story:
        raise HTTPException(status_code=502, detail="Tongyi model returned empty volume story")

    # 构建响应
    log_progress(trace_id, "model returned volume story text, preparing response", started_at, scope)
    response = StoryVolumeStoryGenerateResponse(volumeStory=volume_story)
    log_progress(trace_id, "volume story response ready", started_at, scope)
    return response
