# Python AI 引擎入口模块
# 负责创建 FastAPI 应用、挂载业务路由、启动后台 RabbitMQ Worker

# uvicorn：ASGI 服务器，用于启动 FastAPI 应用
import uvicorn

# FastAPI：Web 框架，提供 HTTP 接口给 Java 后端调用
from fastapi import FastAPI

# 从 chat_ai 模块导入对话 Agent 路由，挂载到 /api/chat/* 路径
from chat_ai import router as chat_router

# 从 rabbitmq_worker 模块导入后台启动函数，FastAPI 启动时自动开启 RabbitMQ 消费线程
from rabbitmq_worker import start_rabbitmq_worker

# 从 story_ai 模块导入故事相关路由，挂载到 /api/story/* 路径
from story_ai import router as story_router


# 创建 FastAPI 应用实例，标题用于 API 文档展示
app = FastAPI(title="Aisay Python AI Engine")

# 挂载故事相关路由：/api/story/outline、/api/story/volume-outline 等
app.include_router(story_router)

# 挂载对话 Agent 路由：/api/chat/agent
app.include_router(chat_router)


@app.on_event("startup")
def start_background_workers() -> None:
    """FastAPI 启动生命周期钩子。
    在应用启动时自动调用，启动 RabbitMQ 后台消费线程，
    让非对话类 AI 任务（剧情大纲、分卷、小节等）以异步方式执行。
    """
    start_rabbitmq_worker()


# 当直接运行 python main.py 时，启动 uvicorn 服务器监听 0.0.0.0:5000
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
