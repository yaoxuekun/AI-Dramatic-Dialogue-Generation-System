"""chat_agent_pkg/routing.py 单元测试。

测试消息格式化、功能权限路由归一化和兜底响应。
"""
import json

from chat_agent_pkg.models import ChatAgentRequest, RouteOutput
from chat_agent_pkg.routing import (
    fallback_general_response,
    format_messages,
    normalize_feature_permission_route,
    normalize_important_info,
)


class TestFormatMessages:
    """format_messages 函数测试。"""

    def test_empty_list(self):
        assert format_messages([]) == "无"

    def test_none(self):
        assert format_messages(None) == "无"

    def test_single_message(self):
        class Msg:
            role = "user"
            content = "你好"
        result = format_messages([Msg()])
        assert result == "user: 你好"

    def test_multiple_messages(self):
        class Msg:
            def __init__(self, role, content):
                self.role = role
                self.content = content
        messages = [Msg("user", "你好"), Msg("ai", "你好！")]
        result = format_messages(messages)
        assert "user: 你好" in result
        assert "ai: 你好！" in result
        assert "\n" in result


class TestNormalizeFeaturePermissionRoute:
    """normalize_feature_permission_route 函数测试。"""

    def _make_route(self, module="general", intent="general_chat", route="no_action"):
        return RouteOutput(
            module=module,
            intent=intent,
            route=route,
            requiredPermission="USER",
            importantInfo={},
            missingInfo=[],
            assistantMessage="",
        )

    def test_explicit_feature_permission_keyword(self):
        route = self._make_route()
        result = normalize_feature_permission_route(route, "帮我查看功能权限")
        assert result.module == "feature_permission"
        assert result.required_permission == "ROOT"

    def test_english_keyword(self):
        route = self._make_route()
        result = normalize_feature_permission_route(route, "show featurePermission settings")
        assert result.module == "feature_permission"

    def test_combined_keywords(self):
        route = self._make_route()
        result = normalize_feature_permission_route(route, "禁止对话功能的权限")
        assert result.module == "feature_permission"

    def test_no_match_keeps_original(self):
        route = self._make_route(module="manga")
        result = normalize_feature_permission_route(route, "帮我生成剧情大纲")
        assert result.module == "manga"

    def test_already_feature_permission_unchanged(self):
        route = self._make_route(module="feature_permission")
        result = normalize_feature_permission_route(route, "查看功能权限")
        assert result.module == "feature_permission"

    def test_intent_updated_when_general(self):
        route = self._make_route(intent="general_chat")
        result = normalize_feature_permission_route(route, "功能权限管理")
        assert result.intent == "feature_permission_manage"

    def test_intent_not_overwritten(self):
        route = self._make_route(intent="existing_intent")
        result = normalize_feature_permission_route(route, "功能权限管理")
        assert result.intent == "existing_intent"


class TestNormalizeImportantInfo:
    """normalize_important_info 函数测试。"""

    def test_empty_info(self):
        route = RouteOutput(
            module="manga", intent="test", route="no_action",
            requiredPermission="USER", importantInfo={}, missingInfo=[], assistantMessage="",
        )
        result = normalize_important_info(route)
        assert json.loads(result) == {}

    def test_populated_info(self):
        route = RouteOutput(
            module="manga", intent="test", route="no_action",
            requiredPermission="USER",
            importantInfo={"storyId": 1, "genre": "科幻"},
            missingInfo=[], assistantMessage="",
        )
        result = normalize_important_info(route)
        parsed = json.loads(result)
        assert parsed["storyId"] == 1
        assert parsed["genre"] == "科幻"


class TestFallbackGeneralResponse:
    """fallback_general_response 函数测试。"""

    def test_returns_general_module(self):
        request = ChatAgentRequest(userId=1, sessionId=1, userMessage="你好")
        result = fallback_general_response(request, "你好")
        assert result.module == "general"
        assert result.intent == "general_chat"
        assert result.route == "no_action"
        assert result.required_permission == "USER"

    def test_assistant_message_contains_resolved(self):
        request = ChatAgentRequest(userId=1, sessionId=1, userMessage="测试")
        result = fallback_general_response(request, "测试消息")
        assert "测试消息" in result.assistant_message

    def test_empty_important_info(self):
        request = ChatAgentRequest(userId=1, sessionId=1, userMessage="测试")
        result = fallback_general_response(request, "测试")
        assert result.important_info == {}
        assert result.missing_info == []
