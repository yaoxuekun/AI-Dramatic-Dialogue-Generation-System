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
- **结构化输出防护**：LLM 结构化 JSON 输出自动修复，覆盖截断、转义、格式错误等异常

## 系统架构

### 技术栈

| 层级 | 技术选型 |
|------|----------|
| **前端** | Vue 3 + TypeScript + Pinia + Vue Router + Axios + Element Plus |
| **后端** | Python + FastAPI + PyMySQL + Redis + RabbitMQ |
| **AI引擎** | Python + LangChain + FastAPI + Pydantic + 通义千问 (qwen-max) |
| **图片生成** | 豆包 SeedDream 4.5 |
| **数据库** | MySQL 8.0 + Redis 7 |
| **消息队列** | RabbitMQ 3.12+ |

### 架构图

```
┌─────────────┐    HTTP          ┌─────────────────┐    RabbitMQ     ┌─────────────────┐
│   Vue 前端   │ ───────────────► │  FastAPI 后端    │ ──────────────► │  Python AI 引擎  │
│  :8080      │ ◄─────────────── │  :8085          │ ◄────────────── │  :5000          │
└─────────────┘    轮询结果       └────────┬────────┘    结果回传     └────────┬────────┘
                                          │                                  │
                          ┌───────────────┼───────────────┐                  │
                          │               │               │                  │
                  ┌───────▼───────┐ ┌─────▼───────┐ ┌─────▼───────┐   ┌─────▼───────┐
                  │    MySQL     │ │    Redis    │ │   RabbitMQ  │   │   豆包 API   │
                  │  :3306      │ │  :6379     │ │  :5672     │   │  图片生成    │
                  └──────────────┘ └────────────┘ └────────────┘   └─────────────┘
```

**调用链路：**
- **对话消息**：前端 → FastAPI 后端 → Python Agent (HTTP) → 指代消解 → 意图路由 → 记忆更新 → 子 Agent → 后端执行
- **故事生成**：前端 → FastAPI 后端 → RabbitMQ → Python Worker → RabbitMQ → 后端监听落库 → 前端轮询
- **消息持久化**：前端 → FastAPI 后端 → Redis 短期记忆 → RabbitMQ → MySQL 持久化

## 快速开始

### 前置要求
- **Node.js 18+** (`node -v`)
- **Python 3.11+** (`python --version`)
- **MySQL 8.0** (已安装并运行)
- **Redis 7** (已安装并运行)
- **RabbitMQ 3.12+** (已安装并运行)

### 环境配置

1. **克隆项目**
```bash
git clone https://github.com/yaoxuekun/AI-Dramatic-Dialogue-Generation-System.git
cd AI-Dramatic-Dialogue-Generation-System
```

2. **数据库初始化**
```bash
mysql -u root -p < fastapi-backend/db/init.sql
```

3. **配置后端环境变量**
```bash
cd fastapi-backend
cp .env.example .env
# 编辑 .env，填入你的数据库、Redis、RabbitMQ 连接信息
```

4. **配置 Python AI 引擎**
```bash
cd python-ai
cp api.yml.example api.yml
# 编辑 api.yml，填入通义千问和豆包 API Key
```

### 启动服务

**窗口1：启动 FastAPI 后端**
```bash
cd fastapi-backend
pip install -r requirements.txt
python main.py
```

**窗口2：启动 Python AI 引擎**
```bash
cd python-ai
pip install -r requirements.txt
python main.py
```

**窗口3：启动 Vue 前端**
```bash
cd frontend
npm install
npm run dev
```

### 访问应用
- **前端界面**: http://localhost:8080
- **后端API文档**: http://localhost:8085/docs
- **RabbitMQ管理界面**: http://localhost:15672 (guest/guest)

## 项目结构

```
AI-Dramatic-Dialogue-Generation-System/
├── fastapi-backend/               # Python FastAPI 后端
│   ├── main.py                    # 应用入口
│   ├── config.py                  # 配置管理
│   ├── database.py                # 数据库连接池
│   ├── redis_client.py            # Redis 连接
│   ├── rabbitmq_client.py         # RabbitMQ 连接
│   ├── dependencies.py            # 认证依赖注入
│   ├── constants.py               # 常量定义
│   ├── routers/                   # API 路由
│   │   ├── auth.py                # 认证接口
│   │   ├── user.py                # 用户管理
│   │   ├── chat.py                # 聊天服务
│   │   ├── story.py               # 漫剧服务
│   │   ├── file.py                # 文件服务
│   │   ├── outline_option.py      # 大纲配置
│   │   ├── feature_permission.py  # 功能权限
│   │   └── prompt.py              # Prompt 管理
│   ├── schemas/                   # Pydantic 数据模型
│   ├── repositories/              # 数据访问层
│   ├── services/                  # 业务逻辑层
│   │   ├── task_publisher.py      # RabbitMQ 任务发布
│   │   ├── result_consumer.py     # RabbitMQ 结果消费者
│   │   ├── chat_persist_consumer.py # 聊天持久化消费者
│   │   └── chat_dispatcher.py     # 对话白名单分发
│   ├── db/                        # 数据库初始化脚本
│   │   └── init.sql               # 数据库初始化
│   └── utils/                     # 工具类
│
├── python-ai/                     # Python AI 引擎
│   ├── main.py                    # FastAPI 入口
│   ├── ai_runtime.py              # 通用运行时 (LLM, 重试, JSON修复)
│   ├── story_ai.py                # 故事 API 兼容门面
│   ├── story_ai_pkg/              # 故事 AI 包
│   │   ├── outline.py             # 剧情大纲生成
│   │   ├── volumes.py             # 分卷大纲生成
│   │   ├── sections.py            # 小节故事生成
│   │   ├── assets.py              # 人物/场景资产
│   │   ├── scripts.py             # 分镜脚本生成
│   │   └── prompt_repository.py   # Prompt 动态加载
│   ├── chat_ai.py                 # 对话 Agent 入口
│   ├── chat_agent_pkg/            # 智能对话 Agent 包
│   │   ├── routing.py             # 意图路由
│   │   ├── memory.py              # 记忆管理
│   │   ├── sub_agents.py          # ReAct 子 Agent
│   │   └── tools.py               # LangChain Tool 定义
│   ├── prompt.py                  # 提示词模板 (兜底)
│   ├── rabbitmq_worker.py         # RabbitMQ 消费者
│   └── requirements.txt           # Python 依赖
│
├── frontend/                      # Vue 3 前端
│   └── src/
│       ├── views/                 # 页面组件
│       ├── components/            # 可复用组件
│       ├── stores/                # Pinia 状态管理
│       ├── api/                   # API 接口封装
│       ├── router/                # Vue Router 路由
│       └── types/                 # TypeScript 类型
│
└── config.txt.example             # 基础设施配置模板
```

