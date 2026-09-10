# 分镜脚本业务模块
# 本文件负责根据小节故事内容生成镜头级分镜脚本。
# 包含一个 FastAPI 端点：
# - POST /api/story/section-script：生成分镜脚本

# time：用于计算请求耗时
import time

# uuid：用于生成请求追踪 ID
import uuid

# HTTPException：FastAPI HTTP 异常
from fastapi import HTTPException

# 从 ai_runtime 导入共享的 LLM 实例和工具函数
from ai_runtime import ConsoleStreamingCallback, invoke_structured_output_with_guard, log_progress, structured_llm_base

# 从 formatters 导入角色设定格式化函数
from .formatters import build_characters_text

# 从 models 导入数据模型
from .models import StorySectionScriptGenerateRequest, StorySectionScriptGenerateResponse

# 从 router 导入路由器
from .router import router

# 从 templates 导入提示词模板加载函数
from .templates import load_prompt_template


@router.post("/api/story/section-script", response_model=StorySectionScriptGenerateResponse)
def generate_section_script(request: StorySectionScriptGenerateRequest) -> StorySectionScriptGenerateResponse:
    """根据单个小节故事生成分镜故事脚本。

    处理流程：
    1. 校验小节内容是否存在
    2. 创建结构化输出链：promptTemplate_SectionScriptGenerate → structured_llm → StorySectionScriptGenerateResponse
    3. 调用大模型，传入故事上下文和小节内容
    4. 校验并补全结果（设置小节号、计算总时长）

    Args:
        request: 分镜脚本生成请求体，包含故事上下文和小节内容。

    Returns:
        StorySectionScriptGenerateResponse: 包含分镜列表、小节号和总时长。
    """
    # 生成追踪 ID
    trace_id = uuid.uuid4().hex[:8]
    started_at = time.perf_counter()
    scope = "section-script"

    # 校验小节内容
    if not request.section.content or not request.section.content.strip():
        raise HTTPException(status_code=400, detail="Section content is required before generating section script")

    # 打印请求接收日志
    log_progress(
        trace_id,
        (
            f"request accepted, user_id={request.user_id}, story_id={request.story_id}, "
            f"volume_id={request.volume_id}, section={request.section.section_number}"
        ),
        started_at,
        scope,
    )

    # 创建结构化输出 LLM：绑定 StorySectionScriptGenerateResponse 模型
    # 大模型会返回包含 shots 列表的结构化 JSON
    structured_llm = structured_llm_base.with_structured_output(StorySectionScriptGenerateResponse)

    # 构建链
    chain = load_prompt_template(
        "generate_section_script",
        genre=request.genre,
        story_style=request.story_style,
    ) | structured_llm
    log_progress(trace_id, "structured section script chain created, invoking Tongyi model", started_at, scope)

    # 调用大模型
    result = invoke_structured_output_with_guard(
        chain,
        {
            "Title": request.title,
            "Theme": request.genre or "未指定",
            "StoryStyle": request.story_style or "高质量国漫/漫剧视觉",
            "StorySummary": request.story_summary or "",
            "Outline": request.outline or "",
            "Characters": build_characters_text(request.main_characters),
            "VolumeNumber": request.volume_outline.volume_number,
            "VolumeTitle": request.volume_outline.title,
            "VolumeSummary": request.volume_outline.summary or "",
            "VolumeContent": request.volume_outline.content or "",
            "EndingHook": request.volume_outline.ending_hook or "",
            "SectionNumber": request.section.section_number,
            "SectionTitle": request.section.title,
            "SectionSummary": request.section.summary or "",
            "SectionContent": request.section.content,
            "SectionEndingHook": request.section.ending_hook or "",
        },
        StorySectionScriptGenerateResponse,
        config={"callbacks": [ConsoleStreamingCallback(trace_id, scope)]},
        trace_id=trace_id,
        started_at=started_at,
        scope=scope,
    )

    # 校验是否有分镜结果
    if not result.shots:
        raise HTTPException(status_code=502, detail="Tongyi model returned no section script shots")

    # 设置小节号（大模型可能返回错误的值）
    result.section_number = request.section.section_number

    # 如果大模型没有返回总时长，自动计算所有镜头时长之和
    if not result.total_duration_seconds:
        result.total_duration_seconds = sum(max(shot.duration_seconds or 0, 0) for shot in result.shots)

    # 打印完成日志
    log_progress(trace_id, f"section script generated: {len(result.shots)} shots", started_at, scope)
    return result
