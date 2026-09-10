"""漫剧相关 API 接口测试。

测试漫剧 CRUD、大纲生成/修改、分卷/小节等接口。
需要 Java 后端运行在 localhost:8085。
"""
import uuid


class TestStoryList:
    """GET /api/story/list 漫剧列表接口测试。"""

    def test_list_stories(self, api_client, auth_headers):
        response = api_client.get("/api/story/list", headers=auth_headers, params={
            "page": 1, "size": 10,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "records" in data["data"]

    def test_list_stories_no_token(self, api_client):
        response = api_client.get("/api/story/list")
        assert response.status_code == 401

    def test_list_stories_pagination(self, api_client, auth_headers):
        response = api_client.get("/api/story/list", headers=auth_headers, params={
            "page": 1, "size": 5,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["size"] == 5


class TestStoryGenerate:
    """POST /api/story/generate 生成剧情大纲接口测试。"""

    def test_generate_story(self, api_client, auth_headers):
        """生成剧情大纲（异步任务）。"""
        response = api_client.post("/api/story/generate", headers=auth_headers, json={
            "genre": "科幻",
            "style": "国漫电影感",
            "plot": "一个少年在末日世界中寻找希望",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "id" in data["data"]

    def test_generate_story_missing_genre(self, api_client, auth_headers):
        """缺少题材应返回校验错误。"""
        response = api_client.post("/api/story/generate", headers=auth_headers, json={
            "style": "国漫",
        })
        assert response.status_code in (400, 200)
        data = response.json()
        if response.status_code == 200:
            assert data["code"] != 200

    def test_generate_story_no_token(self, api_client):
        response = api_client.post("/api/story/generate", json={
            "genre": "科幻", "style": "国漫",
        })
        assert response.status_code == 401


class TestStoryDetail:
    """GET /api/story/{id} 漫剧详情接口测试。"""

    def test_get_story_detail(self, api_client, auth_headers):
        """获取已生成漫剧的详情。"""
        # 先生成一个漫剧
        gen_resp = api_client.post("/api/story/generate", headers=auth_headers, json={
            "genre": "奇幻", "style": "日系赛璐璐",
        })
        story_id = gen_resp.json()["data"]["id"]

        response = api_client.get(f"/api/story/{story_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == story_id

    def test_get_nonexistent_story(self, api_client, auth_headers):
        response = api_client.get("/api/story/999999", headers=auth_headers)
        data = response.json()
        assert data["code"] != 200


class TestStoryUpdate:
    """PUT /api/story/{id} 更新漫剧接口测试。"""

    def test_update_story(self, api_client, auth_headers):
        gen_resp = api_client.post("/api/story/generate", headers=auth_headers, json={
            "genre": "悬疑", "style": "黑白悬疑漫画",
        })
        story_id = gen_resp.json()["data"]["id"]

        response = api_client.put(f"/api/story/{story_id}", headers=auth_headers, json={
            "title": "新标题",
            "genre": "科幻",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200


class TestStoryDelete:
    """DELETE /api/story/{id} 删除漫剧接口测试。"""

    def test_delete_story(self, api_client, auth_headers):
        gen_resp = api_client.post("/api/story/generate", headers=auth_headers, json={
            "genre": "热血", "style": "复古港漫",
        })
        story_id = gen_resp.json()["data"]["id"]

        response = api_client.delete(f"/api/story/{story_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # 验证已删除
        get_resp = api_client.get(f"/api/story/{story_id}", headers=auth_headers)
        assert get_resp.json()["code"] != 200

    def test_delete_nonexistent_story(self, api_client, auth_headers):
        response = api_client.delete("/api/story/999999", headers=auth_headers)
        data = response.json()
        assert data["code"] != 200


class TestStoryDetailUpdate:
    """PUT /api/story/{id}/detail 手动保存大纲和角色测试。"""

    def test_update_story_detail(self, api_client, auth_headers):
        gen_resp = api_client.post("/api/story/generate", headers=auth_headers, json={
            "genre": "都市", "style": "水彩治愈系",
        })
        story_id = gen_resp.json()["data"]["id"]

        response = api_client.put(f"/api/story/{story_id}/detail", headers=auth_headers, json={
            "synopsis": "更新后的摘要",
            "fullContent": "更新后的大纲内容",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
