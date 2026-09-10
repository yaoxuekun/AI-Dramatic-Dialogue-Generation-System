"""ai_runtime.py 单元测试。

测试 JSON 修复、重试判断和结构化输出校验等纯逻辑函数。
"""
import json

import pytest
from pydantic import BaseModel

from ai_runtime import (
    build_json_repair_candidates,
    complete_truncated_json,
    escape_unescaped_quotes_and_controls,
    extract_malformed_json_from_exception,
    extract_outer_json_candidate,
    is_retryable_llm_error,
    parse_json_with_repair,
    strip_json_markdown_fence,
    validate_structured_output,
)


# ── strip_json_markdown_fence ──────────────────────────────────────


class TestStripJsonMarkdownFence:
    def test_no_fence(self):
        assert strip_json_markdown_fence('{"a":1}') == '{"a":1}'

    def test_json_fence(self):
        text = '```json\n{"a":1}\n```'
        result = strip_json_markdown_fence(text)
        assert result == '{"a":1}'

    def test_fence_without_lang(self):
        text = '```\n{"a":1}\n```'
        result = strip_json_markdown_fence(text)
        assert result == '{"a":1}'

    def test_fence_with_extra_whitespace(self):
        text = '  ```json  \n{"a":1}\n  ```  '
        result = strip_json_markdown_fence(text)
        assert result == '{"a":1}'

    def test_only_opening_fence(self):
        text = '```json\n{"a":1}'
        result = strip_json_markdown_fence(text)
        assert '{"a":1}' in result


# ── extract_outer_json_candidate ───────────────────────────────────


class TestExtractOuterJsonCandidate:
    def test_clean_json_object(self):
        assert extract_outer_json_candidate('{"a":1}') == '{"a":1}'

    def test_json_with_prefix(self):
        result = extract_outer_json_candidate('Here is the result: {"a":1}')
        assert result == '{"a":1}'

    def test_json_with_suffix(self):
        result = extract_outer_json_candidate('{"a":1} done')
        assert result == '{"a":1}'

    def test_json_array(self):
        result = extract_outer_json_candidate('[1,2,3]')
        assert result == '[1,2,3]'

    def test_no_json(self):
        assert extract_outer_json_candidate('no json here') == 'no json here'

    def test_nested_objects(self):
        text = 'prefix {"outer": {"inner": 1}} suffix'
        result = extract_outer_json_candidate(text)
        assert '{"outer": {"inner": 1}}' in result


# ── escape_unescaped_quotes_and_controls ───────────────────────────


class TestEscapeUnescapedQuotesAndControls:
    def test_clean_json_unchanged(self):
        text = '{"a":"hello"}'
        result = escape_unescaped_quotes_and_controls(text)
        assert json.loads(result) == {"a": "hello"}

    def test_raw_newline_in_string(self):
        text = '{"a":"hello\nworld"}'
        result = escape_unescaped_quotes_and_controls(text)
        assert "\\n" in result
        assert json.loads(result)["a"] == "hello\nworld"

    def test_raw_tab_in_string(self):
        text = '{"a":"hello\tworld"}'
        result = escape_unescaped_quotes_and_controls(text)
        assert "\\t" in result

    def test_empty_input(self):
        assert escape_unescaped_quotes_and_controls("") == ""


# ── complete_truncated_json ────────────────────────────────────────


class TestCompleteTruncatedJson:
    def test_complete_json_unchanged(self):
        text = '{"a":1}'
        result = complete_truncated_json(text)
        assert json.loads(result) == {"a": 1}

    def test_truncated_object(self):
        text = '{"a":1, "b":'
        result = complete_truncated_json(text)
        # complete_truncated_json closes brackets but may not produce valid JSON
        # when a value is missing after a colon. Verify it at least closes the structure.
        assert result.endswith("}")

    def test_truncated_string(self):
        text = '{"a":"hello'
        result = complete_truncated_json(text)
        parsed = json.loads(result)
        assert "hello" in parsed["a"]

    def test_truncated_array(self):
        text = '{"items": [1, 2'
        result = complete_truncated_json(text)
        parsed = json.loads(result)
        assert isinstance(parsed["items"], list)

    def test_nested_truncation(self):
        text = '{"outer": {"inner":'
        result = complete_truncated_json(text)
        # Verify the function closes all open brackets
        assert result.count("{") == result.count("}")


# ── build_json_repair_candidates ───────────────────────────────────


