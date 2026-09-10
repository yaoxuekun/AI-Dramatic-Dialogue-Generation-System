"""chat_agent_pkg/sub_agents.py 单元测试。

测试 JSON 提取和子 Agent 输出解析。
"""
import json

from chat_agent_pkg.models import RouteOutput, SubAgentAction
from chat_agent_pkg.sub_agents import extract_json_object, parse_sub_agent_output


class TestExtractJsonObject:
    """extract_json_object 函数测试。"""

    def test_clean_json(self):
        result = extract_json_object('{"javaMethod": "story.list"}')
        assert result == {"javaMethod": "story.list"}

    def test_json_with_surrounding_text(self):
        text = 'Here is the result: {"javaMethod": "story.list"} done.'
        result = extract_json_object(text)
        assert result == {"javaMethod": "story.list"}

    def test_empty_string(self):
        assert extract_json_object("") is None

    def test_none_equivalent(self):
        assert extract_json_object("") is None

    def test_no_json(self):
        assert extract_json_object("no json here") is None

    def test_json_array(self):
        # extract_json_object only returns dicts
        result = extract_json_object("[1, 2, 3]")
        assert result is None

    def test_malformed_json(self):
        result = extract_json_object("{invalid json}")
        assert result is None

    def test_nested_json(self):
        data = {"args": {"storyId": 1}, "method": "story.detail"}
        text = f"Result: {json.dumps(data)}"
        result = extract_json_object(text)
        assert result == data

    def test_json_with_newlines(self):
        text = '{\n  "javaMethod": "story.list",\n  "args": {}\n}'
        result = extract_json_object(text)
        assert result["javaMethod"] == "story.list"


class TestParseSubAgentOutput:
    """parse_sub_agent_output 函数测试。"""

    def _make_route(self, assistant_message="默认回复"):
        return RouteOutput(
            module="manga",
            intent="story_generate",
            route="generate",
            requiredPermission="USER",
            importantInfo={},
            missingInfo=[],
            assistantMessage=assistant_message,
        )

    def test_valid_json_output(self):
        output = json.dumps({
            "javaMethod": "story.generate",
            "javaMethodArgs": {"genre": "科幻"},
            "assistantMessage": "好的",
        })
        result = parse_sub_agent_output(output, self._make_route())
        assert result.java_method == "story.generate"
        assert result.java_method_args == {"genre": "科幻"}
        assert result.assistant_message == "好的"

    def test_snake_case_keys(self):
        output = json.dumps({
            "java_method": "story.list",
            "java_method_args": {"page": 1},
            "assistant_message": "列表",
        })
        result = parse_sub_agent_output(output, self._make_route())
        assert result.java_method == "story.list"

    def test_empty_output_fallback(self):
        route = self._make_route("兜底回复")
        result = parse_sub_agent_output("", route)
        assert result.java_method == "story.none"
        assert result.assistant_message == "兜底回复"

    def test_no_json_fallback(self):
        route = self._make_route("兜底回复")
        result = parse_sub_agent_output("no json here", route)
        assert result.java_method == "story.none"

    def test_missing_java_method_defaults(self):
        output = '{"assistantMessage": "测试"}'
        result = parse_sub_agent_output(output, self._make_route())
        assert result.java_method == "story.none"

    def test_missing_assistant_message_uses_route(self):
        output = '{"javaMethod": "story.list"}'
        route = self._make_route("路由回复")
        result = parse_sub_agent_output(output, route)
        assert result.assistant_message == "路由回复"

    def test_missing_info_field(self):
        output = '{"javaMethod": "story.none", "missingInfo": ["storyId"]}'
        result = parse_sub_agent_output(output, self._make_route())
        assert result.missing_info == ["storyId"]
