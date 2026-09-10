"""story_ai_pkg/assets.py 单元测试。

测试资产 key 归一化、注册表构建和提示词构造。
"""
from story_ai_pkg.assets import (
    build_asset_registry,
    build_character_three_view_prompt,
    build_doubao_prompt,
    build_scene_concept_prompt,
    format_existing_asset_context,
    normalize_asset_key,
)
from story_ai_pkg.models import ExistingStoryAsset, SectionAssetItem


class TestNormalizeAssetKey:
    """normalize_asset_key 函数测试。"""

    def test_normal_case(self):
        assert normalize_asset_key("CHARACTER", "林澈") == "CHARACTER::林澈"

    def test_lowercase_type(self):
        assert normalize_asset_key("character", "林澈") == "CHARACTER::林澈"

    def test_mixed_case_name(self):
        assert normalize_asset_key("SCENE", "Test Scene") == "SCENE::test scene"

    def test_whitespace_trimmed(self):
        assert normalize_asset_key("  CHARACTER  ", "  林澈  ") == "CHARACTER::林澈"


class TestBuildAssetRegistry:
    """build_asset_registry 函数测试。"""

    def test_empty_list(self):
        assert build_asset_registry([]) == {}

    def test_single_asset(self):
        assets = [ExistingStoryAsset(assetType="CHARACTER", name="林澈", description="主角")]
        registry = build_asset_registry(assets)
        assert "CHARACTER::林澈" in registry
        assert registry["CHARACTER::林澈"].name == "林澈"
        assert registry["CHARACTER::林澈"].first_appearance is False

    def test_multiple_assets(self):
        assets = [
            ExistingStoryAsset(assetType="CHARACTER", name="林澈"),
            ExistingStoryAsset(assetType="SCENE", name="天文台"),
        ]
        registry = build_asset_registry(assets)
        assert len(registry) == 2

    def test_empty_name_skipped(self):
        assets = [
            ExistingStoryAsset(assetType="CHARACTER", name=""),
            ExistingStoryAsset(assetType="CHARACTER", name="林澈"),
        ]
        registry = build_asset_registry(assets)
        assert len(registry) == 1

    def test_duplicate_key_last_wins(self):
        assets = [
            ExistingStoryAsset(assetType="CHARACTER", name="林澈", description="旧"),
            ExistingStoryAsset(assetType="CHARACTER", name="林澈", description="新"),
        ]
        registry = build_asset_registry(assets)
        assert registry["CHARACTER::林澈"].description == "新"


class TestFormatExistingAssetContext:
    """format_existing_asset_context 函数测试。"""

    def test_empty_registry(self):
        assert format_existing_asset_context({}) == "暂无"

    def test_single_asset(self):
        registry = {
            "CHARACTER::林澈": SectionAssetItem(
                assetType="CHARACTER", name="林澈", description="主角",
                imagePrompt="短发少年", imagePath="path.png",
            )
        }
        result = format_existing_asset_context(registry)
        assert "林澈" in result
        assert "主角" in result

    def test_asset_with_none_fields(self):
        registry = {
            "CHARACTER::林澈": SectionAssetItem(
                assetType="CHARACTER", name="林澈",
            )
        }
        result = format_existing_asset_context(registry)
        assert "林澈" in result
        assert "无描述" in result


class TestBuildDoubaoPrompt:
    """build_doubao_prompt 函数测试。"""

    def test_character_type(self):
        result = build_doubao_prompt("星际迷航", "国漫", "CHARACTER", "林澈", "短发少年")
        assert "林澈" in result
        assert "三视图" in result

    def test_scene_type(self):
        result = build_doubao_prompt("星际迷航", "国漫", "SCENE", "天文台", "废弃天文台")
        assert "天文台" in result
        assert "环境概念图" in result

    def test_none_style_uses_default(self):
        result = build_doubao_prompt("星际迷航", None, "CHARACTER", "林澈", "短发少年")
        assert "高质量国漫" in result

    def test_empty_style_uses_default(self):
        result = build_doubao_prompt("星际迷航", "", "SCENE", "天文台", "废弃")
        assert "高质量国漫" in result


class TestBuildCharacterThreeViewPrompt:
    """build_character_three_view_prompt 函数测试。"""

    def test_contains_all_fields(self):
        result = build_character_three_view_prompt("星际迷航", "国漫", "林澈", "短发少年")
        assert "星际迷航" in result
        assert "国漫" in result
        assert "林澈" in result
        assert "短发少年" in result
        assert "三视图" in result

    def test_contains_style_requirement(self):
        result = build_character_three_view_prompt("书", "风格", "角色", "描述")
        assert "风格" in result


class TestBuildSceneConceptPrompt:
    """build_scene_concept_prompt 函数测试。"""

    def test_contains_all_fields(self):
        result = build_scene_concept_prompt("星际迷航", "国漫", "天文台", "废弃天文台")
        assert "星际迷航" in result
        assert "国漫" in result
        assert "天文台" in result
        assert "废弃天文台" in result
        assert "环境概念图" in result

    def test_not_character_prompt(self):
        result = build_scene_concept_prompt("书", "风格", "场景", "描述")
        assert "不要画成人物三视图" in result
