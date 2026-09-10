# 剧情大纲业务模块
# 本文件负责剧情大纲的生成和修改，包含两个 FastAPI 端点：
# - POST /api/story/outline：生成剧情大纲
# - POST /api/story/outline/revise：修改剧情大纲
# 这些端点同时被 RabbitMQ Worker 和 HTTP 调试使用。

# time：用于计算请求耗时
import time

# uuid：用于生成请求追踪 ID
import uuid

# 从 ai_runtime 导入共享的 LLM 实例和工具函数
from ai_runtime import ConsoleStreamingCallback, invoke_structured_output_with_guard, log_progress, structured_llm_base

# 从 models 导入请求/响应/输出模型
from .models import (
    NovelOutlineOutput,                # 大模型剧情大纲输出约束
    OutlineRevisionOutput,             # 大模型大纲修改输出约束
    StoryOutlineGenerateRequest,       # 剧情大纲生成请求
    StoryOutlineGenerateResponse,      # 剧情大纲生成响应
    StoryOutlineReviseRequest,         # 剧情大纲修改请求
    StoryOutlineReviseResponse,        # 剧情大纲修改响应
)

# 从 router 导入路由器，用于注册端点
from .router import router

# 从 templates 导入提示词模板加载函数
from .templates import load_prompt_template


def _build_story_outline_payload(request: StoryOutlineGenerateRequest, *, strict_output: bool = False) -> dict[str, str]:
    """Build prompt variables for story outline generation.

    This function is called by generate_story_outline before every LLM invocation.
    strict_output=True adds a stronger instruction to reduce cases where the model echoes input
    fields instead of the target schema.
    """
    plot = request.plot or "User did not provide a rough plot. Please create a story from the theme."
    if strict_output:
        plot = (
            f"{plot}\n\n"
            "重要输出要求：你必须生成全新的漫剧剧情大纲，不要复述输入参数。"
            "最终结构化输出必须完整填写 novel_name、story_summary、outline、main_characters，"
            "main_characters 至少包含 3 个主要角色。"
        )

    return {
        "Theme": request.genre,
        "StoryStyle": request.story_style or "未指定，按题材自然推导",
        "Plot": plot,
    }


@router.post("/api/story/outline", response_model=StoryOutlineGenerateResponse)
def generate_story_outline(request: StoryOutlineGenerateRequest) -> StoryOutlineGenerateResponse:
    """根据题材和可选剧情生成结构化剧情大纲、故事摘要和主要角色设定。

    处理流程：
    1. 生成追踪 ID，记录请求开始
    2. 创建结构化输出链：promptTemplate_Outline → structured_llm → NovelOutlineOutput
    3. 调用大模型，传入题材、风格和剧情
    4. 将结构化输出映射为响应模型

    Args:
        request: 剧情大纲生成请求体，包含用户 ID、题材、风格和可选剧情。

    Returns:
        StoryOutlineGenerateResponse: 包含小说名、摘要、大纲和角色设定。
    """
    # 生成 8 位十六进制追踪 ID
    trace_id = uuid.uuid4().hex[:8]

    # 记录请求开始时间
    started_at = time.perf_counter()

    # 打印请求接收日志
    log_progress(trace_id, f"request accepted, user_id={request.user_id}, genre={request.genre}", started_at)

    # 创建结构化输出 LLM：绑定 NovelOutlineOutput 模型，约束大模型输出格式
    structured_llm = structured_llm_base.with_structured_output(NovelOutlineOutput)

    # 构建 LangChain 链：提示词模板 → 结构化 LLM
    chain = load_prompt_template(
        "generate_story_outline",
        genre=request.genre,
        story_style=request.story_style,
    ) | structured_llm

    # 打印链创建完成日志
    log_progress(trace_id, "structured chain created, invoking Tongyi model in non-streaming mode", started_at)

    # 调用大模型，传入提示词变量。结构化输出必须经过 JSON 修复/验证保护；
    # 最多重新生成 3 次，仍失败则让任务真实失败，避免落库伪造大纲。
    result = invoke_structured_output_with_guard(
        chain,
        _build_story_outline_payload(request, strict_output=True),
        NovelOutlineOutput,
        # 传入控制台回调，打印调用进度
        config={"callbacks": [ConsoleStreamingCallback(trace_id)]},
        trace_id=trace_id,
        started_at=started_at,
        scope="story-outline",
    )

    # 打印模型返回日志
    log_progress(trace_id, "model returned structured output, preparing HTTP response", started_at)

    # 将结构化输出映射为响应模型（snake_case → camelCase）
    response = StoryOutlineGenerateResponse(
        novelName=result.novel_name,              # 小说名称
        storySummary=result.story_summary,        # 故事摘要
        outline=result.outline,                   # 完整大纲
        mainCharacters=result.main_characters,    # 主要角色设定
    )

    # 打印响应就绪日志
    log_progress(trace_id, "response ready", started_at)
    return response


