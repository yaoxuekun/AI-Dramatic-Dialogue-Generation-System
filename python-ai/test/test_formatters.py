"""story_ai_pkg/formatters.py 单元测试。

测试文本格式化、标签解析和 LLM 文本提取。
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from story_ai_pkg.formatters import (
    build_characters_text,
    extract_llm_text,
    extract_tagged_text,
    format_volume_outline_context,
    format_volume_section_context,
    parse_volume_section_text,
)
from story_ai_pkg.models import MainCharacterSetting, VolumeOutlineItem, VolumeSectionItem


class TestBuildCharactersText:
    """build_characters_text 函数测试。"""

    def test_empty_list(self):
        assert build_characters_text([]) == "No character settings were provided."

    def test_single_character(self):
        chars = [MainCharacterSetting(
            name="林澈", role="主角", description="少年", personality="勇敢"
        )]
        result = build_characters_text(chars)
        assert "林澈" in result
        assert "主角" in result

    def test_character_with_appearance(self):
        chars = [MainCharacterSetting(
            name="林澈", role="主角", description="少年", personality="勇敢",
            appearance={"hairstyle": "短发"}
        )]
        result = build_characters_text(chars)
        assert "短发" in result

    def test_character_with_none_fields(self):
        chars = [MainCharacterSetting(
            name="林澈", role="主角", description="少年", personality="勇敢"
        )]
        result = build_characters_text(chars)
        assert "appearance={}" in result or "appearance=None" in result

    def test_multiple_characters(self):
        chars = [
            MainCharacterSetting(name="林澈", role="主角", description="少年", personality="勇敢"),
            MainCharacterSetting(name="星野", role="搭档", description="少女", personality="冷静"),
        ]
        result = build_characters_text(chars)
        assert "林澈" in result
        assert "星野" in result
        assert "\n" in result


class TestFormatVolumeOutlineContext:
    """format_volume_outline_context 函数测试。"""

    def test_empty_list(self):
        assert format_volume_outline_context([]) == "暂无"

    def test_single_volume(self):
        volumes = [VolumeOutlineItem(
            volumeNumber=1, title="第一卷", summary="开篇",
            content="详细内容", endingHook="悬念"
        )]
        result = format_volume_outline_context(volumes)
        assert "第 1 卷" in result
        assert "第一卷" in result
        assert "悬念" in result

    def test_multiple_volumes(self):
        volumes = [
            VolumeOutlineItem(volumeNumber=1, title="卷一", summary="s1", content="c1", endingHook="h1"),
            VolumeOutlineItem(volumeNumber=2, title="卷二", summary="s2", content="c2", endingHook="h2"),
        ]
        result = format_volume_outline_context(volumes)
        assert "第 1 卷" in result
        assert "第 2 卷" in result
        assert "\n\n" in result


class TestFormatVolumeSectionContext:
    """format_volume_section_context 函数测试。"""

    def test_empty_list(self):
        assert format_volume_section_context([]) == "暂无"

    def test_single_section(self):
        sections = [VolumeSectionItem(
            sectionNumber=1, title="第一节", summary="开篇",
            content="故事内容", endingHook="钩子"
        )]
        result = format_volume_section_context(sections)
        assert "第 1 节" in result
        assert "钩子" in result


class TestExtractLlmText:
    """extract_llm_text 函数测试。"""

    def test_none(self):
        assert extract_llm_text(None) == ""

    def test_plain_string(self):
        assert extract_llm_text("hello") == "hello"

    def test_string_with_whitespace(self):
        assert extract_llm_text("  hello  ") == "hello"

    def test_object_with_content_string(self):
        obj = SimpleNamespace(content="hello world")
        assert extract_llm_text(obj) == "hello world"

    def test_object_with_content_list(self):
        obj = SimpleNamespace(content=["hello", " ", "world"])
        result = extract_llm_text(obj)
        assert "hello" in result
        assert "world" in result

    def test_list_of_strings(self):
        result = extract_llm_text(["hello", "world"])
        assert "hello" in result
        assert "world" in result

    def test_list_of_dicts(self):
        result = extract_llm_text([{"text": "hello"}, {"content": "world"}])
        assert "hello" in result
        assert "world" in result

    def test_empty_string(self):
        assert extract_llm_text("") == ""


class TestExtractTaggedText:
    """extract_tagged_text 函数测试。"""

    def test_present_tag(self):
        text = "<title>标题</title>"
        assert extract_tagged_text(text, "title") == "标题"

    def test_absent_tag(self):
        text = "<title>标题</title>"
        assert extract_tagged_text(text, "summary") == ""

    def test_multiline_content(self):
        text = "<content>第一行\n第二行\n第三行</content>"
        result = extract_tagged_text(text, "content")
        assert "第一行" in result
        assert "第三行" in result

    def test_case_insensitive(self):
        text = "<TITLE>标题</title>"
        assert extract_tagged_text(text, "title") == "标题"

    def test_multiple_same_tags_returns_first(self):
        text = "<title>第一个</title><title>第二个</title>"
        assert extract_tagged_text(text, "title") == "第一个"

    def test_surrounding_whitespace_trimmed(self):
        text = "<title>  标题  </title>"
        assert extract_tagged_text(text, "title") == "标题"

    def test_empty_tag(self):
        text = "<title></title>"
        assert extract_tagged_text(text, "title") == ""


class TestParseVolumeSectionText:
    """parse_volume_section_text 函数测试。"""

    def test_all_tags_present(self):
        text = (
            "<title>小节标题</title>\n"
            "<summary>小节摘要</summary>\n"
            "<content>详细内容</content>\n"
            "<endingHook>钩子</endingHook>"
        )
        result = parse_volume_section_text(text, 1)
        assert result.section_number == 1
        assert result.title == "小节标题"
        assert result.summary == "小节摘要"
        assert result.content == "详细内容"
        assert result.ending_hook == "钩子"

    def test_missing_title_uses_default(self):
        text = "<content>详细内容</content>"
        result = parse_volume_section_text(text, 3)
        assert result.title == "第 3 节"

    def test_missing_content_raises_502(self):
        text = "<title>标题</title><summary>摘要</summary>"
        with pytest.raises(HTTPException) as exc_info:
            parse_volume_section_text(text, 1)
        assert exc_info.value.status_code == 502

    def test_empty_content_raises_502(self):
        text = "<content></content>"
        with pytest.raises(HTTPException) as exc_info:
            parse_volume_section_text(text, 1)
        assert exc_info.value.status_code == 502

    def test_partial_tags(self):
        text = "<content>只有内容</content>"
        result = parse_volume_section_text(text, 2)
        assert result.content == "只有内容"
        assert result.summary == ""
        assert result.ending_hook == ""
