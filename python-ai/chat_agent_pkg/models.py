# 智能对话 Agent 数据模型定义模块
# 本文件定义对话系统中所有 Pydantic 数据模型，包括请求、响应和中间处理模型。

# typing.Any：用于声明动态类型字典的值类型
from typing import Any

# Pydantic：数据验证和序列化库
from pydantic import BaseModel, ConfigDict, Field


class ChatMemoryMessage(BaseModel):
    """对话记忆消息模型。

    描述一条对话消息，用于短期记忆（Redis）和长期记忆（摘要）的传递。
    Java 端通过 recentMessages 和 summaryCandidateMessages 字段传入。
    """

    # 允许使用别名（camelCase）填充字段
    model_config = ConfigDict(populate_by_name=True)

    # 消息角色：user（用户）或 ai（助手）
    role: str

    # 消息内容
    content: str

    # 消息创建时间，可选
    created_at: str | None = Field(default=None, alias="createdAt")


class ChatAgentRequest(BaseModel):
    """对话 Agent 请求体。

    对应 Java 端 AiEngineClient.runChatAgent 的入参。
    包含用户信息、故事上下文、对话记忆和当前用户消息。
    """

    # 允许使用别名填充
    model_config = ConfigDict(populate_by_name=True)

    # 用户 ID
    user_id: int = Field(alias="userId")

    # 会话 ID
    session_id: int = Field(alias="sessionId")

    # 绑定的故事 ID，可选（无绑定漫剧时为空）
    story_id: int | None = Field(default=None, alias="storyId")

    # 故事标题，可选
    title: str | None = None

    # 故事题材，可选（如科幻、玄幻、都市）
    genre: str | None = None

    # 漫剧视觉风格，可选
    story_style: str | None = Field(default=None, alias="storyStyle")

    # 故事摘要，可选
    synopsis: str | None = None

    # 故事大纲，可选
    outline: str | None = None

    # 用户当前发送的消息
    user_message: str = Field(alias="userMessage")

    # 用户角色：USER、ADMIN、ROOT
    user_role: str = Field(default="USER", alias="userRole")

    # 近期对话消息列表（短期记忆，来自 Redis）
    recent_messages: list[ChatMemoryMessage] = Field(default_factory=list, alias="recentMessages")

    # 长期记忆文本（经过摘要压缩的历史上下文）
    long_term_memory: str | None = Field(default=None, alias="longTermMemory")

    # 关键事实信息（结构化 JSON，如 storyId、genre、style 等）
    key_facts: dict[str, Any] = Field(default_factory=dict, alias="keyFacts")

    # 需要摘要压缩的候选消息列表（即将从短期记忆移出的旧消息）
    summary_candidate_messages: list[ChatMemoryMessage] = Field(
        default_factory=list,
        alias="summaryCandidateMessages",
    )

    # 候选消息数量
    summary_candidate_count: int = Field(default=0, alias="summaryCandidateCount")


class CoreferenceOutput(BaseModel):
    """指代消解结构化输出模型。

    大模型将用户输入中的指代词替换为具体实体后的结果。
    例如："帮我修改它" → "帮我修改《星际迷航》的剧情大纲"
    """

    # 消解后的独立、明确的用户消息
    resolved_message: str = Field(alias="resolvedMessage")

    # 消解说明，记录做了哪些替换
    resolution_notes: str = Field(default="", alias="resolutionNotes")


class RouteOutput(BaseModel):
    """意图路由结构化输出模型。

    大模型判断用户意图后，路由到对应模块并提取关键信息。
    """

    # 目标模块：manga（漫剧）、outline_config（大纲配置）、prompt_management（Prompt管理）、user_permission（用户权限）、feature_permission（功能权限）、general（闲聊）
    module: str = Field(description="manga, outline_config, prompt_management, user_permission, feature_permission, or general")

    # 用户意图，如 story_generate、prompt_update、user_role_update
    intent: str

    # 路由标签，如 update_outline、no_action
    route: str

    # 执行此操作所需的最低权限：USER、ADMIN、ROOT
    required_permission: str = Field(default="USER", alias="requiredPermission")

    # 从用户输入中提取的关键信息，如 storyId、genre、style 等
    important_info: dict[str, Any] = Field(default_factory=dict, alias="importantInfo")

    # 缺失的必要信息列表，用于提示用户补充
    missing_info: list[str] = Field(default_factory=list, alias="missingInfo")

    # 助手回复消息
    assistant_message: str = Field(default="", alias="assistantMessage")


class MemoryUpdateOutput(BaseModel):
    """记忆更新结构化输出模型。

    大模型压缩短期记忆后输出的长期记忆和关键事实。
    """

    # 更新后的长期记忆文本
    long_term_memory: str = Field(default="", alias="longTermMemory")

    # 更新后的关键事实 JSON 对象
    key_facts: dict[str, Any] = Field(default_factory=dict, alias="keyFacts")


class SubAgentAction(BaseModel):
    """子 Agent 执行结果模型。

    ReAct Agent 选择工具执行后返回的结果，包含要调用的 Java 方法和参数。
    """

    # 要调用的 Java 方法名，如 story.generate、story.none
    java_method: str = Field(default="story.none", alias="javaMethod")

    # Java 方法的参数
    java_method_args: dict[str, Any] = Field(default_factory=dict, alias="javaMethodArgs")

    # 助手回复消息
    assistant_message: str = Field(default="", alias="assistantMessage")

    # 缺失信息列表
    missing_info: list[str] = Field(default_factory=list, alias="missingInfo")


class ChatAgentResponse(BaseModel):
    """对话 Agent 最终响应体。

    返回给 Java 端的完整结果，包含消解后的消息、路由信息、记忆更新和要执行的操作。
    """

    # 允许使用别名填充
    model_config = ConfigDict(populate_by_name=True)

    # 重写后的用户问题（兼容旧接口）
    rewritten_question: str = Field(alias="rewrittenQuestion")

    # 指代消解后的用户问题
    resolved_question: str = Field(alias="resolvedQuestion")

    # 路由标签
    route: str

    # 目标模块
    module: str

    # 用户意图
    intent: str

    # 所需权限
    required_permission: str = Field(alias="requiredPermission")

    # 提取的关键信息
    important_info: dict[str, Any] = Field(default_factory=dict, alias="importantInfo")

    # 缺失信息
    missing_info: list[str] = Field(default_factory=list, alias="missingInfo")

    # 要调用的 Java 方法名
    java_method: str = Field(alias="javaMethod")

    # Java 方法参数
    java_method_args: dict[str, Any] = Field(default_factory=dict, alias="javaMethodArgs")

    # 助手回复
    assistant_message: str = Field(alias="assistantMessage")

    # 更新后的长期记忆
    long_term_memory: str | None = Field(default=None, alias="longTermMemory")

    # 更新后的关键事实
    key_facts: dict[str, Any] = Field(default_factory=dict, alias="keyFacts")

    # 本次摘要压缩的消息数量
    summarized_message_count: int | None = Field(default=None, alias="summarizedMessageCount")
