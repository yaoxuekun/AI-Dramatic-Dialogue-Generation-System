"""chat_agent_pkg/memory.py 单元测试。

测试关键事实合并逻辑。
"""
from chat_agent_pkg.memory import merge_key_facts


class TestMergeKeyFacts:
    """merge_key_facts 函数测试。"""

    def test_both_none(self):
        result = merge_key_facts(None, None)
        assert result == {}

    def test_existing_none(self):
        result = merge_key_facts(None, {"genre": "科幻"})
        assert result == {"genre": "科幻"}

    def test_info_none(self):
        result = merge_key_facts({"genre": "科幻"}, None)
        assert result == {"genre": "科幻"}

    def test_merge_no_overlap(self):
        result = merge_key_facts({"genre": "科幻"}, {"style": "国漫"})
        assert result == {"genre": "科幻", "style": "国漫"}

    def test_merge_with_overlap(self):
        result = merge_key_facts({"genre": "科幻"}, {"genre": "玄幻"})
        assert result == {"genre": "玄幻"}

    def test_skip_none_values(self):
        result = merge_key_facts({"genre": "科幻"}, {"genre": None, "style": "国漫"})
        assert result == {"genre": "科幻", "style": "国漫"}

    def test_skip_empty_string_values(self):
        result = merge_key_facts({"genre": "科幻"}, {"genre": "", "style": "国漫"})
        assert result == {"genre": "科幻", "style": "国漫"}

    def test_skip_whitespace_only_values(self):
        result = merge_key_facts({"genre": "科幻"}, {"genre": "   "})
        assert result == {"genre": "科幻"}

    def test_does_not_mutate_original(self):
        original = {"genre": "科幻"}
        merge_key_facts(original, {"style": "国漫"})
        assert original == {"genre": "科幻"}

    def test_empty_dicts(self):
        result = merge_key_facts({}, {})
        assert result == {}
