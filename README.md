# AI漫剧生成对话系统

基于自然对话的AI漫剧创作平台，通过多轮对话收集用户需求，自动生成完整的漫画剧本、分镜和角色设定。

## 项目概述

这是一个全栈的AI漫剧生成系统，用户可以通过自然对话的形式与AI创作助手交互，逐步完善漫剧设定，最终生成包含角色、剧情、分镜、对白等完整内容的漫画剧本。

**核心特性：**
- **智能对话交互**：多阶段 AI Agent 流水线（指代消解→意图路由→记忆管理→子Agent执行），自动理解用户意图并路由到对应操作
- **渐进式生成**：多轮对话逐步细化角色、剧情、风格设定
- **完整漫剧内容**：自动生成剧情大纲、分卷大纲、小节故事、分镜脚本
- **AI 资产生成**：自动识别人物/场景，调用豆包生成三视图设定图和环境概念图
- **异步任务架构**：RabbitMQ 消息队列驱动非对话 AI 任务，支持逐卷/逐节增量回传
- **智能记忆管理**：Redis 短期记忆 + 长期记忆压缩 + 关键事实提取，支持跨会话上下文理解
- **提示词动态管理**：数据库配置提示词，按题材/风格精确匹配特定提示词
- **用户权限系统**：ROOT/ADMIN/USER 三级角色，分级管理功能权限
- **功能权限管理**：细粒度控制各功能模块的访问权限，支持按功能开启/关闭
- **结构化输出防护**：LLM 结构化 JSON 输出自动修复，覆盖截断、转义、格式错误等异常
- **模块化架构**：前后端分离，AI 引擎独立部署，易于扩展和维护

## 系统架构

### 技术栈

| 层级 | 技术选型 |
|------|----------|
| **前端** | Vue 3 + TypeScript + Pinia + Vue Router + Axios + Element Plus |
| **后端** | Java 17 + Spring Boot 3.2 + MyBatis-Plus + Spring Security |
| **AI引擎** | Python + LangChain + FastAPI + Pydantic + 通义千问 (qwen-max) |
| **图片生成** | 豆包 SeedDream 4.5 (doubao-seedream-4-5-251128) |
| **数据库** | MySQL 8.0 + Redis 7 |
| **消息队列** | RabbitMQ 3.12+ |
| **文件存储** | 本地文件系统 (`./storage/`) |
| **API文档** | Knife4j (Spring Boot集成) |

### 架构图

```
┌─────────────┐    HTTP/WebSocket    ┌─────────────────┐    RabbitMQ     ┌─────────────────┐
│   Vue 前端   │ ────────────────────► │ Spring Boot 后端 │ ──────────────► │  Python AI 引擎  │
│  :8080      │ ◄──────────────────── │  :8085          │ ◄────────────── │  :5000          │
└─────────────┘    轮询结果           └────────┬────────┘    结果回传     └────────┬────────┘
                                              │                                  │
                              ┌───────────────┼───────────────┐                  │
                              │               │               │                  │
                      ┌───────▼───────┐ ┌─────▼───────┐ ┌─────▼───────┐   ┌─────▼───────┐
                      │    MySQL     │ │    Redis    │ │   RabbitMQ  │   │   豆包 API   │
                      │  :3306      │ │  :6379     │ │  :5672     │   │  图片生成    │
                      └──────────────┘ └────────────┘ └────────────┘   └─────────────┘
```

**调用链路：**
- **对话消息**：前端 → Java 后端 → Python Agent (HTTP) → 指代消解 → 意图路由 → 记忆更新 → 子 Agent → Java 执行
- **故事生成**：前端 → Java 后端 → RabbitMQ → Python Worker → RabbitMQ → Java 监听落库 → 前端轮询
- **消息持久化**：前端 → Java 后端 → Redis 短期记忆 → RabbitMQ → MySQL 持久化

## 快速开始

### 前置要求
- **Java 17+** (`java -version`)
- **Node.js 18+** (`node -v`)
- **Python 3.11+** (`python --version`)
- **Maven 3.9+** (`mvn -version`)
- **MySQL 8.0** (已安装并运行)
- **Redis 7** (已安装并运行)
- **RabbitMQ 3.12+** (已安装并运行)

### 环境配置

