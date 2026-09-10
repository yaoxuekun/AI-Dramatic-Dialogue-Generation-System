"""聊天相关 API 接口测试。

测试会话创建、消息发送、历史查询、会话列表和删除等接口。
需要 Java 后端运行在 localhost:8085。
"""
import uuid


class TestChatSession:
    """聊天会话相关接口测试。"""

    def test_create_session(self, api_client, auth_headers):
        """POST /api/chat/start 创建会话。"""
        response = api_client.post("/api/chat/start", headers=auth_headers, json={
            "title": f"测试会话_{uuid.uuid4().hex[:6]}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "id" in data["data"]

    def test_create_session_no_token(self, api_client):
        """无 token 创建会话应返回 401。"""
        response = api_client.post("/api/chat/start", json={
            "title": "测试会话",
        })
        assert response.status_code == 401

    def test_list_sessions(self, api_client, auth_headers):
        """GET /api/chat/sessions 获取会话列表。"""
        response = api_client.get("/api/chat/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_send_message(self, api_client, auth_headers):
        """POST /api/chat/message 发送消息。"""
        # 先创建会话
        session_resp = api_client.post("/api/chat/start", headers=auth_headers, json={
            "title": f"消息测试_{uuid.uuid4().hex[:6]}",
        })
        session_id = session_resp.json()["data"]["id"]

        # 发送消息
        response = api_client.post("/api/chat/message", headers=auth_headers, json={
            "sessionId": session_id,
            "content": "你好，这是一条测试消息",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "content" in data["data"]

    def test_send_message_no_session(self, api_client, auth_headers):
        """发送消息到不存在的会话应返回错误。"""
        response = api_client.post("/api/chat/message", headers=auth_headers, json={
            "sessionId": 999999,
            "content": "测试消息",
        })
        data = response.json()
        assert data["code"] != 200

    def test_get_history(self, api_client, auth_headers):
        """GET /api/chat/history/{sessionId} 获取历史消息。"""
        # 先创建会话并发送消息
        session_resp = api_client.post("/api/chat/start", headers=auth_headers, json={
            "title": f"历史测试_{uuid.uuid4().hex[:6]}",
        })
        session_id = session_resp.json()["data"]["id"]

        api_client.post("/api/chat/message", headers=auth_headers, json={
            "sessionId": session_id,
            "content": "历史测试消息",
        })

        # 获取历史
        response = api_client.get(f"/api/chat/history/{session_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_delete_session(self, api_client, auth_headers):
        """DELETE /api/chat/session/{sessionId} 删除会话。"""
        # 先创建会话
        session_resp = api_client.post("/api/chat/start", headers=auth_headers, json={
            "title": f"删除测试_{uuid.uuid4().hex[:6]}",
        })
        session_id = session_resp.json()["data"]["id"]

        # 删除会话
        response = api_client.delete(f"/api/chat/session/{session_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_delete_nonexistent_session(self, api_client, auth_headers):
        """删除不存在的会话应返回错误或成功（软删除可能不报错）。"""
        response = api_client.delete("/api/chat/session/999999", headers=auth_headers)
        # 软删除实现可能对不存在的会话也返回 200
        assert response.status_code in (200, 404)
