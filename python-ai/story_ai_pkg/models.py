# 数据模型定义模块
# 本文件定义所有 Pydantic 数据模型，分为三类：
# 1. 请求模型（Request）：Java 端通过 RabbitMQ 或 HTTP 传入的参数
# 2. 响应模型（Response）：返回给 Java 端的结果
# 3. 输出模型（Output）：大模型结构化输出的约束模型，通过 with_structured_output 绑定

# Pydantic：数据验证和序列化库，FastAPI 的核心依赖
from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════
# 基础模型：被多个请求/响应模型复用的公共结构
# ══════════════════════════════════════════════════════════════════════


class MainCharacterSetting(BaseModel):
    """主要角色设定模型。

    描述一个核心角色的基本信息，用于剧情大纲、分卷大纲和修改链路。
    在大纲生成时由大模型返回，在大纲修改时作为上下文传入。
    """

    # 角色姓名或代号
    name: str = Field(description="Character name or codename")

    # 角色定位：如主角、搭档、反派、导师、幕后黑手
    role: str = Field(description="Character role, such as protagonist, partner, antagonist, mentor, or hidden manipulator")

    # 角色背景、能力和叙事功能
    description: str = Field(description="Character background, ability, and narrative function")

    # 性格、核心欲望、弱点或人物弧光
    personality: str = Field(description="Personality, core desire, weakness, or character arc")

    # 可选的外观特征，如发型、服装、标志性道具
    appearance: dict[str, str] | None = Field(
        default=None,
        description="Optional appearance traits, such as hairstyle, clothing, or signature item",
    )


class VolumeOutlineItem(BaseModel):
    """单卷大纲条目模型。

    描述一卷的核心信息：卷号、标题、摘要、详细大纲内容和卷末悬念钩子。
    用于分卷大纲生成、修改和小节生成的输入输出。
    """

    # 卷号，从 1 开始
    volume_number: int = Field(alias="volumeNumber", description="Volume number, starting from 1")

    # 卷标题
    title: str = Field(description="Volume title")

    # 卷摘要，简短概括本卷内容
    summary: str = Field(description="Short summary of this volume")

    # 详细大纲内容，包含丰富的情节点、冲突、反转和情绪钩子
    content: str = Field(description="Detailed volume outline with rich plot beats, conflicts, reversals, choices, and emotional hooks")

    # 卷末悬念钩子，让读者迫不及待点开下一卷
    ending_hook: str = Field(alias="endingHook", description="The cliffhanger or hook at the end of this volume")


class ExistingStoryAsset(BaseModel):
    """已有故事资产引用模型。

    Java 端传入的故事已有资产列表，用于判断人物/场景是否第一次出现。
    如果是首次出现，需要调用豆包生成图片；否则复用已有图片。
    """

    # 资产类型：CHARACTER（人物）或 SCENE（场景）
    asset_type: str = Field(alias="assetType")

    # 资产名称，用于查重匹配
    name: str

    # 资产描述，用于 LLM 识别时的上下文
    description: str | None = None

    # 图片生成提示词，用于豆包生成图片
    image_prompt: str | None = Field(default=None, alias="imagePrompt")

    # 本地图片相对路径，如 generated-assets/2026-05-22/xxx.png
    image_path: str | None = Field(default=None, alias="imagePath")

    # 人物音频相对路径，用于角色配音
    audio_path: str | None = Field(default=None, alias="audioPath")


class SectionAssetItem(BaseModel):
    """当前小节的人物或场景资产模型。

    描述小节中出现的单个人物或场景，包含图片路径和是否首次出现的标记。
    用于小节资产生成的输出和故事详情接口的返回。
    """

    # 资产类型：CHARACTER 或 SCENE
    asset_type: str = Field(alias="assetType", description="CHARACTER or SCENE")

    # 资产名称
    name: str

    # 资产描述
    description: str | None = None

    # 图片生成提示词
    image_prompt: str | None = Field(default=None, alias="imagePrompt")

    # 本地图片相对路径
    image_path: str | None = Field(default=None, alias="imagePath")

    # 人物音频相对路径
    audio_path: str | None = Field(default=None, alias="audioPath")

    # 是否为首次出现（首次出现时标记为 True）
    first_appearance: bool = Field(default=False, alias="firstAppearance")

    # 图片生成失败时的错误信息
    generation_error: str | None = Field(default=None, alias="generationError")