1. **克隆项目**
```bash
git clone <repository-url>
cd aisay
```

2. **数据库初始化**
```sql
mysql -u root -p < backend/src/main/resources/db/init.sql
```

3. **配置检查**
确保 `backend/src/main/resources/application.yml` 中的数据库连接信息与本地环境一致。

4. **Python AI 配置**
在 `python-ai/` 目录下创建 `api.yml`，填入通义千问和豆包 API Key：
```yaml
tongyi:
  api_key: "your-tongyi-api-key"
doubao:
  ARK_API_KEY: "your-doubao-api-key"
```

### 启动服务

**窗口1：启动 Spring Boot 后端**
```bash
cd backend
mvn -gs ../settings.phase1.xml spring-boot:run
```

**窗口2：启动 Vue 前端**
```bash
cd frontend
npm install
npm run dev
```

**窗口3：启动 Python AI 引擎**
```bash
cd python-ai
pip install -r requirements.txt
python main.py
```

### 访问应用
- **前端界面**: http://localhost:8080
- **后端API文档**: http://localhost:8085/doc.html
- **RabbitMQ管理界面**: http://localhost:15672 (guest/guest)

## 项目结构

```
aisay/
├── backend/                        # Spring Boot 后端
│   └── src/main/java/com/aisay/manga/
│       ├── controller/             # REST API 控制器
│       ├── service/                # 业务逻辑层
│       ├── service/impl/           # 业务实现
│       ├── repository/             # MyBatis-Plus Mapper + Redis Repository
│       ├── entity/                 # 数据库实体
│       ├── dto/
│       │   ├── request/            # 请求 DTO
│       │   ├── response/           # 响应 DTO
│       │   ├── ai/                 # Java ↔ Python AI DTO
│       │   └── chat/               # 聊天相关 DTO
│       ├── config/                 # 配置类 (Security, RabbitMQ, Redis, etc.)
│       └── utils/                  # 工具类 (JWT, 文件存储, AI 任务发布, 聊天持久化)
│
├── frontend/                       # Vue 3 前端
│   └── src/
│       ├── views/                  # 页面组件 (Chat, StoryList, StoryDetail, User, Prompt, etc.)
│       ├── components/             # 可复用组件
│       │   ├── chat/               # 聊天组件 (MessageBubble, InputArea, SessionList)
│       │   └── story/              # 漫剧组件 (CharacterCard)
│       ├── stores/                 # Pinia 状态管理
│       ├── api/                    # API 接口封装
│       ├── router/                 # Vue Router 路由配置
│       └── types/                  # TypeScript 类型定义
│
├── python-ai/                      # Python AI 引擎
│   ├── main.py                     # FastAPI 入口，挂载 router
│   ├── ai_runtime.py               # 通用运行时 (LLM 实例, 回调, 日志, 重试)
│   ├── story_ai.py                 # 故事 API 兼容门面
│   ├── story_ai_pkg/               # 故事 AI 包（按职责拆分）
│   │   ├── models.py               # Pydantic 数据模型
│   │   ├── templates.py            # PromptTemplate 初始化
│   │   ├── prompt_repository.py    # 数据库提示词加载
│   │   ├── formatters.py           # 文本格式化工具
│   │   ├── outline.py              # 剧情大纲生成与修改
│   │   ├── volumes.py              # 分卷大纲生成、修改与正文
│   │   ├── sections.py             # 分卷小节生成
│   │   ├── assets.py               # 人物/场景资产与豆包图片
│   │   ├── scripts.py              # 分镜脚本生成
│   │   └── router.py               # FastAPI 路由器
│   ├── chat_ai.py                  # 对话 Agent 入口
│   ├── chat_agent_pkg/             # 智能对话 Agent 包
│   │   ├── models.py               # 对话相关数据模型
│   │   ├── prompts.py              # 对话提示词（指代消解、路由、记忆压缩、子Agent）
│   │   ├── routing.py              # 指代消解与意图路由
│   │   ├── memory.py               # 记忆管理（短期记忆压缩、关键事实合并）
│   │   ├── sub_agents.py           # ReAct 子 Agent 执行
│   │   ├── tools.py                # LangChain Tool 定义（各模块业务工具）
│   │   └── permissions.py          # 角色权限校验
│   ├── prompt.py                   # 提示词模板（数据库兜底）
│   ├── rabbitmq_worker.py          # RabbitMQ 消费者
│   ├── requirements.txt            # Python 依赖
│   └── api.yml                     # 通义千问 & 豆包 API Key (已 gitignore)
│
└── config.txt                      # 基础设施连接配置
```

