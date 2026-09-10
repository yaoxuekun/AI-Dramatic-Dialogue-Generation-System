# 智能对话 Agent 包
# 本包实现了一个多阶段智能对话系统，用于理解用户意图并路由到对应的业务操作。
#
# 整体流程：
# 1. 指代消解（routing.resolve_coreference）：将用户输入中的"它"、"那个"等指代词替换为具体实体
# 2. 意图路由（routing.route_message）：判断用户意图，路由到对应模块（漫剧/配置/权限/闲聊）
# 3. 记忆更新（memory.update_memory）：更新短期记忆（Redis）和长期记忆（摘要压缩）
# 4. 子 Agent 执行（sub_agents.run_sub_agent）：根据模块调用对应的 ReAct Agent，选择工具执行
# 5. 返回结果：将 Java 方法名和参数返回给 Java 后端执行
#
# 模块划分：
# - models.py:     所有 Pydantic 数据模型
# - prompts.py:    提示词模板（指代消解、路由、记忆压缩、子 Agent）
# - permissions.py: 角色权限校验
# - memory.py:     记忆管理（短期记忆压缩、关键信息合并）
# - routing.py:    指代消解和意图路由
# - sub_agents.py: ReAct 子 Agent 执行
# - tools.py:      LangChain Tool 定义（各模块的业务工具）
