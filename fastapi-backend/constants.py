# constants.py
"""
项目常量定义
作用：为了方便管理所有 RabbitMQ 任务类型
"""


class TaskType:
    """RabbitMQ AI 任务类型"""

    STORY_OUTLINE_GENERATE = "STORY_OUTLINE_GENERATE"
    STORY_OUTLINE_REVISE = "STORY_OUTLINE_REVISE"
    VOLUME_OUTLINE_GENERATE = "VOLUME_OUTLINE_GENERATE"
    VOLUME_OUTLINE_REVISE = "VOLUME_OUTLINE_REVISE"
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
    VOLUME_SECTION_PENDING = "volume_section_pending"
    SECTION_ASSET_PENDING = "section_asset_pending"  # 👈 4.9 需要
    SECTION_SCRIPT_PENDING = "section_script_pending"
    FAILED = "failed"

    BUSY_STATUSES = [
        GENERATING,
        REVISING,
        VOLUME_PENDING,
        VOLUME_REVISING,
        VOLUME_SECTION_PENDING,
        SECTION_ASSET_PENDING,
        SECTION_SCRIPT_PENDING,
    ]

BUSY_STATUSES = [
    "generating",
    "revising",
    "volume_pending",
    "volume_revising",
    "volume_section_pending",
    "section_asset_pending",
    "section_script_pending",
]