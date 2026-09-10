# 记忆管理模块
# 本文件负责对话记忆的更新和压缩，包括：
# 1. 短期记忆压缩：将即将从 Redis 移出的旧消息摘要压缩为长期记忆
# 2. 关键事实合并：将路由提取的重要信息合并到 keyFacts 中

# json：用于序列化 keyFacts 字典
import json

# 从 ai_runtime 导入 LLM 实例和重试调用函数
from ai_runtime import Router, invoke_structured_output_with_guard

# 从 prompt_repository 导入提示词模板加载函数
from story_ai_pkg.prompt_repository import get_prompt_template

# 从 models 导入数据模型
from .models import ChatAgentRequest, MemoryUpdateOutput, RouteOutput

# 从 prompts 导入记忆压缩提示词
from .prompts import prompt_ChatMemorySummary

# 从 routing 导入消息格式化函数
from .routing import format_messages


def update_memory(
        request: ChatAgentRequest,
        route: RouteOutput,
        resolved_message: str,
        trace_id: str,
        started_at: float,
) -> MemoryUpdateOutput:
    """更新对话记忆。

    两种模式：
    1. 有候选消息时：调用大模型将旧短期记忆压缩为长期记忆，并更新 keyFacts
    2. 无候选消息时：直接合并路由提取的 importantInfo 到 keyFacts

    Args:
        request:          对话 Agent 请求体，包含记忆上下文。
        route:            路由输出，包含提取的关键信息。
        resolved_message: 指代消解后的用户消息。
        trace_id:         追踪 ID。
        started_at:       请求开始时间。

    Returns:
        MemoryUpdateOutput: 更新后的长期记忆和关键事实。
    """
    # 如果有需要摘要压缩的候选消息
    if request.summary_candidate_messages:
        # 构建记忆压缩链：提示词模板 → 结构化 LLM
        chain = get_prompt_template(
            "chat_memory_summary",           # 提示词 key
            prompt_ChatMemorySummary,        # 兜底提示词
            genre=request.genre,             # 按题材匹配特定提示词
            story_style=request.story_style, # 按风格匹配特定提示词
        ) | Router.with_structured_output(MemoryUpdateOutput)

        # 调用大模型进行记忆压缩
        return invoke_structured_output_with_guard(
            chain,
            {
                "ExistingLongTermMemory": request.long_term_memory or "无",       # 已有长期记忆
                "ExistingKeyFacts": json.dumps(request.key_facts or {}, ensure_ascii=False),  # 已有关键事实
                "SummaryCandidateMessages": format_messages(request.summary_candidate_messages),  # 待压缩消息
                "CurrentMessage": resolved_message,                               # 当前用户消息
                "ImportantInfo": json.dumps(route.important_info or {}, ensure_ascii=False),  # 本轮提取的关键信息
            },
            MemoryUpdateOutput,
            trace_id=trace_id,
            started_at=started_at,
            scope="chat-memory",  # 日志前缀
        )

    # 无候选消息时，直接合并关键信息
    return MemoryUpdateOutput(
        longTermMemory=request.long_term_memory or "",  # 保留原有长期记忆
        keyFacts=merge_key_facts(request.key_facts, route.important_info),  # 合并关键事实
    )


def merge_key_facts(existing_facts: dict | None, important_info: dict | None) -> dict:
    """将新提取的关键信息合并到已有的关键事实中。

    合并规则：
    - 保留已有的所有事实
    - 新信息覆盖同名旧信息
    - 跳过 None 值和空字符串

    Args:
        existing_facts:  已有的关键事实字典。
        important_info:  本轮新提取的关键信息。

    Returns:
        dict: 合并后的关键事实字典。
    """
    # 复制已有事实，避免修改原字典
    facts = dict(existing_facts or {})

    # 遍历新信息，合并到事实中
    for key, value in (important_info or {}).items():
        # 跳过 None 值
        if value is None:
            continue
        # 跳过空字符串
        if isinstance(value, str) and not value.strip():
            continue
        # 覆盖写入
        facts[key] = value

    return facts
