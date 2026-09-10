"""Pydantic 模型校验测试。

测试 story_ai_pkg 和 chat_agent_pkg 中的关键模型：构造、别名、默认值和约束。
"""
import pytest
from pydantic import ValidationError

from chat_agent_pkg.models import (
    ChatAgentRequest,
    ChatAgentResponse,
    ChatMemoryMessage,
    CoreferenceOutput,
    MemoryUpdateOutput,
    RouteOutput,
    SubAgentAction,
)
from story_ai_pkg.models import (
    MainCharacterSetting,
    NovelOutlineOutput,
    ScriptShotItem,
    SectionAssetExtractionItem,
    StoryOutlineGenerateRequest,
    VolumeCountOutput,
    VolumeOutlineItem,
    VolumeSectionCountOutput,
    VolumeSectionItem,
)


# ── story_ai_pkg 模型测试 ──────────────────────────────────────────


class TestMainCharacterSetting:
    def test_valid_construction(self):
        char = MainCharacterSetting(
            name="林澈", role="主角", description="少年", personality="勇敢"
        )
        assert char.name == "林澈"

    def test_appearance_optional(self):
        char = MainCharacterSetting(
            name="林澈", role="主角", description="少年", personality="勇敢"
        )
        assert char.appearance is None

    def test_with_appearance(self):
        char = MainCharacterSetting(
            name="林澈", role="主角", description="少年", personality="勇敢",
            appearance={"hairstyle": "短发"}
        )
        assert char.appearance["hairstyle"] == "短发"


class TestVolumeOutlineItem:
    def test_valid_construction(self):
        item = VolumeOutlineItem(
            volumeNumber=1, title="第一卷", summary="开篇",
            content="详细内容", endingHook="悬念"
        )
        assert item.volume_number == 1

    def test_alias_serialization(self):
        item = VolumeOutlineItem(
            volumeNumber=1, title="卷", summary="s", content="c", endingHook="h"
        )
        dumped = item.model_dump(by_alias=True)
        assert "volumeNumber" in dumped
        assert "endingHook" in dumped


class TestVolumeCountOutput:
    def test_valid_count(self):
        output = VolumeCountOutput(volume_count=8)
        assert output.volume_count == 8

    def test_too_low_raises(self):
        with pytest.raises(ValidationError):
            VolumeCountOutput(volume_count=4)

    def test_too_high_raises(self):
        with pytest.raises(ValidationError):
            VolumeCountOutput(volume_count=21)

    def test_boundary_values(self):
        assert VolumeCountOutput(volume_count=5).volume_count == 5
        assert VolumeCountOutput(volume_count=20).volume_count == 20


class TestVolumeSectionCountOutput:
    def test_valid_count(self):
        output = VolumeSectionCountOutput(section_count=6)
        assert output.section_count == 6

    def test_too_low_raises(self):
        with pytest.raises(ValidationError):
            VolumeSectionCountOutput(section_count=3)

    def test_too_high_raises(self):
        with pytest.raises(ValidationError):
            VolumeSectionCountOutput(section_count=13)


class TestScriptShotItem:
    def test_valid_construction(self):
        shot = ScriptShotItem(
            shotNumber=1, durationSeconds=5, shotType="近景",
            action="角色微笑", dialogue="你好"
        )
        assert shot.shot_number == 1

    def test_shot_number_must_be_positive(self):
        with pytest.raises(ValidationError):
            ScriptShotItem(shotNumber=0, durationSeconds=5, shotType="近景", action="动作")

    def test_duration_must_be_positive(self):
        with pytest.raises(ValidationError):
            ScriptShotItem(shotNumber=1, durationSeconds=0, shotType="近景", action="动作")

    def test_optional_fields(self):
        shot = ScriptShotItem(shotNumber=1, durationSeconds=5, shotType="近景", action="动作")
        assert shot.camera_movement is None
        assert shot.dialogue is None


class TestStoryOutlineGenerateRequest:
    def test_alias_construction(self):
        req = StoryOutlineGenerateRequest(userId=1, genre="科幻")
        assert req.user_id == 1
        assert req.genre == "科幻"

    def test_optional_fields(self):
        req = StoryOutlineGenerateRequest(userId=1, genre="科幻")
        assert req.story_style is None
        assert req.plot is None


