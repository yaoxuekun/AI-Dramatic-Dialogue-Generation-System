# story_ai_pkg 包初始化模块
# 本文件定义包的公共接口，统一导出所有外部需要的符号。
# main.py 和 rabbitmq_worker.py 通过 story_ai.py 兼容门面间接导入这些符号。

# ── 从 models.py 导出所有数据模型 ──────────────────────────────────────
from .models import (
    ExistingStoryAsset,                      # 已有故事资产引用（用于判断是否首次出现）
    MainCharacterSetting,                    # 主要角色设定（姓名、角色、描述、性格、外观）
    ScriptShotItem,                          # 单个分镜脚本条目（镜头号、时长、景别、运镜、动作、对白）
    SectionAssetExtractionItem,              # LLM 识别出的单个人物或场景
    SectionAssetExtractionOutput,            # LLM 资产识别结构化输出
    SectionAssetItem,                        # 当前小节的人物或场景资产
    StoryOutlineGenerateRequest,             # 剧情大纲生成请求
    StoryOutlineGenerateResponse,            # 剧情大纲生成响应
    StoryOutlineReviseRequest,               # 剧情大纲修改请求
    StoryOutlineReviseResponse,              # 剧情大纲修改响应
    StorySectionAssetGenerateRequest,        # 小节资产生成请求
    StorySectionScriptGenerateRequest,       # 小节分镜脚本生成请求
    StorySectionScriptGenerateResponse,      # 小节分镜脚本生成响应
    StoryVolumeOutlineGenerateRequest,       # 分卷大纲生成请求
    StoryVolumeOutlineGenerateResponse,      # 分卷大纲生成响应
    StoryVolumeOutlineReviseRequest,         # 分卷大纲修改请求
    StoryVolumeSectionGenerateRequest,       # 分卷小节生成请求
    StoryVolumeSectionGenerateResponse,      # 分卷小节生成响应
    StoryVolumeStoryGenerateRequest,         # 分卷正文生成请求
    StoryVolumeStoryGenerateResponse,        # 分卷正文生成响应
    VolumeCountOutput,                       # 分卷数量规划输出
    VolumeOutlineItem,                       # 单卷大纲条目
    VolumeOutlineOutput,                     # 分卷大纲结构化输出
    VolumeSectionCountOutput,                # 小节数量规划输出
    VolumeSectionItem,                       # 单个小节故事细节
)

# ── 从 router.py 导出路由器 ────────────────────────────────────────────
from .router import router                   # FastAPI 路由器，挂载到主 app

# ── 从 outline.py 导出剧情大纲相关函数 ──────────────────────────────────
from .outline import generate_story_outline, revise_story_outline

# ── 从 volumes.py 导出分卷相关函数 ─────────────────────────────────────
from .volumes import generate_volume_outline, generate_volume_story, revise_volume_outline

# ── 从 sections.py 导出小节相关函数 ─────────────────────────────────────
from .sections import generate_volume_sections, generate_volume_sections_endpoint

# ── 从 assets.py 导出资产相关函数 ──────────────────────────────────────
from .assets import (
    build_asset_registry,                    # 构建已有资产字典
    build_character_three_view_prompt,       # 构造人物三视图提示词
    build_doubao_prompt,                     # 构造豆包图片生成提示词
    build_scene_concept_prompt,              # 构造场景概念图提示词
    format_existing_asset_context,           # 已有资产转上下文文本
    generate_asset_image_path,               # 调用豆包生成资产图片
    generate_section_assets,                 # 小节资产生成入口
    has_local_image_file,                    # 判断本地图片文件是否存在
    normalize_asset_key,                     # 资产 key 归一化
    resolve_section_assets,                  # 小节资产批量解析
    resolve_single_section_asset,            # 单个资产解析
    resolve_storage_file,                    # 解析 storage 相对路径
    save_doubao_image_file,                  # 豆包图片生成并保存
)

# ── 从 scripts.py 导出脚本生成函数 ─────────────────────────────────────
from .scripts import generate_section_script

# ── 公共接口列表，定义 from story_ai_pkg import * 时导出的符号 ─────────
__all__ = [
    'router',
    # 数据模型
    'ExistingStoryAsset',
    'MainCharacterSetting',
    'ScriptShotItem',
    'SectionAssetExtractionItem',
    'SectionAssetExtractionOutput',
    'SectionAssetItem',
    'StoryOutlineGenerateRequest',
    'StoryOutlineGenerateResponse',
    'StoryOutlineReviseRequest',
    'StoryOutlineReviseResponse',
    'StorySectionAssetGenerateRequest',
    'StorySectionScriptGenerateRequest',
    'StorySectionScriptGenerateResponse',
    'StoryVolumeOutlineGenerateRequest',
    'StoryVolumeOutlineGenerateResponse',
    'StoryVolumeOutlineReviseRequest',
    'StoryVolumeSectionGenerateRequest',
    'StoryVolumeSectionGenerateResponse',
    'StoryVolumeStoryGenerateRequest',
    'StoryVolumeStoryGenerateResponse',
    'VolumeCountOutput',
    'VolumeOutlineItem',
    'VolumeOutlineOutput',
    'VolumeSectionCountOutput',
    'VolumeSectionItem',
    # 业务函数
    'generate_story_outline',
    'revise_story_outline',
    'generate_volume_outline',
    'generate_volume_story',
    'revise_volume_outline',
    'generate_volume_sections',
    'generate_volume_sections_endpoint',
    'generate_section_assets',
    'generate_section_script',
    # 资产工具函数
    'build_asset_registry',
    'build_character_three_view_prompt',
    'build_doubao_prompt',
    'build_scene_concept_prompt',
    'format_existing_asset_context',
    'generate_asset_image_path',
    'has_local_image_file',
    'normalize_asset_key',
    'resolve_section_assets',
    'resolve_single_section_asset',
    'resolve_storage_file',
    'save_doubao_image_file',
]