## 核心功能

### 1. 用户认证与权限
- JWT 无状态认证，token 有效期 24 小时
- 注册、登录、用户资料管理、头像上传
- 三级角色权限：ROOT（超级管理员）、ADMIN（管理员）、USER（普通用户）
- ROOT 可管理所有用户角色，ADMIN 可管理大纲配置和提示词

### 2. 智能对话系统
- **多阶段 AI Agent 流水线**：
  1. **指代消解**：将"它"、"这个"等指代词替换为具体实体
  2. **意图路由**：判断用户意图，提取关键信息，路由到对应模块
  3. **记忆更新**：Redis 短期记忆 + 长期记忆压缩 + 关键事实提取
  4. **子 Agent 执行**：ReAct 模式选择工具，返回 Java 方法和参数
- 支持无绑定漫剧的自由对话
- 消息持久化通过 RabbitMQ 异步写入 MySQL
- 对话绑定漫剧，围绕一部作品持续迭代

### 3. 剧情大纲生成
- 用户输入题材、可选剧情和漫剧风格，AI 自动生成完整剧情大纲
- 大纲包含：故事摘要、主线剧情、主要角色设定
- 支持大纲修改：用户输入修改意见，AI 自动重写
- 漫剧风格贯穿后续所有图片和视频生成

### 4. 分卷大纲生成
- 两阶段生成：先判断总分卷数，再逐卷生成详细大纲
- 每卷包含：卷名、摘要、详细剧情、卷末悬念
- 逐卷增量回传，前端可逐步查看已生成的分卷
- 支持自动修改（AI 重写）和手动修改（直接编辑）

### 5. 分卷小节故事生成
- 将单卷大纲拆解为 4-12 个小节
- 逐节生成具体故事细节，包含场景、动作、对话、冲突
- 增量回传，前端逐步展示已生成的小节
- 小节生成采用纯文本标签解析，避免长正文 JSON 转义失败

### 6. 分镜脚本生成
- 根据小节故事生成镜头级分镜脚本
- 每个镜头包含：镜头号、时长、景别、运镜、动作、对白
- 使用结构化输出约束，确保分镜格式统一
- 支持自动计算总时长

### 7. AI 资产生成
- 每个小节可自动识别出现的人物和场景
- 人物资产生成三视图设定图（正面、侧面、背面）
- 场景资产生成环境概念图
- 调用豆包 SeedDream 4.5 模型生成图片
- 已识别的人物/场景自动复用，避免重复生成
- 支持上传人物音频，为角色配音

### 8. 提示词动态管理
- 数据库存储提示词模板，支持在线编辑
- 按任务类型分类管理（剧情大纲、分卷、小节、资产、脚本、对话）
- 支持默认提示词和特定提示词（按题材/风格匹配）
- 特定提示词优先级高于默认提示词
- Python 引擎优先从数据库加载，数据库不可用时回退到文件兜底

### 9. 大纲配置管理
- 数据库管理题材和漫剧风格选项
- 生成大纲弹窗从数据库动态加载选项列表
- 支持新增、编辑、启停和删除

### 10. 功能权限管理
- 细粒度功能级权限控制，覆盖对话、漫剧、大纲配置、提示词管理等所有模块
- ROOT 可在管理页面按功能设置允许的角色等级
- 前端根据功能权限动态显示/隐藏菜单入口
- 对话 Agent 路由时同步检查功能权限，未授权功能自动拒绝

### 11. 异步任务架构
- RabbitMQ 消息队列驱动所有非对话 AI 任务
- Java 提交任务后立即返回，Python 后台异步处理
- 支持 partial/completed 消息，实现增量结果回传
- LLM 调用自动重试（网络超时、5xx 错误）
- 结构化 JSON 输出自动修复（截断、转义、格式错误）
- 前端轮询获取最新结果