class TestSectionAssetExtractionItem:
    def test_matched_existing_name_optional(self):
        item = SectionAssetExtractionItem(
            name="林澈", description="主角", imagePrompt="短发少年"
        )
        assert item.matched_existing_name is None

    def test_with_matched_name(self):
        item = SectionAssetExtractionItem(
            name="林澈", description="主角", imagePrompt="短发",
            matchedExistingName="林澈"
        )
        assert item.matched_existing_name == "林澈"


class TestNovelOutlineOutput:
    def test_valid_construction(self):
        output = NovelOutlineOutput(
            novel_name="星际迷航", story_summary="科幻故事",
            outline="完整大纲", main_characters=[]
        )
        assert output.novel_name == "星际迷航"

    def test_main_characters_required(self):
        output = NovelOutlineOutput(
            novel_name="书", story_summary="摘要", outline="大纲", main_characters=[]
        )
        assert output.main_characters == []

    def test_main_characters_missing_raises(self):
        with pytest.raises(ValidationError):
            NovelOutlineOutput(novel_name="书", story_summary="摘要", outline="大纲")


# ── chat_agent_pkg 模型测试 ──────────────────────────────────────────


class TestChatMemoryMessage:
    def test_valid_construction(self):
        msg = ChatMemoryMessage(role="user", content="你好")
        assert msg.role == "user"
        assert msg.created_at is None

    def test_populate_by_name(self):
        msg = ChatMemoryMessage(**{"role": "ai", "content": "你好", "createdAt": "2024-01-01"})
        assert msg.created_at == "2024-01-01"


class TestChatAgentRequest:
    def test_minimal_construction(self):
        req = ChatAgentRequest(userId=1, sessionId=1, userMessage="你好")
        assert req.user_id == 1
        assert req.story_id is None
        assert req.user_role == "USER"

    def test_alias_fields(self):
        req = ChatAgentRequest(
            userId=1, sessionId=1, userMessage="你好",
            storyId=5, storyStyle="国漫", userRole="ADMIN"
        )
        assert req.story_id == 5
        assert req.story_style == "国漫"
        assert req.user_role == "ADMIN"

    def test_default_collections(self):
        req = ChatAgentRequest(userId=1, sessionId=1, userMessage="你好")
        assert req.recent_messages == []
        assert req.key_facts == {}
        assert req.summary_candidate_messages == []


class TestCoreferenceOutput:
    def test_alias_construction(self):
        output = CoreferenceOutput(resolvedMessage="消解后消息")
        assert output.resolved_message == "消解后消息"

    def test_default_notes(self):
        output = CoreferenceOutput(resolvedMessage="消息")
        assert output.resolution_notes == ""


class TestRouteOutput:
    def test_default_permission(self):
        route = RouteOutput(module="manga", intent="test", route="no_action")
        assert route.required_permission == "USER"
        assert route.important_info == {}
        assert route.missing_info == []


class TestMemoryUpdateOutput:
    def test_defaults(self):
        output = MemoryUpdateOutput()
        assert output.long_term_memory == ""
        assert output.key_facts == {}


class TestSubAgentAction:
    def test_defaults(self):
        action = SubAgentAction()
        assert action.java_method == "story.none"
        assert action.java_method_args == {}
        assert action.missing_info == []


class TestChatAgentResponse:
    def test_populate_by_name(self):
        resp = ChatAgentResponse(
            rewrittenQuestion="重写",
            resolvedQuestion="消解",
            route="no_action",
            module="general",
            intent="chat",
            requiredPermission="USER",
            javaMethod="story.none",
            assistantMessage="回复",
        )
        assert resp.rewritten_question == "重写"
        assert resp.resolved_question == "消解"

    def test_default_collections(self):
        resp = ChatAgentResponse(
            rewrittenQuestion="q", resolvedQuestion="q",
            route="r", module="m", intent="i",
            requiredPermission="USER", javaMethod="story.none",
            assistantMessage="a",
        )
        assert resp.important_info == {}
        assert resp.missing_info == []
        assert resp.key_facts == {}