class VolumeSectionItem(BaseModel):
    """单个分卷小节故事细节模型。

    描述一卷中的一个小节的具体故事内容，包含场景、动作、对话、冲突和情绪。
    用于小节生成的输出和分镜脚本生成的输入。
    """

    # 小节号，从 1 开始
    section_number: int = Field(alias="sectionNumber", description="Section number, starting from 1")

    # 小节标题
    title: str = Field(description="Section title")

    # 小节摘要
    summary: str = Field(description="Short summary of this section")

    # 详细故事细节，包含场景、动作、对话、冲突和情绪
    content: str = Field(description="Detailed story beats for this section, including scene, action, dialogue, conflict, and emotion")

    # 小节钩子，引出下一节的悬念或压力
    ending_hook: str = Field(alias="endingHook", description="Hook or pressure that leads into the next section")

    # 本节出现的人物和场景资产列表
    assets: list[SectionAssetItem] = Field(default_factory=list, description="Characters and scenes that appear in this section")


class ScriptShotItem(BaseModel):
    """单个分镜脚本条目模型。

    描述一个镜头的详细信息，包含镜头号、时长、景别、运镜、动作和对白。
    用于分镜脚本生成的输出。
    """

    # 镜头号，从 1 开始
    shot_number: int = Field(alias="shotNumber", ge=1, description="Shot number, starting from 1")

    # 镜头时长（秒）
    duration_seconds: int = Field(alias="durationSeconds", ge=1, description="Duration of this shot in seconds")

    # 景别：全景、近景、特写、推拉、摇移等
    shot_type: str = Field(alias="shotType", description="Shot type, such as 全景, 近景, 特写, 推拉, 摇移")

    # 运镜方式，可选
    camera_movement: str | None = Field(default=None, alias="cameraMovement", description="Camera movement for this shot")

    # 可见的动作、情绪、场景变化和导演指示
    action: str = Field(description="Visible action, emotion, scene change, and cinematic direction")

    # 角色对白，无对白时为空
    dialogue: str | None = Field(default=None, description="Spoken dialogue in this shot, empty when no dialogue")


# ══════════════════════════════════════════════════════════════════════
# 请求模型：Java 端传入的参数
# ══════════════════════════════════════════════════════════════════════


class StoryOutlineGenerateRequest(BaseModel):
    """剧情大纲生成请求体。

    对应 Java 端 RabbitMQ 故事生成任务的入参。
    包含用户 ID、题材、用户设定风格和可选剧情。
    """

    # 用户 ID
    user_id: int = Field(alias="userId")

    # 题材，如科幻、玄幻、都市、悬疑
    genre: str

    # 用户设定的漫剧视觉风格，可选
    story_style: str | None = Field(default=None, alias="storyStyle")

    # 用户提供的大致剧情，可选
    plot: str | None = None


class StoryOutlineReviseRequest(BaseModel):
    """剧情大纲修改请求体。

    对应 Java 端 RabbitMQ 故事大纲修改任务的入参。
    包含原始故事信息和用户的修改意见。
    """

    # 用户 ID
    user_id: int = Field(alias="userId")

    # 故事 ID
    story_id: int = Field(alias="storyId")

    # 故事标题
    title: str

    # 题材，如科幻、玄幻、都市、悬疑
    genre: str | None = None

    # 用户设定的漫剧视觉风格，可选
    story_style: str | None = Field(default=None, alias="storyStyle")

    # 故事摘要，可选
    synopsis: str | None = None

    # 原始剧情大纲
    outline: str

    # 用户的修改意见
    suggestion: str


