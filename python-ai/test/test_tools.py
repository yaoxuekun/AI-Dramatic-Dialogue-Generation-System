"""chat_agent_pkg/tools.py 单元测试。

测试 Tool 输入解析、参数归一化、空值判断和系统工具。
"""
import json

from chat_agent_pkg.tools import (
    ask_missing_info,
    deny_permission,
    get_tools_for_module,
    is_blank,
    normalize_args,
    parse_tool_input,
    to_json,
)


class TestToJson:
    """to_json 函数测试。"""

    def test_empty_dict(self):
        assert to_json({}) == "{}"

    def test_simple_dict(self):
        result = to_json({"a": 1})
        assert json.loads(result) == {"a": 1}

    def test_chinese_characters(self):
        result = to_json({"name": "林澈"})
        assert "林澈" in result

    def test_nested_dict(self):
        data = {"outer": {"inner": [1, 2, 3]}}
        assert json.loads(to_json(data)) == data


class TestParseToolInput:
    """parse_tool_input 函数测试。"""

    def test_empty_string(self):
        assert parse_tool_input("") == {}

    def test_none_like(self):
        assert parse_tool_input("") == {}

    def test_empty_json_object(self):
        assert parse_tool_input("{}") == {}

    def test_valid_json(self):
        result = parse_tool_input('{"storyId": 1}')
        assert result == {"storyId": 1}

    def test_already_dict(self):
        data = {"a": 1}
        assert parse_tool_input(data) == {"a": 1}

    def test_non_json_text(self):
        result = parse_tool_input("hello world")
        assert result == {"rawText": "hello world"}

    def test_json_array_returns_empty(self):
        # JSON array is not a dict, should return empty
        result = parse_tool_input("[1, 2, 3]")
        assert result == {}


class TestNormalizeArgs:
    """normalize_args 函数测试。"""

    def test_single_alias(self):
        data = {"id": 5}
        aliases = {"id": "storyId"}
        result = normalize_args(data, aliases)
        assert result["storyId"] == 5
        assert result["id"] == 5

    def test_alias_not_overwriting_existing(self):
        data = {"id": 5, "storyId": 10}
        aliases = {"id": "storyId"}
        result = normalize_args(data, aliases)
        assert result["storyId"] == 10

    def test_multiple_aliases(self):
        data = {"theme": "科幻", "storyStyle": "国漫"}
        aliases = {"theme": "genre", "storyStyle": "style"}
        result = normalize_args(data, aliases)
        assert result["genre"] == "科幻"
        assert result["style"] == "国漫"

    def test_no_aliases(self):
        data = {"a": 1, "b": 2}
        result = normalize_args(data, {})
        assert result == {"a": 1, "b": 2}

    def test_alias_source_not_present(self):
        data = {"other": 1}
        aliases = {"id": "storyId"}
        result = normalize_args(data, aliases)
        assert "storyId" not in result


class TestIsBlank:
    """is_blank 函数测试。"""

    def test_none(self):
        assert is_blank(None) is True

    def test_empty_string(self):
        assert is_blank("") is True

    def test_whitespace_only(self):
        assert is_blank("   ") is True

    def test_non_empty_string(self):
        assert is_blank("abc") is False

    def test_empty_list(self):
        assert is_blank([]) is True

    def test_non_empty_list(self):
        assert is_blank([1]) is False

    def test_zero_is_not_blank(self):
        assert is_blank(0) is False

    def test_false_is_not_blank(self):
        assert is_blank(False) is False


class TestAskMissingInfo:
    """ask_missing_info 函数测试。"""

    def test_basic_missing_info(self):
        result = json.loads(ask_missing_info('{"missingInfo": ["storyId"]}'))
        assert result["javaMethod"] == "story.none"
        assert "storyId" in result["missingInfo"]
        assert len(result["assistantMessage"]) > 0

    def test_custom_question(self):
        result = json.loads(ask_missing_info('{"missingInfo": ["genre"], "question": "请提供题材"}'))
        assert result["assistantMessage"] == "请提供题材"

    def test_empty_input(self):
        result = json.loads(ask_missing_info("{}"))
        assert result["javaMethod"] == "story.none"

    def test_string_missing_info(self):
        result = json.loads(ask_missing_info('{"missingInfo": "storyId"}'))
        assert "storyId" in result["missingInfo"]


class TestDenyPermission:
    """deny_permission 函数测试。"""

    def test_basic_deny(self):
        result = json.loads(deny_permission('{"requiredPermission": "ROOT"}'))
        assert result["javaMethod"] == "story.none"
        assert "ROOT" in result["assistantMessage"]

    def test_empty_input(self):
        result = json.loads(deny_permission("{}"))
        assert "更高权限" in result["assistantMessage"]

    def test_missing_permission_field(self):
        result = json.loads(deny_permission("{}"))
        assert result["javaMethod"] == "story.none"


class TestGetToolsForModule:
    """get_tools_for_module 函数测试。"""

    def test_manga_module_returns_tools(self):
        tools = get_tools_for_module("manga")
        names = [t.name for t in tools]
        assert "story_list" in names
        assert "story_generate_outline" in names
        assert "story_delete" in names

    def test_outline_config_module(self):
        tools = get_tools_for_module("outline_config")
        names = [t.name for t in tools]
        assert "outline_config_list" in names

    def test_prompt_management_module(self):
        tools = get_tools_for_module("prompt_management")
        names = [t.name for t in tools]
        assert "prompt_list" in names

    def test_user_permission_module(self):
        tools = get_tools_for_module("user_permission")
        names = [t.name for t in tools]
        assert "user_list" in names

    def test_unknown_module_returns_system_tools(self):
        tools = get_tools_for_module("unknown")
        names = [t.name for t in tools]
        assert "ask_missing_info" in names
        assert "deny_permission" in names

    def test_none_module_returns_system_tools(self):
        tools = get_tools_for_module(None)
        names = [t.name for t in tools]
        assert "ask_missing_info" in names

    def test_all_modules_include_system_tools(self):
        for module in ["manga", "outline_config", "prompt_management", "user_permission"]:
            tools = get_tools_for_module(module)
            names = [t.name for t in tools]
            assert "ask_missing_info" in names, f"{module} missing ask_missing_info"
            assert "deny_permission" in names, f"{module} missing deny_permission"

    def test_feature_permission_module(self):
        tools = get_tools_for_module("feature_permission")
        names = [t.name for t in tools]
        assert "feature_permission_list" in names
        assert "feature_permission_update" in names
