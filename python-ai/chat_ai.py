# 对话 Agent 入口模块
# 本文件是智能对话系统的 FastAPI 入口，提供 /api/chat/agent 接口。
# 整体流程：指代消解 → 意图路由 → 记忆更新 → 子 Agent 执行 → 返回结果

# time：用于计算请求耗时
import time

# uuid：用于生成请求追踪 ID
import uuid

# FastAPI 工具导入
from fastapi import APIRouter

# 从 ai_runtime 导入日志函数
from ai_runtime import log_progress

# 从 chat_agent_pkg 导入各阶段处理函数和模型
from chat_agent_pkg.memory import update_memory             # 记忆更新
from chat_agent_pkg.models import ChatAgentRequest, ChatAgentResponse  # 请求/响应模型
from chat_agent_pkg.permissions import module_required_role  # 权限校验
from chat_agent_pkg.routing import fallback_general_response, resolve_coreference, route_message  # 路由
from chat_agent_pkg.sub_agents import run_sub_agent         # 子 Agent 执行


# 创建对话 Agent 路由器，最终在 main.py 中挂载到 app
router = APIRouter()


@router.post("/api/chat/agent", response_model=ChatAgentResponse)
def run_chat_agent(request: ChatAgentRequest) -> ChatAgentResponse:
    """执行智能对话 Agent 流水线。

    完整处理流程：
    1. 指代消解：将"它"、"这个"等指代词替换为具体实体
    2. 意图路由：判断用户意图，提取关键信息，路由到对应模块
    3. 记忆更新：压缩短期记忆为长期记忆，合并关键事实
    4. 子 Agent 执行：根据模块调用 ReAct Agent，选择工具执行
    5. 返回结果：将 Java 方法名和参数返回给 Java 后端

    Args:
        request: 对话 Agent 请求体，包含用户消息和对话记忆。

    Returns:
        ChatAgentResponse: 包含消解后消息、路由信息、记忆更新和要执行的操作。
    """
    # 生成 8 位十六进制追踪 ID
    trace_id = uuid.uuid4().hex[:8]

    # 记录请求开始时间
    started_at = time.perf_counter()

    # 业务范围标识
    scope = "chat-agent"

    # 打印请求接收日志
    log_progress(
        trace_id,
        f"request accepted, user_id={request.user_id}, session_id={request.session_id}, role={request.user_role}",
        started_at,
        scope,
    )

    try:
        # ── 第 1 步：指代消解 ──────────────────────────────────────────
        # 将用户输入中的指代词替换为具体实体
        coreference = resolve_coreference(request, trace_id, started_at)
        resolved_message = coreference.resolved_message
        log_progress(trace_id, f"resolved message: {resolved_message[:120]}", started_at, scope)

        # ── 第 2 步：意图路由 ──────────────────────────────────────────
        # 判断用户意图，提取关键信息，路由到对应模块
        route = route_message(request, resolved_message, trace_id, started_at)

        # 如果路由模块为空，使用通用回复兜底
        if not route.module:
            route = fallback_general_response(request, resolved_message)

        # 如果路由未指定权限，根据模块自动填充
        if not route.required_permission:
            route.required_permission = module_required_role(route.module)

        log_progress(
            trace_id,
            f"route module={route.module}, intent={route.intent}, required={route.required_permission}",
            started_at,
            scope,
        )

        # ── 第 3 步：记忆更新 ──────────────────────────────────────────
        # 压缩短期记忆为长期记忆，合并关键事实
        memory = update_memory(request, route, resolved_message, trace_id, started_at)

        # ── 第 4 步：子 Agent 执行 ──────────────────────────────────────
        # 根据模块调用 ReAct Agent，选择工具执行
        action = run_sub_agent(request, route, resolved_message, trace_id, started_at)

        # 计算摘要压缩的消息数量
        summarized_count = request.summary_candidate_count if request.summary_candidate_messages else None

        log_progress(
            trace_id,
            f"sub-agent selected method={action.java_method}, missing={action.missing_info}",
            started_at,
            scope,
        )

        # ── 第 5 步：构建并返回响应 ────────────────────────────────────
        return ChatAgentResponse(
            rewrittenQuestion=resolved_message,                          # 重写后的消息（兼容旧接口）
            resolvedQuestion=resolved_message,                           # 消解后的消息
            route=route.route,                                           # 路由标签
            module=route.module,                                         # 目标模块
            intent=route.intent,                                         # 用户意图
            requiredPermission=route.required_permission,                # 所需权限
            importantInfo=route.important_info,                          # 提取的关键信息
            missingInfo=action.missing_info or route.missing_info,       # 缺失信息
            javaMethod=action.java_method,                               # Java 方法名
            javaMethodArgs=action.java_method_args,                      # Java 方法参数
            assistantMessage=action.assistant_message or route.assistant_message or "我已经理解你的需求。",  # 助手回复
            longTermMemory=memory.long_term_memory,                      # 更新后的长期记忆
            keyFacts=memory.key_facts,                                   # 更新后的关键事实
            summarizedMessageCount=summarized_count,                     # 摘要压缩的消息数量
        )

    except Exception as exc:
        # ── 异常兜底 ──────────────────────────────────────────────────
        # 如果任何步骤失败，返回友好的错误回复
        log_progress(trace_id, f"chat agent failed: {exc}", started_at, scope)
        return ChatAgentResponse(
            rewrittenQuestion=request.user_message,                      # 使用原始消息
            resolvedQuestion=request.user_message,
            route="fallback",                                            # 兜底路由
            module="general",                                            # 通用模块
            intent="fallback_response",                                  # 兜底意图
            requiredPermission="USER",                                   # 普通用户权限
            importantInfo={},                                            # 无关键信息
            missingInfo=[],                                              # 无缺失信息
            javaMethod="story.none",                                     # 不执行操作
            javaMethodArgs={},                                           # 无参数
            assistantMessage="智能对话模块暂时没有处理成功，我先保留你的输入，请稍后再试或换一种更明确的说法。",
            longTermMemory=request.long_term_memory or "",               # 保留原有记忆
            keyFacts=request.key_facts or {},                            # 保留原有关键事实
            summarizedMessageCount=None,                                 # 无摘要压缩
        )