### 12. LLM 结构化输出防护
- 统一防护函数 `invoke_structured_output_with_guard`，保护所有 `with_structured_output` 调用
- Pydantic 校验失败时自动提取原始 JSON 并本地修复
- 覆盖常见问题：Markdown 代码块包裹、字符串未闭合、未转义双引号
- 修复失败后重新调用大模型，最多重试 3 次
- 网络错误和 JSON 结构错误分开处理，互不干扰

## 数据库设计

系统使用 MySQL 存储核心业务数据：

### 实体关系图
```mermaid
erDiagram
    users ||--o{ chat_sessions : has
    users ||--o{ stories : creates
    chat_sessions }o--|| stories : binds
    chat_sessions ||--o{ messages : contains
    stories ||--o{ characters : has
    stories ||--o{ story_volume_outlines : has
    story_volume_outlines ||--o{ story_volume_sections : has
    story_volume_sections ||--o{ story_section_scripts : has
    stories ||--o{ story_assets : has
    story_volume_sections ||--o{ story_section_assets : has
    story_assets ||--o{ story_section_assets : has
```

### 核心表结构
- **users**: 用户账户信息（含 role 角色字段）
- **chat_sessions**: 聊天会话（可选绑定 story_id）
- **messages**: 会话内的用户与 AI 消息
- **stories**: 漫剧主记录（标题、摘要、大纲、风格、状态）
- **characters**: 主要角色设定
- **story_volume_outlines**: 分卷大纲（一 story 多卷）
- **story_volume_sections**: 分卷小节故事（一卷多节）
- **story_section_scripts**: 小节分镜脚本（一节多镜头）
- **story_assets**: 人物/场景资产（图片、音频、描述）
- **story_section_assets**: 小节与资产的多对多关联
- **story_outline_options**: 大纲配置（题材和风格选项）
- **ai_prompts**: AI 提示词模板（支持特定匹配）
- **ai_prompt_parameters**: 提示词参数说明
- **feature_permissions**: 功能权限配置（功能 key、允许角色、启用状态）

### 故事状态流转
```
draft → generating → draft (大纲生成完成)
draft → revising → draft (大纲修改完成)
draft → volume_pending → draft (分卷生成完成)
draft → volume_section_pending → draft (小节生成完成)
draft → section_asset_pending → draft (资产图片生成完成)
draft → section_script_pending → draft (分镜脚本生成完成)
任意状态 → failed (任务失败)
```

## API 接口

### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/user/profile` - 获取用户信息
- `PUT /api/user/profile` - 更新用户信息

### 聊天服务
- `POST /api/chat/start` - 开始新对话（可选绑定 storyId）
- `POST /api/chat/message` - 发送消息（Agent 路由分发）
- `GET /api/chat/history/{sessionId}` - 获取历史消息
- `GET /api/chat/sessions` - 获取用户会话列表
- `DELETE /api/chat/session/{sessionId}` - 删除会话

### 漫剧服务
- `POST /api/story/generate` - 生成剧情大纲（异步）
- `POST /api/story/{id}/outline/revise` - 修改剧情大纲（异步）
- `PUT /api/story/{id}/detail` - 手动保存大纲和角色
- `POST /api/story/{id}/volume-outline/generate` - 生成分卷大纲（异步）
- `POST /api/story/{id}/volume-outline/revise` - 自动修改分卷大纲（异步）
- `PUT /api/story/{id}/volume-outline` - 手动修改分卷大纲
- `POST /api/story/{id}/volume-outline/{volumeId}/sections/generate` - 生成小节故事（异步）
- `POST /api/story/{id}/volume-sections/{sectionId}/assets/generate` - 生成小节资产图片（异步）
- `POST /api/story/{id}/volume-sections/{sectionId}/script/generate` - 生成分镜脚本（异步）
- `POST /api/story/{id}/assets/{assetId}/audio` - 上传人物音频
- `GET /api/story/{id}` - 获取漫剧详情
- `GET /api/story/list` - 获取漫剧列表
- `PUT /api/story/{id}` - 更新漫剧
- `DELETE /api/story/{id}` - 删除漫剧

