# FastAPI 路由器模块
# 本文件只负责创建 APIRouter 实例，供各业务模块（outline.py、volumes.py 等）导入并注册路由。
# 最终在 __init__.py 中导出 router，由 main.py 挂载到 FastAPI app。

# APIRouter：FastAPI 路由组织器，用于将路由分组注册
from fastapi import APIRouter

# 创建故事 AI 路由器实例，所有 /api/story/* 接口都注册到这个路由器上
router = APIRouter()
