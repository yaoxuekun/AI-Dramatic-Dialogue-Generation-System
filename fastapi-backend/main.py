# FastAPI后端入口
import time
import uvicorn
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pymysql import MySQLError
from schemas.common import ApiResponse, error_response, ErrorCode, success_response

from config import settings
from contextlib import asynccontextmanager
import database
import redis_client
import rabbitmq_client
import json
import logging
from utils.jwt_util import generate_token, validate_token, get_user_id_from_token
from routers import auth, user, story, chat, file, outline_option, feature_permission, prompt
from services.result_consumer import start_result_consumer
from services.chat_persist_consumer import start_chat_persist_consumer
import sys

logger = logging.getLogger(__name__)
# 配置日志输出到控制台（包含堆栈信息）
logging.basicConfig(
    level=logging.DEBUG,  # 设为 DEBUG 以显示最详细的信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # 输出到控制台
    ]
)

# 设置 uvicorn 的日志级别，让它也显示更详细的信息
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)

# 应用启动事件：初始化数据库连接池
@asynccontextmanager
async def lifespan(app: FastAPI):

    print("正在初始化服务...")

    # 1.初始化数据库
    database.init_db_pool()
    if not database.test_connection():
        raise RuntimeError(
            "❌ 数据库连接失败，服务拒绝启动！"
        )  # 这里抛出异常，yield 不会执行，端口不会监听
    print("✅ 数据库连接成功")

    # 2.初始化 Redis
    redis_client.init_redis_pool()
    if redis_client.test_redis_connection():
        print("Redis 连接成功")
    else:
        raise RuntimeError("Redis 连接失败，服务终止启动")

    # 将 redis 客户端挂在到 app.state，方便路由中调用
    app.state.redis = redis_client.get_redis()

    # 3.初始化RabbitMQ
    rabbitmq_client.init_rabbitmq()
    if rabbitmq_client.test_rabbitmq_connection():
        print("RabbitMQ 连接成功，队列已声明")
    else:
        raise RuntimeError("RabbitMQ 连接失败，服务终止启动")
    app.state.rabbitmq_conn = rabbitmq_client.get_connection()

    # 4.启动 RabbitMQ 消费者（后台 daemon 线程）
    start_result_consumer()
    start_chat_persist_consumer()

    # 创建存储目录
    os.makedirs(settings.STORAGE_ROOT_PATH, exist_ok=True)
    for subdir in [
        "avatars",
        "resources",
        "covers",
        "generated-assets",
        "character-audio",
    ]:
        os.makedirs(os.path.join(settings.STORAGE_ROOT_PATH, subdir), exist_ok=True)

    yield  # 只有上面没报错，才能到这里，服务才会启动

    # ---- 关闭 ----
    print("🛑 服务正常关闭，释放资源...")


app = FastAPI(
    title="Aisay Backend",
    description="AI漫剧生成对话系统后端",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api", tags=["认证"])
app.include_router(user.router, prefix="/api", tags=["用户管理"])
app.include_router(chat.router, prefix="/api", tags=["对话"])
app.include_router(story.router, prefix="/api", tags=["漫剧"])
app.include_router(file.router, prefix="/api", tags=["文件存储"])
app.include_router(outline_option.router, prefix="/api", tags=["大纲配置"])
app.include_router(feature_permission.router, prefix="/api", tags=["功能权限"])
app.include_router(prompt.router, prefix="/api", tags=["Prompt管理"])


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    捕获 FastAPI/Starlette 抛出的 HTTPException（如404,403等）
    """
    # 如果是401，特殊处理让前端跳转登录
    if exc.status_code == 401:
        return JSONResponse(
            status_code=401,
            content=error_response(
                code=ErrorCode.UNAUTHORIZED, message="未认证或token已过期，请重新登录"
            ).model_dump(),
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.status_code, message=exc.detail or "请求异常"
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    捕获 Pydantic 参数校验失败（如 JSON 格式不对、缺少必填字段）
    """
    # 提取详细的校验错误信息，方便前端定位问题
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}:{error['msg']}")

    error_msg = ";".join(errors) if errors else "参数校验失败"
    return JSONResponse(
        status_code=422,
        content=error_response(
            code=ErrorCode.VALIDATION_ERROR, message=error_msg
        ).model_dump(),
    )


@app.exception_handler(MySQLError)
async def mysql_error_handler(request: Request, exc: MySQLError):
    """
    捕获 MySQL 数据库错误（如连接断开、SQL 语法错误）
    注意：生产环境不要暴露具体 SQL 错误给前端，只记录日志
    """
    logger.error(f"数据库错误：{exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            code=ErrorCode.INTERNAL_ERROR, message="数据库服务异常，请稍后重试"
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    兜底异常处理器：捕获所有未被上面捕获的异常。
    生产环境只记录日志，不暴露详情。
    """
    logger.error(f"未知异常:{exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            code=ErrorCode.INTERNAL_ERROR, message="服务器内部错误，请稍后重试"
        ).model_dump(),
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    return success_response(data={"status": "ok", "service": "aisay-backend"})


# 根路径，可简单返回信息
@app.get("/")
async def root():
    return {"message": "Aisay Backend is running", "docs": "/docs", "redoc": "/redoc"}


@app.get("/test-redis")
def test_redis(request: Request):
    redis = request.app.state.redis

    redis.set("test_key", "Hello Redis")
    value = redis.get("test_key")
    return {"status": "ok", "retrieved_value": value}


@app.get("/test-rabbitmq")
def test_rabbitmq(request: Request):
    test_data = {"test": "hello rabbitmq", "timestamp": "2026-07-19"}
    rabbitmq_client.publish_message(
        routing_key=settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
        message_body=json.dumps(test_data, ensure_ascii=False),
    )
    return {"status": "ok", "message": "测试消息已发送到队列"}


@app.get("/test-error/400")
def test_bad_request():
    from fastapi import HTTPException

    raise HTTPException(status_code=400, detail="这是一个测试的400错误")


@app.get("/test-error/500")
def test_internal_error():
    raise RuntimeError("这是一个测试的 500 内部错误")


# main.py 中添加（仅供测试，后续可删除）
@app.get("/test-jwt")
def test_jwt():
    token = generate_token(1, "testuser")
    valid = validate_token(token)
    uid = get_user_id_from_token(token)
    return {"token": token, "valid": valid, "user_id": uid}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,  # 开发时自动重启
    )
