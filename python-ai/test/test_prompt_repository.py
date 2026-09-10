"""story_ai_pkg/prompt_repository.py 单元测试。

测试缓存 key 构建、值归一化和 JDBC URL 解析。
"""
from story_ai_pkg.prompt_repository import (
    _parse_jdbc_url,
    build_prompt_cache_key,
    normalize_optional_match_value,
)


class TestBuildPromptCacheKey:
    """build_prompt_cache_key 函数测试。"""

    def test_all_present(self):
        result = build_prompt_cache_key("generate_story_outline", "科幻", "国漫")
        assert result == "generate_story_outline|科幻|国漫"

    def test_none_genre(self):
        result = build_prompt_cache_key("generate_story_outline", None, "国漫")
        assert result == "generate_story_outline||国漫"

    def test_none_style(self):
        result = build_prompt_cache_key("generate_story_outline", "科幻", None)
        assert result == "generate_story_outline|科幻|"

    def test_both_none(self):
        result = build_prompt_cache_key("generate_story_outline", None, None)
        assert result == "generate_story_outline||"

    def test_empty_strings_treated_as_none(self):
        result = build_prompt_cache_key("key", "", "")
        assert result == "key||"


class TestNormalizeOptionalMatchValue:
    """normalize_optional_match_value 函数测试。"""

    def test_none(self):
        assert normalize_optional_match_value(None) is None

    def test_empty_string(self):
        assert normalize_optional_match_value("") is None

    def test_whitespace_only(self):
        assert normalize_optional_match_value("   ") is None

    def test_normal_value(self):
        assert normalize_optional_match_value("科幻") == "科幻"

    def test_whitespace_trimmed(self):
        assert normalize_optional_match_value("  科幻  ") == "科幻"

    def test_english_value(self):
        assert normalize_optional_match_value("sci-fi") == "sci-fi"


class TestParseJdbcUrl:
    """_parse_jdbc_url 函数测试。"""

    def test_full_url(self):
        host, port, db = _parse_jdbc_url("jdbc:mysql://localhost:3306/springcloud?useSSL=false")
        assert host == "localhost"
        assert port == 3306
        assert db == "springcloud"

    def test_url_without_port(self):
        host, port, db = _parse_jdbc_url("jdbc:mysql://localhost/springcloud")
        assert host == "localhost"
        assert port == 3306  # default
        assert db == "springcloud"

    def test_custom_port(self):
        host, port, db = _parse_jdbc_url("jdbc:mysql://db.example.com:3307/mydb")
        assert host == "db.example.com"
        assert port == 3307
        assert db == "mydb"

    def test_empty_string(self):
        host, port, db = _parse_jdbc_url("")
        assert host is None
        assert port is None
        assert db is None

    def test_invalid_url(self):
        host, port, db = _parse_jdbc_url("not-a-jdbc-url")
        assert host is None

    def test_url_with_params(self):
        host, port, db = _parse_jdbc_url("jdbc:mysql://localhost:3306/springcloud?useSSL=false&serverTimezone=UTC")
        assert host == "localhost"
        assert port == 3306
        assert db == "springcloud"