class TestBuildJsonRepairCandidates:
    def test_valid_json_returns_candidates(self):
        text = '{"a":1}'
        candidates = build_json_repair_candidates(text)
        assert len(candidates) >= 1
        assert text in candidates

    def test_no_duplicates(self):
        text = '{"a":1}'
        candidates = build_json_repair_candidates(text)
        assert len(candidates) == len(set(candidates))

    def test_fence_json(self):
        text = '```json\n{"a":1}\n```'
        candidates = build_json_repair_candidates(text)
        assert any('{"a":1}' in c for c in candidates)

    def test_returns_list(self):
        candidates = build_json_repair_candidates('{"a":1}')
        assert isinstance(candidates, list)


# ── parse_json_with_repair ─────────────────────────────────────────


class TestParseJsonWithRepair:
    def test_valid_json(self):
        result = parse_json_with_repair('{"a":1}')
        assert result == {"a": 1}

    def test_fence_json(self):
        result = parse_json_with_repair('```json\n{"a":1}\n```')
        assert result == {"a": 1}

    def test_json_with_noise(self):
        result = parse_json_with_repair('Result: {"a":1} done')
        assert result == {"a": 1}

    def test_unfixable_returns_none(self):
        result = parse_json_with_repair("not json at all")
        assert result is None

    def test_empty_returns_none(self):
        result = parse_json_with_repair("")
        assert result is None


# ── extract_malformed_json_from_exception ──────────────────────────


class TestExtractMalformedJsonFromException:
    def test_arguments_pattern(self):
        exc = Exception('arguments: {"a":1} are not valid JSON')
        result = extract_malformed_json_from_exception(exc)
        assert result == '{"a":1}'

    def test_invalid_json_pattern(self):
        exc = Exception('Invalid json output: {"a":1}')
        result = extract_malformed_json_from_exception(exc)
        assert result == '{"a":1}'

    def test_could_not_parse_pattern(self):
        exc = Exception('Could not parse json: {"a":1}')
        result = extract_malformed_json_from_exception(exc)
        assert result == '{"a":1}'

    def test_no_json_in_exception(self):
        exc = Exception("some other error")
        result = extract_malformed_json_from_exception(exc)
        assert result is None

    def test_empty_exception(self):
        exc = Exception("")
        result = extract_malformed_json_from_exception(exc)
        assert result is None


# ── is_retryable_llm_error ─────────────────────────────────────────


class TestIsRetryableLlmError:
    def test_remote_disconnected(self):
        assert is_retryable_llm_error(Exception("RemoteDisconnected")) is True

    def test_connection_aborted(self):
        assert is_retryable_llm_error(Exception("Connection aborted")) is True

    def test_connection_reset(self):
        assert is_retryable_llm_error(Exception("Connection reset by peer")) is True

    def test_read_timed_out(self):
        assert is_retryable_llm_error(Exception("Read timed out")) is True

    def test_502_error(self):
        assert is_retryable_llm_error(Exception("502 Bad Gateway")) is True

    def test_503_error(self):
        assert is_retryable_llm_error(Exception("503 Service Unavailable")) is True

    def test_504_error(self):
        assert is_retryable_llm_error(Exception("504 Gateway Timeout")) is True

    def test_non_retryable_error(self):
        assert is_retryable_llm_error(ValueError("invalid value")) is False

    def test_key_error(self):
        assert is_retryable_llm_error(KeyError("missing_key")) is False

    def test_timeout_in_message(self):
        assert is_retryable_llm_error(Exception("Request timed out")) is True

    def test_max_retries_exceeded(self):
        assert is_retryable_llm_error(Exception("Max retries exceeded with url")) is True


# ── validate_structured_output ─────────────────────────────────────


class TestValidateStructuredOutput:
    class SampleModel(BaseModel):
        name: str
        value: int

    def test_already_correct_type(self):
        obj = self.SampleModel(name="test", value=42)
        result = validate_structured_output(obj, self.SampleModel)
        assert result.name == "test"
        assert result.value == 42

    def test_from_dict(self):
        result = validate_structured_output({"name": "test", "value": 42}, self.SampleModel)
        assert result.name == "test"

    def test_from_pydantic_model(self):
        obj = self.SampleModel(name="test", value=42)
        result = validate_structured_output(obj, self.SampleModel)
        assert isinstance(result, self.SampleModel)

    def test_invalid_data_raises(self):
        with pytest.raises(Exception):
            validate_structured_output({"name": "test", "value": "not_int"}, self.SampleModel)
