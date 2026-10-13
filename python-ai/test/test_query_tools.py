"""chat_agent_pkg/tools.py 真查询工具单元测试。

测试 make_query_tool 工厂、manga_tools 注入 user_id，以及
get_tools_for_module 的 user_id 传递逻辑。纯单元测试，无外部服务依赖。
"""
import json

import httpx
import pytest

from chat_agent_pkg.tools import (
    get_tools_for_module,
    make_query_tool,
    manga_tools,
    to_json,
)


class FakeResponse:
    """模拟 httpx.Response 的假响应对象。"""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=None, response=None
            )

    def json(self):
        return self._payload


class TestMangaTools:
    """manga_tools 注入 user_id 后的工具列表测试。"""

    def test_contains_query_tools(self):
        tools = manga_tools(user_id=42)
        names = [t.name for t in tools]
        assert "story_list_search" in names
        assert "story_detail_search" in names

    def test_query_tools_at_front(self):
        # 真查询工具应放在列表最前面（紧跟 system_tools 之后）
        tools = manga_tools(user_id=42)
        names = [t.name for t in tools]
        assert names[2] == "story_list_search"
        assert names[3] == "story_detail_search"

    def test_proposal_tools_still_present(self):
        tools = manga_tools(user_id=42)
        names = [t.name for t in tools]
        assert "story_list" in names
        assert "story_generate_outline" in names

    def test_without_user_id(self):
        # 无 user_id 时也应能构建工具列表
        tools = manga_tools()
        names = [t.name for t in tools]
        assert "story_list_search" in names


class TestMakeQueryToolRun:
    """make_query_tool 的 run() 行为测试（monkeypatch httpx.get）。"""

    def _capture(self, monkeypatch, payload=None, exc=None):
        captured = {}

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["url"] = url
            captured["params"] = params
            captured["headers"] = headers
            captured["timeout"] = timeout
            if exc is not None:
                raise exc
            return FakeResponse(payload if payload is not None else {"ok": True})

        monkeypatch.setattr(httpx, "get", fake_get)
        return captured

    def test_request_has_token_and_user_id(self, monkeypatch):
        captured = self._capture(monkeypatch)
        tool = make_query_tool("t", "d", "/internal/stories/search", user_id=42)
        tool.run("{}")

        assert captured["headers"]["X-Internal-Token"] is not None
        assert captured["params"]["user_id"] == 42

    def test_normal_response_returns_json(self, monkeypatch):
        data = [{"id": 1, "title": "科幻冒险"}]
        self._capture(monkeypatch, payload=data)
        tool = make_query_tool("t", "d", "/internal/stories/search", user_id=42)

        result = json.loads(tool.run("{}"))
        assert result == data

    def test_exception_returns_error_json(self, monkeypatch):
        self._capture(monkeypatch, exc=httpx.ConnectError("connection refused"))
        tool = make_query_tool("t", "d", "/internal/stories/search", user_id=42)

        result = json.loads(tool.run("{}"))
        assert "error" in result
        assert "connection refused" in result["error"]

    def test_missing_user_context(self):
        # user_id 未注入时直接返回错误 JSON，不发起请求
        tool = make_query_tool("t", "d", "/internal/stories/search", user_id=None)
        result = json.loads(tool.run("{}"))
        assert result == {"error": "user context missing"}

    def test_story_detail_path_concat(self, monkeypatch):
        # endpoint 以 / 结尾时，storyId 拼接到路径尾部且不进入 query 参数
        captured = self._capture(monkeypatch, payload={"id": 7})
        tool = make_query_tool("t", "d", "/internal/stories/", user_id=42)

        result = json.loads(tool.run('{"storyId": 7}'))
        assert captured["url"].endswith("/internal/stories/7")
        assert "storyId" not in captured["params"]
        assert result == {"id": 7}


class TestGetToolsForModuleWithUserId:
    """get_tools_for_module 的 user_id 传递测试。"""

    def test_with_user_id(self):
        tools = get_tools_for_module("manga", user_id=42)
        assert tools
        names = [t.name for t in tools]
        assert "story_list_search" in names
        assert "story_detail_search" in names

    def test_without_user_id(self):
        # 无 user_id 时不报错，查询工具 run 时返回错误 JSON
        tools = get_tools_for_module("manga")
        assert tools
        query_tool = next(t for t in tools if t.name == "story_list_search")
        result = json.loads(query_tool.run("{}"))
        assert result == {"error": "user context missing"}

    def test_other_factories_unchanged(self):
        # 其他模块工厂不接受 user_id，也应正常工作
        tools = get_tools_for_module("outline_config", user_id=42)
        names = [t.name for t in tools]
        assert "outline_config_list" in names
