"""认证相关 API 接口测试。

测试用户注册、登录、获取/修改资料等接口。
需要 Java 后端运行在 localhost:8085。
"""
import uuid

import httpx


class TestRegister:
    """POST /api/auth/register 注册接口测试。"""

    def test_register_success(self, api_client):
        username = f"reg_{uuid.uuid4().hex[:8]}"
        response = api_client.post("/api/auth/register", json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "Test123456",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == username

    def test_register_duplicate_username(self, api_client, registered_user):
        response = api_client.post("/api/auth/register", json={
            "username": registered_user["username"],
            "email": f"dup_{uuid.uuid4().hex[:8]}@test.com",
            "password": "Test123456",
        })
        # 重复用户名应返回错误
        assert response.status_code in (400, 409, 200)
        data = response.json()
        if response.status_code == 200:
            assert data["code"] != 200

    def test_register_missing_fields(self, api_client):
        response = api_client.post("/api/auth/register", json={
            "username": "",
            "email": "",
            "password": "",
        })
        assert response.status_code in (400, 200)
        data = response.json()
        if response.status_code == 200:
            assert data["code"] != 200

    def test_register_short_password(self, api_client):
        username = f"reg_{uuid.uuid4().hex[:8]}"
        response = api_client.post("/api/auth/register", json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "123",
        })
        assert response.status_code in (400, 200)
        data = response.json()
        if response.status_code == 200:
            assert data["code"] != 200


class TestLogin:
    """POST /api/auth/login 登录接口测试。"""

    def test_login_success(self, api_client, registered_user):
        response = api_client.post("/api/auth/login", json={
            "username": registered_user["username"],
            "password": registered_user["password"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "token" in data["data"]
        assert len(data["data"]["token"]) > 20

    def test_login_wrong_password(self, api_client, registered_user):
        response = api_client.post("/api/auth/login", json={
            "username": registered_user["username"],
            "password": "WrongPassword123",
        })
        data = response.json()
        assert data["code"] != 200

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post("/api/auth/login", json={
            "username": f"nonexist_{uuid.uuid4().hex[:8]}",
            "password": "Test123456",
        })
        data = response.json()
        assert data["code"] != 200


class TestUserProfile:
    """GET/PUT /api/user/profile 用户资料接口测试。"""

    def test_get_profile_success(self, api_client, auth_headers):
        response = api_client.get("/api/user/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "username" in data["data"]

    def test_get_profile_no_token(self, api_client):
        response = api_client.get("/api/user/profile")
        assert response.status_code == 401

    def test_get_profile_invalid_token(self, api_client):
        response = api_client.get("/api/user/profile", headers={
            "Authorization": "Bearer invalid_token_here"
        })
        assert response.status_code == 401

    def test_update_profile(self, api_client, auth_headers):
        new_email = f"updated_{uuid.uuid4().hex[:8]}@test.com"
        response = api_client.put("/api/user/profile", headers=auth_headers, json={
            "email": new_email,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