@router.post("/api/story/outline/revise", response_model=StoryOutlineReviseResponse)
def revise_story_outline(request: StoryOutlineReviseRequest) -> StoryOutlineReviseResponse:
    """根据用户修改意见调用大模型修改剧情大纲，并返回结构化结果。

    处理流程：
    1. 生成追踪 ID，记录请求开始
    2. 将原始故事信息组装为文本
    3. 创建结构化输出链：promptTemplate_ReviseOutline → structured_llm → OutlineRevisionOutput
    4. 调用大模型，传入原始大纲和修改意见
    5. 返回修改后的结构化结果

    Args:
        request: 剧情大纲修改请求体，包含故事信息和修改意见。

    Returns:
        StoryOutlineReviseResponse: 包含修改后的摘要、大纲和角色设定。
    """
    # 生成追踪 ID
    trace_id = uuid.uuid4().hex[:8]

    # 记录请求开始时间
    started_at = time.perf_counter()

    # 业务范围标识
    scope = "story-outline-revise"

    # 打印请求接收日志
    log_progress(
        trace_id,
        f"revision request accepted, user_id={request.user_id}, story_id={request.story_id}, title={request.title}",
        started_at,
        scope,
    )

    # 将原始故事信息组装为文本，作为大模型的上下文
    original_outline = (
        f"书名：{request.title}\n"
        f"故事摘要：{request.synopsis or ''}\n\n"
        f"剧情大纲：\n{request.outline}"
    )

    # 创建结构化输出 LLM：绑定 OutlineRevisionOutput 模型
    structured_llm = structured_llm_base.with_structured_output(OutlineRevisionOutput)

    # 构建 LangChain 链
    chain = load_prompt_template(
        "revise_story_outline",
        genre=request.genre,
        story_style=request.story_style,
    ) | structured_llm

    # 打印链创建日志
    log_progress(trace_id, "structured revision chain created, invoking Tongyi model in non-streaming mode", started_at, scope)

    # 调用大模型
    result = invoke_structured_output_with_guard(
        chain,
        {
            "Theme": request.genre or "未指定",
            "StoryStyle": request.story_style or "未指定，按题材自然推导",
            "OriginalOutline": original_outline,   # 原始大纲文本
            "RevisionNotes": request.suggestion,   # 用户修改意见
        },
        OutlineRevisionOutput,
        config={"callbacks": [ConsoleStreamingCallback(trace_id, scope)]},
        trace_id=trace_id,
        started_at=started_at,
        scope=scope,
    )

    # 打印模型返回日志
    log_progress(trace_id, "model returned revised outline, preparing HTTP response", started_at, scope)

    # 构建响应
    response = StoryOutlineReviseResponse(
        storySummary=result.story_summary,        # 修改后的摘要
        outline=result.outline,                   # 修改后的大纲
        mainCharacters=result.main_characters,    # 更新后的角色设定
    )

    # 打印响应就绪日志
    log_progress(trace_id, "revision response ready", started_at, scope)
    return response
