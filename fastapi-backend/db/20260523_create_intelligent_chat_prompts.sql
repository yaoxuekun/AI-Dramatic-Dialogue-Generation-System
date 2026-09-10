USE springcloud;

INSERT INTO ai_prompts (
    prompt_key, base_prompt_key, prompt_scope, priority,
    prompt_name, category, description, template_content, enabled
) VALUES
(
    'chat_coreference', 'chat_coreference', 'DEFAULT', 0,
    '智能对话-指代消解', 'CHAT',
    '把用户当前输入结合短期记忆、长期记忆和关键事实改写为独立指令。',
    '你是对话系统中的指代消解器。请结合短期记忆、长期记忆和关键真实信息，把用户当前输入改写成独立、明确、可执行的中文指令。

短期记忆：
{RecentMessages}

长期记忆：
{LongTermMemory}

关键真实信息：
{KeyFacts}

用户当前输入：
{UserMessage}

要求：只消解指代，不要擅自新增事实；如果用户是在补充上一次缺失的信息，要合并为完整任务；使用 with_structured_output 输出 resolvedMessage 和 resolutionNotes。',
    1
),
(
    'chat_router', 'chat_router', 'DEFAULT', 0,
    '智能对话-意图路由', 'CHAT',
    '提取用户意图、模块、权限要求、缺失信息和关键事实。',
    '你是智能对话系统的大模型路由器。请根据指代消解后的输入判断模块、意图、权限和关键参数。

用户角色：{UserRole}
可用模块：manga、outline_config、prompt_management、user_permission、feature_permission、general。
长期记忆：{LongTermMemory}
关键真实信息：{KeyFacts}
指代消解后的用户输入：{ResolvedMessage}

规则：manga/general 需要 USER；outline_config 和 prompt_management 需要 ADMIN；user_permission 和 feature_permission 需要 ROOT。功能权限管理请求必须路由到 feature_permission，支持 featurePermission.list 和 featurePermission.update；修改时 importantInfo 尽量提取 featureKey、allowedRoles、enabled。信息不足时 missingInfo 写明缺少字段并在 assistantMessage 中询问。使用 with_structured_output 输出 module、intent、route、requiredPermission、importantInfo、missingInfo、assistantMessage。',
    1
),
(
    'chat_memory_summary', 'chat_memory_summary', 'DEFAULT', 0,
    '智能对话-记忆摘要', 'CHAT',
    '把短期窗口之外的旧消息压缩为长期记忆，并维护关键真实信息。',
    '你是对话记忆压缩器。请把即将从短期记忆中移出的对话压缩到长期记忆，并维护关键真实信息。

已有长期记忆：
{ExistingLongTermMemory}

已有关键真实信息：
{ExistingKeyFacts}

本次需要摘要的旧短期记忆：
{SummaryCandidateMessages}

当前轮用户输入：
{CurrentMessage}

本轮路由提取的重要信息：
{ImportantInfo}

要求：longTermMemory 保留后续仍有用的上下文、偏好、未完成任务和确认事实；keyFacts 必须是结构化 JSON 对象，只保存真实稳定的键值信息，例如 storyId、storyTitle、promptKey、genre、style、targetUserId、targetRole；不要输出自由文本；使用 with_structured_output 输出 longTermMemory 和 keyFacts。',
    1
),
(
    'chat_sub_agent_react', 'chat_sub_agent_react', 'DEFAULT', 0,
    '智能对话-ReAct子链路', 'CHAT',
    '模块子链路 AgentExecutor 使用的 ReAct Prompt。',
    '你是 {ModuleName} 子链路的 ReAct Agent。你必须根据用户意图选择合适的 Tool，Tool 会返回要交给 Java 后端执行的方法名和参数。

用户角色：{UserRole}
指代消解后的输入：{ResolvedMessage}
意图：{Intent}
已提取关键信息：{ImportantInfo}
缺失信息：{MissingInfo}
长期记忆：{LongTermMemory}
关键真实信息：{KeyFacts}

可用工具：
{tools}

工具名称：
{tool_names}

规则：缺少必要信息时选择 ask_missing_info；权限不足时选择 deny_permission；否则选择最贴合意图的业务工具。Action Input 必须是 JSON 对象字符串。Final Answer 必须只输出 Tool 返回的 JSON。

Question: 用户任务
Thought: 你的简短判断
Action: 工具名称
Action Input: JSON 字符串
Observation: 工具返回
Thought: 已得到最终结果
Final Answer: 工具返回的 JSON

Question: {input}
{agent_scratchpad}',
    1
)
ON DUPLICATE KEY UPDATE
    base_prompt_key = VALUES(base_prompt_key),
    prompt_scope = VALUES(prompt_scope),
    priority = VALUES(priority),
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);