### 管理接口
- `GET /api/story-outline-options` - 获取大纲配置列表
- `POST /api/story-outline-options` - 新增大纲配置（ADMIN+）
- `PUT /api/story-outline-options/{id}` - 修改大纲配置（ADMIN+）
- `DELETE /api/story-outline-options/{id}` - 删除大纲配置（ADMIN+）
- `GET /api/prompts` - 获取提示词列表（ADMIN+）
- `POST /api/prompts` - 新增提示词（ADMIN+）
- `PUT /api/prompts/{id}` - 修改提示词（ADMIN+）
- `DELETE /api/prompts/{id}` - 删除提示词（ADMIN+）
- `GET /api/users` - 获取用户列表（ROOT）
- `PUT /api/users/{id}/role` - 修改用户角色（ROOT）
- `GET /api/feature-permissions` - 获取功能权限列表（ROOT）
- `PUT /api/feature-permissions/{id}` - 修改功能权限（ROOT）
- `GET /api/feature-permissions/me` - 获取当前用户可用功能

### 文件服务
- `POST /api/files/upload` - 文件上传（需认证）
- `GET /api/files/{path}` - 文件访问（公开，无需认证）

详细API文档启动后访问：http://localhost:8085/doc.html

## 开发指南

### 后端开发
```bash
cd backend
mvn -gs ../settings.phase1.xml compile      # 编译
mvn -gs ../settings.phase1.xml test         # 测试
mvn -gs ../settings.phase1.xml spring-boot:run  # 启动
```

### 前端开发
```bash
cd frontend
npm install      # 安装依赖
npm run dev      # 开发模式
npm run build    # 生产构建
```

### Python AI 引擎开发
```bash
cd python-ai
pip install -r requirements.txt   # 安装依赖
python main.py                    # 启动 FastAPI + RabbitMQ Worker
```

## 故障排除

### 常见问题

1. **后端编译失败**
   - 检查 Java 版本是否为 17+
   - 使用项目内 settings：`mvn -gs ../settings.phase1.xml compile`

2. **数据库连接失败**
   - 确认 MySQL 服务已启动
   - 检查 `application.yml` 中的连接信息
   - 确认已执行 `init.sql` 初始化数据库

3. **前端无法启动**
   - 检查 Node.js 版本：`node -v` >= 18.0.0
   - 清理重新安装：`rm -rf node_modules && npm install`

4. **Python AI 引擎报错**
   - 确认 `python-ai/api.yml` 中的 API Key 正确
   - 确认 RabbitMQ 服务已启动
   - 查看控制台 `[rabbitmq-worker]` 日志排查任务失败原因

5. **故事状态变为 failed**
   - 查看 Python 控制台日志中的错误信息
   - 确认通义千问 API Key 有效且有余额
   - 确认 RabbitMQ 连接正常

6. **图片无法显示**
   - 确认 `/api/files/**` 已在 SecurityConfig 中放行（无需认证）
   - 确认 `storage/generated-assets/` 目录存在且有写入权限
   - 确认豆包 API Key 有效

7. **LLM 调用偶发失败**
   - Python 已内置自动重试机制（最多 3 次，指数退避）
   - 网络错误和 JSON 结构错误分开处理，互不干扰
   - 查看控制台 `llm transient error, retrying...` 日志
   - 如果 3 次重试后仍失败，说明上游服务暂时不可用

8. **结构化输出 JSON 解析失败**
   - Python 已内置 `invoke_structured_output_with_guard` 防护函数
   - 自动修复常见问题：Markdown 代码块、字符串未闭合、未转义引号
   - 修复失败后会重新调用大模型，最多重试 3 次
   - 查看控制台 `structured output validation failed after 3 attempts` 日志

8. **提示词未生效**
   - 确认已执行 `20260522_create_ai_prompts.sql` 和 `20260522_add_ai_prompt_specific_matching.sql`
   - 确认 Python 已安装 `pymysql`：`pip install pymysql`
   - 如果数据库不可用，Python 会自动回退到 `prompt.py` 文件

9. **对话记忆异常**
   - 确认 Redis 服务已启动且连接正常
   - 短期记忆存储在 Redis 中，重启 Redis 会丢失未持久化的对话
   - 长期记忆和关键事实通过 RabbitMQ 异步写入 MySQL，重启不影响

## 项目进度

详细开发进度见：[progress.md](./progress.md)

架构说明见：[architecture.md](./architecture.md)

## 许可证

本项目采用 MIT 许可证。
