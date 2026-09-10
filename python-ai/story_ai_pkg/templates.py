# 提示词模板初始化模块
# 本文件把 prompt_key 映射到 MySQL 中的模板内容。
# Python 仅按 prompt_key 读取模板，Prompt 的新增、修改、删除都由 Java 后端处理。
# prompt.py 仍作为数据库不可用或 SQL 未执行时的兼容兜底。

# 从 prompt 模块导入所有原始提示词字符串，作为数据库兜底内容
from prompt import (
    prompt_Outline,                  # 剧情大纲生成提示词
    prompt_ReviseOutline,            # 剧情大纲修改提示词
    prompt_SectionAssetExtraction,   # 小节资产识别提示词
    prompt_SectionScriptGenerate,    # 分镜脚本生成提示词
    prompt_VolumeCount,              # 分卷数量规划提示词
    prompt_VolumeOutlineSingle,      # 单卷大纲生成提示词
    prompt_VolumeOutline_Editor,     # 分卷大纲修改提示词
    prompt_VolumeSectionCount,       # 小节数量规划提示词
    prompt_VolumeSectionSingle,      # 单节故事生成提示词
    prompt_VolumeStory,              # 分卷正文生成提示词
)

from .prompt_repository import get_prompt_template


PROMPT_FALLBACKS = {
    "generate_story_outline": prompt_Outline,
    "revise_story_outline": prompt_ReviseOutline,
    "generate_volume_count": prompt_VolumeCount,
    "generate_volume_outline_single": prompt_VolumeOutlineSingle,
    "revise_volume_outline": prompt_VolumeOutline_Editor,
    "generate_volume_story": prompt_VolumeStory,
    "generate_volume_section_count": prompt_VolumeSectionCount,
    "generate_volume_section_single": prompt_VolumeSectionSingle,
    "extract_section_assets": prompt_SectionAssetExtraction,
    "generate_section_script": prompt_SectionScriptGenerate,
}


def load_prompt_template(prompt_key: str, *, genre: str | None = None, story_style: str | None = None):
    """按 prompt_key 从 MySQL 加载模板，支持按题材/风格匹配特定 Prompt。"""
    fallback = PROMPT_FALLBACKS[prompt_key]
    return get_prompt_template(prompt_key, fallback, genre=genre, story_style=story_style)