class StoryVolumeOutlineGenerateRequest(BaseModel):
    """分卷大纲生成请求体。

    对应 Java 端 RabbitMQ 分卷大纲生成任务的入参。
    包含故事基本信息和角色设定，用于生成 5-20 卷的详细大纲。
    """

    # 用户 ID
    user_id: int = Field(alias="userId")

    # 故事 ID
    story_id: int = Field(alias="storyId")

    # 故事标题
    title: str

    # 题材，如科幻、玄幻、都市、悬疑
    genre: str | None = None

    # 用户设定的漫剧视觉风格，可选
    story_style: str | None = Field(default=None, alias="storyStyle")

    # 故事摘要，可选
    story_summary: str | None = Field(default=None, alias="storySummary")

    # 故事大纲
    outline: str

    # 主要角色设定列表
    main_characters: list[MainCharacterSetting] = Field(default_factory=list, alias="mainCharacters")


class StoryVolumeOutlineReviseRequest(BaseModel):
    """分卷大纲自动修改请求体。

    对应 Java 端 RabbitMQ 分卷大纲修改任务的入参。
    包含故事上下文、现有分卷大纲和用户的修改意见。
    """

    # 用户 ID
    user_id: int = Field(alias="userId")

    # 故事 ID
    story_id: int = Field(alias="storyId")

    # 故事标题
    title: str

    # 题材，如科幻、玄幻、都市、悬疑
    genre: str | None = None

    # 用户设定的漫剧视觉风格，可选
    story_style: str | None = Field(default=None, alias="storyStyle")

    # 故事摘要，可选
    story_summary: str | None = Field(default=None, alias="storySummary")

    # 故事大纲
    outline: str

    # 主要角色设定列表
    main_characters: list[MainCharacterSetting] = Field(default_factory=list, alias="mainCharacters")

    # 现有分卷大纲列表
    volume_outlines: list[VolumeOutlineItem] = Field(default_factory=list, alias="volumeOutlines")

    # 用户的修改意见
    suggestion: str


class StoryVolumeStoryGenerateRequest(BaseModel):
    """分卷详细故事正文生成请求体。

    调用方：rabbitmq_worker 分卷正文生成任务；同时保留 HTTP 路由用于本地调试。
    包含故事上下文和单卷大纲，用于生成该卷的完整故事正文。
    """

    # 用户 ID
    user_id: int = Field(alias="userId")

    # 故事 ID
    story_id: int = Field(alias="storyId")

    # 分卷 ID
    volume_id: int = Field(alias="volumeId")

    # 故事标题
    title: str

    # 题材，如科幻、玄幻、都市、悬疑
    genre: str | None = None

    # 漫剧视觉风格，可选
    story_style: str | None = Field(default=None, alias="storyStyle")

    # 故事摘要，可选
    story_summary: str | None = Field(default=None, alias="storySummary")

    # 故事大纲
    outline: str

    # 主要角色设定列表
    main_characters: list[MainCharacterSetting] = Field(default_factory=list, alias="mainCharacters")

    # 单卷大纲条目
    volume_outline: VolumeOutlineItem = Field(alias="volumeOutline")


class StoryVolumeSectionGenerateRequest(BaseModel):
    """分卷小节生成请求体。

    调用方：rabbitmq_worker 分卷小节生成任务；同时保留 HTTP 路由用于本地调试。
    包含故事上下文、分卷大纲和已有资产列表，用于生成 4-12 个小节。
    """

    # 用户 ID
    user_id: int = Field(alias="userId")

    # 故事 ID
    story_id: int = Field(alias="storyId")

    # 分卷 ID
    volume_id: int = Field(alias="volumeId")

    # 故事标题
    title: str

    # 题材，如科幻、玄幻、都市、悬疑
    genre: str | None = None

    # 漫剧视觉风格，可选
    story_style: str | None = Field(default=None, alias="storyStyle")

    # 故事摘要，可选
    story_summary: str | None = Field(default=None, alias="storySummary")

    # 故事大纲
    outline: str

    # 主要角色设定列表
    main_characters: list[MainCharacterSetting] = Field(default_factory=list, alias="mainCharacters")

    # 单卷大纲条目
    volume_outline: VolumeOutlineItem = Field(alias="volumeOutline")

    # 已有资产列表，用于判断是否首次出现
    existing_assets: list[ExistingStoryAsset] = Field(default_factory=list, alias="existingAssets")