## 核心功能

### 1. 用户认证与权限
- JWT 无状态认证，token 有效期 24 小时
- 注册、登录、用户资料管理、头像上传
- 三级角色权限：ROOT（超级管理员）、ADMIN（管理员）、USER（普通用户）

### 2. 智能对话系统
- **多阶段 AI Agent 流水线**：
  1. **指代消解**：将"它"、"这个"等指代词替换为具体实体
  2. **意图路由**：判断用户意图，提取关键信息，路由到对应模块
  3. **记忆更新**：Redis 短期记忆 + 长期记忆压缩 + 关键事实提取
  4. **子 Agent 执行**：ReAct 模式选择工具，返回方法名和参数
- 对话白名单分发：AI 返回的方法名经后端白名单校验后执行

### 3. 漫剧生成（5个阶段）
1. **剧情大纲**：用户输入题材和风格，AI 生成完整大纲和角色设定
2. **分卷大纲**：两阶段生成，逐卷增量回传
3. **小节故事**：逐节生成具体故事细节
4. **人物/场景图片**：识别资产并调用豆包生成图片
5. **分镜脚本**：生成镜头级分镜脚本

### 4. 提示词动态管理
- 数据库存储提示词模板，支持在线编辑
- 按题材/风格匹配特定提示词，优先级：特定 > 默认 > 代码兜底

### 5. 异步任务架构
- RabbitMQ 驱动所有非对话 AI 任务
- 支持 partial/completed 消息，实现增量结果回传
- LLM 调用自动重试 + 结构化 JSON 输出自动修复

## 数据库设计

### 核心表
- **users**: 用户账户信息
- **chat_sessions**: 聊天会话
- **messages**: 会话消息
- **stories**: 漫剧主记录
- **characters**: 角色设定
- **story_volume_outlines**: 分卷大纲
- **story_volume_sections**: 小节故事
- **story_section_scripts**: 分镜脚本
- **story_assets**: 人物/场景资产
- **ai_prompts**: AI 提示词模板
- **feature_permissions**: 功能权限配置

### 故事状态流转
```
draft → generating → volume_pending → volume_section_pending
→ section_asset_pending → section_script_pending → draft
```

## API 接口

### 认证
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录

### 聊天
- `POST /api/chat/start` - 创建对话
- `POST /api/chat/message` - 发送消息
- `GET /api/chat/history/{sessionId}` - 历史消息
- `GET /api/chat/sessions` - 会话列表

### 漫剧
- `POST /api/story/generate` - 生成剧情大纲
- `POST /api/story/{id}/outline/revise` - 修改大纲
- `POST /api/story/{id}/volume-outline/generate` - 生成分卷
- `POST /api/story/{id}/volume-outline/{vid}/sections/generate` - 生成小节
- `POST /api/story/{id}/volume-sections/{sid}/assets/generate` - 生成图片
- `POST /api/story/{id}/volume-sections/{sid}/script/generate` - 生成脚本

### 管理
- `GET/POST/PUT/DELETE /api/prompts` - Prompt 管理
- `GET/POST/PUT/DELETE /api/story-outline-options` - 大纲配置
- `GET/PUT /api/feature-permissions` - 功能权限

## 故障排除

1. **后端启动失败**
   - 检查 `.env` 配置是否正确
   - 确认 MySQL、Redis、RabbitMQ 已启动

2. **AI 引擎报错**
   - 检查 `python-ai/api.yml` 中的 API Key
   - 确认 RabbitMQ 连接正常

3. **故事状态变为 failed**
   - 查看 Python 控制台日志
   - 确认通义千问 API Key 有效

4. **图片无法显示**
   - 确认豆包 API Key 有效
   - 确认 `storage/` 目录有写入权限

## 许可证

本项目采用 MIT 许可证。
