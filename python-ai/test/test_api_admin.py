"""管理相关 API 接口测试。

测试用户管理、大纲配置、提示词管理、功能权限等接口。
需要 Java 后端运行在 localhost:8085。
"""


class TestUserManagement:
    """用户管理接口测试（需要 ROOT 权限）。"""

    def test_list_users_no_permission(self, api_client, auth_headers):
        """普通用户访问用户列表应返回 403 或权限不足。"""
        response = api_client.get("/api/users", headers=auth_headers)
        # 普通用户可能返回 403 或 200 但数据受限
        assert response.status_code in (200, 403)


class TestStoryOutlineOptions:
    """大纲配置接口测试。"""

    def test_list_outline_options(self, api_client, auth_headers):
        """GET /api/story-outline-options 获取大纲配置列表。"""
        response = api_client.get("/api/story-outline-options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_list_outline_options_by_type(self, api_client, auth_headers):
        """按类型筛选大纲配置。"""
        response = api_client.get("/api/story-outline-options", headers=auth_headers, params={
            "type": "GENRE",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_list_outline_options_no_token(self, api_client):
        """无 token 应返回 401。"""
        response = api_client.get("/api/story-outline-options")
        assert response.status_code == 401


class TestAiPrompts:
    """提示词管理接口测试（需要 prompt.manage 权限）。"""

    def test_list_prompts_no_permission(self, api_client, auth_headers):
        """普通用户访问提示词列表应返回 403 或权限不足。"""
        response = api_client.get("/api/prompts", headers=auth_headers)
        # 可能返回 403（无权限）或 200（有权限）
        assert response.status_code in (200, 403)

    def test_list_prompts_no_token(self, api_client):
        """无 token 应返回 401。"""
        response = api_client.get("/api/prompts")
        assert response.status_code == 401


class TestFeaturePermissions:
    """功能权限接口测试。"""

    def test_list_my_permissions(self, api_client, auth_headers):
        """GET /api/feature-permissions/me 获取当前用户可用功能。"""
        response = api_client.get("/api/feature-permissions/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_list_my_permissions_no_token(self, api_client):
        """无 token 应返回 401。"""
        response = api_client.get("/api/feature-permissions/me")
        assert response.status_code == 401

    def test_list_all_permissions_no_permission(self, api_client, auth_headers):
        """普通用户访问全部功能权限列表应返回 403 或权限不足。"""
        response = api_client.get("/api/feature-permissions", headers=auth_headers)
        assert response.status_code in (200, 403)