class StorySectionAssetGenerateRequest(BaseModel):
    """单个小节人物/场景资产生成请求体。

    调用方：rabbitmq_worker 小节资产生成任务；同时保留 HTTP 路由用于本地调试。
    包含故事上下文、分卷大纲、小节内容和已有资产列表。
    """

    # 用户 ID
    user_id: int = Field(alias="userId")

    # 故事 ID
    story_id: int = Field(alias="storyId")

    # 分卷 ID
    volume_id: int = Field(alias="volumeId")

    # 故事标题
    title: str

    # 题材，如科幻、玄幻、都市、悬疑
    genre: str | None = None

    # 漫剧视觉风格，可选
    story_style: str | None = Field(default=None, alias="storyStyle")

    # 故事摘要，可选
    story_summary: str | None = Field(default=None, alias="storySummary")

    # 故事大纲，可选
    outline: str | None = None

    # 主要角色设定列表
    main_characters: list[MainCharacterSetting] = Field(default_factory=list, alias="mainCharacters")

    # 单卷大纲条目
    volume_outline: VolumeOutlineItem = Field(alias="volumeOutline")

    # 当前小节内容
    section: VolumeSectionItem

    # 已有资产列表
    existing_assets: list[ExistingStoryAsset] = Field(default_factory=list, alias="existingAssets")


class StorySectionScriptGenerateRequest(BaseModel):
    """单个小节故事脚本生成请求体。

    调用方：rabbitmq_worker 小节脚本生成任务，同时保留 HTTP 路由用于本地调试。
    包含故事上下文、分卷大纲和小节内容，用于生成分镜脚本。
    """

    # 用户 ID
    user_id: int = Field(alias="userId")

    # 故事 ID
    story_id: int = Field(alias="storyId")

    # 分卷 ID
    volume_id: int = Field(alias="volumeId")

    # 故事标题
    title: str

    # 题材，如科幻、玄幻、都市、悬疑
    genre: str | None = None

    # 漫剧视觉风格，可选
    story_style: str | None = Field(default=None, alias="storyStyle")

    # 故事摘要，可选
    story_summary: str | None = Field(default=None, alias="storySummary")

    # 故事大纲，可选
    outline: str | None = None

    # 主要角色设定列表
    main_characters: list[MainCharacterSetting] = Field(default_factory=list, alias="mainCharacters")

    # 单卷大纲条目
    volume_outline: VolumeOutlineItem = Field(alias="volumeOutline")

    # 当前小节内容
    section: VolumeSectionItem


# ══════════════════════════════════════════════════════════════════════
# 响应模型：返回给 Java 端的结果
# ══════════════════════════════════════════════════════════════════════


class StoryOutlineGenerateResponse(BaseModel):
    """剧情大纲生成响应体。

    返回大模型生成的小说名称、故事摘要、完整大纲和主要角色设定列表。
    """

    # 小说名称
    novel_name: str = Field(alias="novelName")

    # 故事摘要
    story_summary: str = Field(alias="storySummary")

    # 完整剧情大纲
    outline: str

    # 主要角色设定列表
    main_characters: list[MainCharacterSetting] = Field(default_factory=list, alias="mainCharacters")


class StoryOutlineReviseResponse(BaseModel):
    """剧情大纲修改响应体。

    返回修改后的故事摘要、大纲内容和更新后的角色设定。
    """

    # 修改后的故事摘要
    story_summary: str = Field(alias="storySummary")

    # 修改后的完整大纲
    outline: str

    # 更新后的角色设定列表
    main_characters: list[MainCharacterSetting] = Field(default_factory=list, alias="mainCharacters")


class StoryVolumeOutlineGenerateResponse(BaseModel):
    """分卷大纲生成响应体。

    包含大模型生成的分卷大纲列表。
    """

    # 分卷大纲列表
    volumes: list[VolumeOutlineItem]


class StoryVolumeStoryGenerateResponse(BaseModel):
    """分卷详细故事正文生成响应体。"""

    # 分卷故事正文
    volume_story: str = Field(alias="volumeStory")


class StoryVolumeSectionGenerateResponse(BaseModel):
    """分卷小节生成响应体。"""

    # 小节列表
    sections: list[VolumeSectionItem]


