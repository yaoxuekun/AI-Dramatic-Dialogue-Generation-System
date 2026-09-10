# ReAct 子 Agent 执行模块
# 本文件负责根据路由结果执行对应的子 Agent：
# 1. 权限校验：检查用户是否有权限执行该模块的操作
# 2. 通用模块处理：general 模块直接返回助手回复
# 3. ReAct Agent 执行：为业务模块创建 LangChain ReAct Agent，选择工具执行
# 4. 结果解析：从 Agent 输出中提取 Java 方法名和参数

# json：用于序列化关键信息
import json

# re：用于从 Agent 输出中提取 JSON 对象
import re

# LangChain Agent 相关导入
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

# 从 ai_runtime 导入 LLM 实例和重试调用函数
from ai_runtime import Router, invoke_llm_with_retry

# 从 prompt_repository 导入提示词加载函数
from story_ai_pkg.prompt_repository import get_prompt_template

# 从 models 导入数据模型
from .models import ChatAgentRequest, RouteOutput, SubAgentAction

# 从 permissions 导入权限校验函数
from .permissions import has_permission, module_required_role

# 从 prompts 导入子 Agent 提示词
from .prompts import prompt_SubAgentReact

# 从 tools 导入工具获取函数和 JSON 序列化函数
from .tools import get_tools_for_module, to_json


def run_sub_agent(
        request: ChatAgentRequest,
        route: RouteOutput,
        resolved_message: str,
        trace_id: str,
        started_at: float,
) -> SubAgentAction:
    """执行子 Agent，根据路由结果选择工具并返回执行结果。

    处理流程：
    1. 权限校验：如果用户权限不足，直接返回权限不足提示
    2. 通用模块：general 模块直接返回助手回复，不调用 Agent
    3. 业务模块：创建 ReAct Agent，选择工具执行，返回 Java 方法和参数

    Args:
        request:          对话 Agent 请求体。
        route:            路由输出，包含模块、意图和关键信息。
        resolved_message: 消解后的用户消息。
        trace_id:         追踪 ID。
        started_at:       请求开始时间。

    Returns:
        SubAgentAction: 子 Agent 执行结果，包含 Java 方法名和参数。
    """
    # ── 权限校验 ──────────────────────────────────────────────────────
    # 获取该模块所需的最低权限
    required_role = route.required_permission or module_required_role(route.module)

    # 检查用户是否有足够权限
    if not has_permission(request.user_role, required_role):
        return SubAgentAction(
            javaMethod="story.none",                     # 不执行操作
            javaMethodArgs={},                           # 无参数
            assistantMessage=f"当前账号是 {request.user_role}，这个操作需要 {required_role} 权限。",
            missingInfo=[],
        )

    # ── 通用模块处理 ──────────────────────────────────────────────────
    # general 模块不需要调用 Agent，直接返回助手回复
    if route.module == "general":
        return SubAgentAction(
            javaMethod="story.none",
            javaMethodArgs={},
            assistantMessage=route.assistant_message or "我理解了，我们可以继续聊这个创作方向。",
            missingInfo=[],
        )

    # ── ReAct Agent 执行 ──────────────────────────────────────────────
    # 获取该模块的工具列表
    tools = get_tools_for_module(route.module)

    # 获取子 Agent 提示词模板
    prompt = get_prompt_template(
        "chat_sub_agent_react",       # 提示词 key
        prompt_SubAgentReact,         # 兜底提示词
        genre=request.genre,          # 按题材匹配
        story_style=request.story_style,  # 按风格匹配
    )

    # 确保 prompt 是 PromptTemplate 类型
    if not isinstance(prompt, PromptTemplate):
        prompt = PromptTemplate.from_template(prompt_SubAgentReact)

    # 创建 ReAct Agent
    agent = create_react_agent(Router, tools, prompt)

    # 创建 Agent 执行器
    executor = AgentExecutor(
        agent=agent,                    # ReAct Agent
        tools=tools,                    # 可用工具列表
        verbose=True,                   # 打印详细执行过程
        handle_parsing_errors=True,     # 自动处理解析错误
        max_iterations=4,               # 最大迭代次数，避免无限循环
        return_intermediate_steps=False, # 不返回中间步骤
    )

    # 调用 Agent 执行器
    result = invoke_llm_with_retry(
        executor,
        {
            "input": resolved_message,                                        # 用户输入
            "ModuleName": route.module,                                       # 模块名
            "UserRole": request.user_role,                                    # 用户角色
            "ResolvedMessage": resolved_message,                              # 消解后消息
            "Intent": route.intent,                                           # 意图
            "ImportantInfo": to_json(route.important_info or {}),             # 关键信息
            "MissingInfo": to_json({"missingInfo": route.missing_info or []}),  # 缺失信息
            "LongTermMemory": request.long_term_memory or "无",               # 长期记忆
            "KeyFacts": json.dumps(request.key_facts or {}, ensure_ascii=False),  # 关键事实
        },
        trace_id=trace_id,
        started_at=started_at,
        scope=f"chat-sub-agent:{route.module}",  # 日志前缀，包含模块名
    )

    # 提取 Agent 输出
    output = result.get("output", "") if isinstance(result, dict) else str(result)

    # 解析输出为 SubAgentAction
    return parse_sub_agent_output(output, route)


def parse_sub_agent_output(output: str, route: RouteOutput) -> SubAgentAction:
    """解析子 Agent 的输出为 SubAgentAction。

    从 Agent 的 Final Answer 中提取 JSON 对象，
    包含 javaMethod、javaMethodArgs、assistantMessage 等字段。

    Args:
        output: Agent 的原始输出文本。
        route:  路由输出，用于兜底回复。

    Returns:
        SubAgentAction: 解析后的执行结果。
    """
    # 尝试从输出中提取 JSON 对象
    data = extract_json_object(output)

    # 如果提取失败，返回兜底结果
    if not data:
        return SubAgentAction(
            javaMethod="story.none",
            javaMethodArgs={},
            assistantMessage=route.assistant_message or "我理解了你的需求，但还没有形成可执行操作。请补充更明确的信息。",
            missingInfo=route.missing_info or [],
        )

    # 从 JSON 中提取字段，支持 camelCase 和 snake_case
    return SubAgentAction(
        javaMethod=data.get("javaMethod") or data.get("java_method") or "story.none",
        javaMethodArgs=data.get("javaMethodArgs") or data.get("java_method_args") or {},
        assistantMessage=data.get("assistantMessage") or route.assistant_message or "已完成处理。",
        missingInfo=data.get("missingInfo") or [],
    )


def extract_json_object(text: str) -> dict | None:
    """从文本中提取 JSON 对象。

    尝试两种方式：
    1. 直接解析整个文本为 JSON
    2. 使用正则表达式提取第一个 {...} 块

    Args:
        text: 原始文本。

    Returns:
        dict | None: 提取到的 JSON 字典，失败返回 None。
    """
    if not text:
        return None

    stripped = text.strip()

    # 方式 1：直接解析
    try:
        parsed = json.loads(stripped)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    # 方式 2：正则提取 {...}
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None
