"""共享测试配置。

将 python-ai 目录加入 sys.path，并提供 API 集成测试所需的 fixtures。
"""
import sys
import uuid
from pathlib import Path

import httpx
import pytest

# 将 python-ai 目录加入 Python 路径
_python_ai_dir = str(Path(__file__).resolve().parent.parent)
if _python_ai_dir not in sys.path:
    sys.path.insert(0, _python_ai_dir)

# ── API 集成测试配置 ──────────────────────────────────────────────────

BASE_URL = "http://localhost:8085"


def _check_server_available() -> bool:
    """检查 Java 后端是否可用。

    只要能连通并收到 HTTP 响应（任何状态码），就认为后端已启动。
    连接失败（ConnectionRefused、超时等）才认为后端不可用。
    """
    try:
        with httpx.Client(base_url=BASE_URL, timeout=5) as client:
            client.get("/api/auth/login")
            return True
    except Exception as exc:
        print(f"[conftest] 后端不可用: {exc}")
        return False


@pytest.fixture(scope="session")
def base_url():
    """Java 后端基础 URL。"""
    return BASE_URL


@pytest.fixture(scope="session")
def server_available():
    """检查后端是否可用，不可用时跳过所有 API 测试。"""
    if not _check_server_available():
        pytest.skip("Java 后端未启动，跳过 API 集成测试")
    return True


@pytest.fixture(scope="session")
def api_client(server_available):
    """httpx 客户端实例，自动处理 JSON 响应。"""
    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        yield client


@pytest.fixture(scope="session")
def registered_user(api_client):
    """注册一个测试用户并返回用户信息。

    使用随机用户名避免重复注册冲突。
    """
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "Test123456"
    email = f"{username}@test.com"

    response = api_client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
    })

    if response.status_code == 200:
        data = response.json()
        return {
            "username": username,
            "password": password,
            "email": email,
            "data": data.get("data"),
        }

    # 如果注册失败（如用户名已存在），尝试用随机用户名重新注册
    username = f"testuser_{uuid.uuid4().hex[:12]}"
    email = f"{username}@test.com"
    response = api_client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
    })
    data = response.json()
    return {
        "username": username,
        "password": password,
        "email": email,
        "data": data.get("data"),
    }


@pytest.fixture(scope="session")
def auth_token(api_client, registered_user):
    """登录测试用户并返回 JWT token。"""
    response = api_client.post("/api/auth/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"],
    })
    assert response.status_code == 200, f"登录失败: {response.text}"
    data = response.json()
    return data["data"]["token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """带 JWT token 的请求头。"""
    return {"Authorization": f"Bearer {auth_token}"}