class StorySectionScriptGenerateResponse(BaseModel):
    """小节故事脚本生成响应体。"""

    # 小节号
    section_number: int = Field(alias="sectionNumber")

    # 总时长（秒）
    total_duration_seconds: int = Field(alias="totalDurationSeconds", ge=1)

    # 分镜列表
    shots: list[ScriptShotItem]


# ══════════════════════════════════════════════════════════════════════
# LLM 结构化输出模型：大模型返回的约束结构
# 通过 with_structured_output() 绑定，确保大模型输出可反序列化为 Python 对象
# ══════════════════════════════════════════════════════════════════════


class NovelOutlineOutput(BaseModel):
    """剧情大纲结构化输出模型。

    通过 LangChain with_structured_output 绑定，确保大模型输出可反序列化。
    用于剧情大纲生成。
    """

    # 小说标题，简洁且有辨识度
    novel_name: str = Field(description="Novel title, concise and recognizable")

    # 故事摘要，200-300 字
    story_summary: str = Field(description="Story summary, 200-300 Chinese characters")

    # 完整剧情大纲
    outline: str = Field(description="Full story outline with setting, main plot, stages, and key characters")

    # 主要角色设定列表，通常 3-5 个
    main_characters: list[MainCharacterSetting] = Field(description="Main character settings, usually 3-5 key characters")


class OutlineRevisionOutput(BaseModel):
    """剧情大纲修改结构化输出模型。

    定义大模型修改大纲后必须返回的结构。
    用于剧情大纲修改。
    """

    # 修改后的故事摘要
    story_summary: str = Field(description="Updated story summary after applying the user's revision notes")

    # 修改后的完整大纲
    outline: str = Field(description="Complete revised story outline, including unchanged sections and revised sections")

    # 更新后的角色设定列表
    main_characters: list[MainCharacterSetting] = Field(
        default_factory=list,
        description="Updated main character settings inferred from the revised outline",
    )


class VolumeCountOutput(BaseModel):
    """分卷数量规划结构化输出模型。

    由温度为 0 的模型先判断总分卷数，再供逐卷生成链路使用。
    用于分卷大纲生成的第一阶段。
    """

    # 推荐的总分卷数，限制在 5-20 之间
    volume_count: int = Field(
        ge=5,
        le=20,
        description="Recommended total volume count, constrained to an integer between 5 and 20",
    )


class VolumeSectionCountOutput(BaseModel):
    """分卷小节数量规划结构化输出模型。

    由温度为 0 的模型判断某一卷应拆分为多少个小节。
    用于小节生成的第一阶段。
    """

    # 推荐的小节数量，限制在 4-12 之间
    section_count: int = Field(
        ge=4,
        le=12,
        description="Recommended section count, constrained to an integer between 4 and 12",
    )


class SectionAssetExtractionItem(BaseModel):
    """LLM 从小节中识别出的单个人物或场景模型。

    用于资产识别的输出，描述一个被识别出的人物或场景。
    """

    # 稳定的人物或场景名称
    name: str = Field(description="Stable character or scene name")

    # 简短可复用的描述
    description: str = Field(description="Short reusable description")

    # 豆包图片生成提示词
    image_prompt: str = Field(alias="imagePrompt", description="Prompt for Doubao image generation")

    # 匹配的已有资产名称，当识别为同一人物/场景时填写
    matched_existing_name: str | None = Field(
        default=None,
        alias="matchedExistingName",
        description="Exact existing asset name when this item is the same character or scene as one existing asset",
    )


class SectionAssetExtractionOutput(BaseModel):
    """小节人物/场景识别结构化输出模型。

    大模型从小节内容中识别出的人物和场景列表。
    用于资产识别。
    """

    # 识别出的人物列表
    characters: list[SectionAssetExtractionItem] = Field(default_factory=list)

    # 识别出的场景列表
    scenes: list[SectionAssetExtractionItem] = Field(default_factory=list)


class VolumeOutlineOutput(BaseModel):
    """分卷大纲结构化输出模型。

    定义大模型返回的多卷大纲列表结构。
    用于分卷大纲修改。
    """

    # 分卷大纲列表
    volumes: list[VolumeOutlineItem] = Field(description="Detailed volume outline list")
