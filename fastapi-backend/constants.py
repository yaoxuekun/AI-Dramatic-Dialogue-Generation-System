# constants.py
"""
项目常量定义
作用：为了方便管理所有 RabbitMQ 任务类型
"""


class TaskType:
    """RabbitMQ AI 任务类型（与 Python worker 保持一致）"""

    STORY_OUTLINE_GENERATE = "STORY_GENERATE"
    STORY_OUTLINE_REVISE = "STORY_REVISE"
    VOLUME_OUTLINE_GENERATE = "VOLUME_GENERATE"
    VOLUME_OUTLINE_REVISE = "VOLUME_REVISE"
    VOLUME_STORY_GENERATE = "VOLUME_STORY_GENERATE"
    VOLUME_SECTION_GENERATE = "VOLUME_SECTION_GENERATE"
    SECTION_ASSET_GENERATE = "SECTION_ASSET_GENERATE"
    SECTION_SCRIPT_GENERATE = "SECTION_SCRIPT_GENERATE"


class StoryStatus:
    """漫剧状态常量"""

    DRAFT = "draft"
    GENERATING = "generating"
    REVISING = "revising"
    VOLUME_PENDING = "volume_pending"
    VOLUME_REVISING = "volume_revising"
    VOLUME_STORY_PENDING = "volume_story_pending"
    VOLUME_SECTION_PENDING = "volume_section_pending"
    SECTION_ASSET_PENDING = "section_asset_pending"
    SECTION_SCRIPT_PENDING = "section_script_pending"
    FAILED = "failed"


# 忙碌状态列表（AI 正在处理中，不允许提交新任务）
# "xxx_pending" 表示等待用户操作，不是忙碌状态
BUSY_STATUSES = [
    "generating",         # AI 正在生成
    "revising",           # AI 正在修改
    "volume_revising",    # AI 正在修改分卷
    "volume_story_pending",  # AI 正在生成分卷正文
]
