from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# 请求模型
class StoryUpdateRequest(BaseModel):
    """更新漫剧请求"""

    title: Optional[str] = Field(None, max_length=200)
    genre: Optional[str] = Field(None, max_length=100)
    style: Optional[str] = Field(None, max_length=100)
    synopsis: Optional[str] = None


class StoryGenerateRequest(BaseModel):
    """创建漫剧请求"""

    session_id: int = Field(..., description="会话 ID")
    genre: str = Field(..., max_length=100, description="题材")
    style: str = Field(..., max_length=100, description="风格")
    plot: Optional[str] = Field(None, description="用户输入的剧情描述（可选）")


class OutlineReviseRequest(BaseModel):
    """剧情大纲修改"""

    suggestion: str = Field(..., min_length=1, description="修改建议")


class CharacterCrateRequest(BaseModel):
    """创建/更新角色请求"""

    name: str = Field(..., max_length=100, description="角色名称")
    role_position: Optional[str] = Field(
        None, max_length=100, description="角色定位（主角/配角/反派等）"
    )
    description: Optional[str] = Field(None, description="角色描述")
    personality: Optional[str] = Field(None, description="性格特征")
    appearance: Optional[str] = Field(None, description="外貌描述")


class StoryDetailUpdateRequest(BaseModel):
    """大纲和角色手动保存"""

    synopsis: Optional[str] = Field(None, description="故事摘要")
    full_content: Optional[str] = Field(None, description="完整剧情大纲")
    characters: Optional[List[CharacterCrateRequest]] = Field(
        None, description="角色列表"
    )


class VolumeOutlineItemRequest(BaseModel):
    """分卷大纲项（手动修改）"""

    volume_number: int = Field(..., ge=1, description="分卷编号")
    title: str = Field(..., max_length=200, description="分卷标题")
    summary: Optional[str] = Field(None, description="分卷摘要")
    content: Optional[str] = Field(None, description="分卷内容")
    ending_hook: Optional[str] = Field(None, description="结尾钩子")
    detailed_content: Optional[str] = Field(None, description="详细内容")


class VolumeOutlineUpdateRequest(BaseModel):
    """手动修改分卷大纲请求"""

    volume_outlines: List[VolumeOutlineItemRequest] = Field(
        ..., description="分卷大纲列表"
    )


# 响应模型
class CharacterResponse(BaseModel):
    """角色设定响应"""

    id: int
    story_id: int
    name: str
    role_position: Optional[str] = None  # 对应表中 role 字段
    description: Optional[str] = None
    personality: Optional[str] = None
    appearance: Optional[dict] = None  # 表中是 JSON 类型


class SectionScriptResponse(BaseModel):
    """分镜脚本响应"""

    id: int
    story_id: int
    section_id: int
    shot_number: int
    duration_seconds: int
    shot_type: str
    camera_movement: Optional[str] = None
    action: str
    dialogue: Optional[str] = None


class VolumeSectionResponse(BaseModel):
    """分卷小节响应"""

    id: int
    story_id: int
    volume_id: int
    section_number: int
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    ending_hook: Optional[str] = None
    scripts: List[SectionScriptResponse] = []


class VolumeOutlineResponse(BaseModel):
    """分卷大纲响应"""

    id: int
    story_id: int
    volume_number: int
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None  # 对应 content 字段
    ending_hook: Optional[str] = None
    detailed_content: Optional[str] = None
    sections: List[VolumeSectionResponse] = []


class AssetResponse(BaseModel):
    """资产响应"""

    id: int
    story_id: int
    asset_type: str
    name: str
    description: Optional[str] = None
    image_prompt: Optional[str] = None
    image_path: Optional[str] = None
    audio_path: Optional[str] = None


class StoryResponse(BaseModel):
    """漫剧简要响应（列表用）"""

    id: int
    user_id: int
    title: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    synopsis: Optional[str] = None
    cover_image_path: Optional[str] = None
    status: str
    view_count: int = 0
    like_count: int = 0
    updated_at: Any
    created_at: Any


class StoryDetailResponse(BaseModel):
    """漫剧详情响应（含所有关联数据）"""

    id: int
    user_id: int
    title: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    synopsis: Optional[str] = None
    full_content: Optional[str] = None
    cover_image_path: Optional[str] = None
    status: str
    view_count: int = 0
    like_count: int = 0
    created_at: Any
    updated_at: Any
    characters: List[CharacterResponse] = []
    volume_outlines: List[VolumeOutlineResponse] = []
    assets: List[AssetResponse] = []


class StoryListResponse(BaseModel):
    """漫剧列表分页响应（MyBatis-Plus 风格）"""

    records: List[StoryResponse]
    current: int
    size: int
    total: int
    pages: int
