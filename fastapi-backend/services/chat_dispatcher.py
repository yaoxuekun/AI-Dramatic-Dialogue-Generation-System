"""
对话 Agent 白名单分发模块
根据 AI 返回的 javaMethod 执行对应操作
"""

import json
import logging
from typing import Any, Dict

from pymysql.connections import Connection
import database
from repositories import story_repository, outline_option_repository, prompt_repository

logger = logging.getLogger(__name__)


def dispatch_java_method(user_id: int, method: str, args: Dict[str, Any]) -> str:
    """
    白名单分发：根据 method 执行对应操作

    Args:
        user_id: 当前用户 ID
        method: AI 返回的方法名
        args: 方法参数

    Returns:
        执行结果描述
    """
    if not method or method == "story.none":
        return ""

    logger.info(f"[dispatch] method={method}, args={args}")

    with database.get_db_cursor() as conn:
        try:
            return _dispatch(conn, user_id, method, args)
        except Exception as e:
            logger.error(f"[dispatch] 执行失败: {method}, error={e}")
            return f"操作执行失败: {str(e)}"


def _dispatch(conn: Connection, user_id: int, method: str, args: Dict[str, Any]) -> str:
    """内部白名单分发"""
    return switch(method, conn, user_id, args)


def switch(method: str, conn: Connection, user_id: int, args: Dict[str, Any]) -> str:
    """白名单 switch"""
    handlers = {
        # 漫剧模块
        "story.list": lambda: _story_list(conn, user_id),
        "story.detail": lambda: _story_detail(conn, user_id, args),
        "story.updateBasic": lambda: _story_update_basic(conn, user_id, args),
        "story.updateDetail": lambda: _story_update_detail(conn, user_id, args),
        "story.reviseOutline": lambda: _story_revise_outline(conn, user_id, args),
        "story.generateVolumeOutline": lambda: _story_generate_volume(conn, user_id, args),
        "story.reviseVolumeOutline": lambda: _story_revise_volume(conn, user_id, args),
        "story.generateVolumeSections": lambda: _story_generate_sections(conn, user_id, args),
        "story.generateSectionAssets": lambda: _story_generate_assets(conn, user_id, args),
        "story.generateSectionScript": lambda: _story_generate_script(conn, user_id, args),
        "story.delete": lambda: _story_delete(conn, user_id, args),

        # 大纲配置模块
        "outlineConfig.list": lambda: _outline_config_list(conn),
        "outlineConfig.create": lambda: _outline_config_create(conn, args),
        "outlineConfig.update": lambda: _outline_config_update(conn, args),
        "outlineConfig.delete": lambda: _outline_config_delete(conn, args),

        # Prompt 管理模块
        "prompt.list": lambda: _prompt_list(conn),
        "prompt.detail": lambda: _prompt_detail(conn, args),
        "prompt.create": lambda: _prompt_create(conn, args),
        "prompt.update": lambda: _prompt_update(conn, args),
        "prompt.delete": lambda: _prompt_delete(conn, args),
    }

    handler = handlers.get(method)
    if handler:
        return handler()
    return f"白名单不支持该操作: {method}"


# ── 漫剧模块 ──────────────────────────────────────────────────

def _story_list(conn: Connection, user_id: int) -> str:
    stories = story_repository.find_by_user_id_paginated(conn, user_id, 0, 10)
    if not stories:
        return "暂无漫剧"
    titles = [s["title"] for s in stories]
    return f"你的漫剧：{'、'.join(titles)}"


def _story_detail(conn: Connection, user_id: int, args: Dict) -> str:
    story_id = args.get("storyId")
    if not story_id:
        return "请指定漫剧ID"
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        return "漫剧不存在"
    return f"《{story['title']}》：{story.get('synopsis', '暂无摘要')}"


def _story_update_basic(conn: Connection, user_id: int, args: Dict) -> str:
    story_id = args.get("storyId")
    if not story_id:
        return "请指定漫剧ID"
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        return "漫剧不存在或无权修改"
    story_repository.update_story(
        conn, story_id,
        title=args.get("title"),
        genre=args.get("genre"),
        style=args.get("style"),
        synopsis=args.get("synopsis"),
    )
    return "漫剧信息已更新"


def _story_update_detail(conn: Connection, user_id: int, args: Dict) -> str:
    story_id = args.get("storyId")
    if not story_id:
        return "请指定漫剧ID"
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        return "漫剧不存在或无权修改"
    story_repository.update_story_detail(
        conn, story_id,
        synopsis=args.get("synopsis"),
        full_content=args.get("fullContent"),
    )
    # 如果有角色设定，替换角色
    characters = args.get("characters")
    if characters:
        story_repository.delete_characters_by_story_id(conn, story_id)
        if isinstance(characters, str):
            characters = json.loads(characters)
        story_repository.batch_insert_characters(conn, story_id, characters)
    return "漫剧详情已更新"


def _story_revise_outline(conn: Connection, user_id: int, args: Dict) -> str:
    """对话中修改大纲 - 需要调用 Python AI"""
    story_id = args.get("storyId")
    suggestion = args.get("suggestion")
    if not story_id or not suggestion:
        return "请指定漫剧ID和修改意见"
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        return "漫剧不存在或无权修改"
    # 发布 RabbitMQ 任务
    from services.task_publisher import publish_story_task
    from constants import TaskType
    publish_story_task({
        "taskType": TaskType.STORY_OUTLINE_REVISE,
        "storyId": story_id,
        "userId": user_id,
        "suggestion": suggestion,
        "currentOutline": story.get("full_content", ""),
        "currentSynopsis": story.get("synopsis", ""),
    })
    story_repository.update_story_status(conn, story_id, "revising")
    return "大纲修改任务已提交，请稍后查看结果"


def _story_generate_volume(conn: Connection, user_id: int, args: Dict) -> str:
    story_id = args.get("storyId")
    if not story_id:
        return "请指定漫剧ID"
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        return "漫剧不存在或无权操作"
    from services.task_publisher import publish_story_task
    from constants import TaskType
    characters = story_repository.find_characters_by_story_id(conn, story_id)
    publish_story_task({
        "taskType": TaskType.VOLUME_OUTLINE_GENERATE,
        "storyId": story_id,
        "userId": user_id,
        "title": story.get("title", ""),
        "genre": story.get("genre", ""),
        "storyStyle": story.get("style", ""),
        "synopsis": story.get("synopsis", ""),
        "outline": story.get("full_content", ""),
        "mainCharacters": [{"name": c["name"], "role_position": c.get("role_position", "")} for c in characters],
    })
    story_repository.update_story_status(conn, story_id, "generating")
    return "分卷大纲生成任务已提交"


def _story_revise_volume(conn: Connection, user_id: int, args: Dict) -> str:
    story_id = args.get("storyId")
    suggestion = args.get("suggestion")
    if not story_id or not suggestion:
        return "请指定漫剧ID和修改意见"
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        return "漫剧不存在或无权修改"
    from services.task_publisher import publish_story_task
    from constants import TaskType
    existing_volumes = story_repository.find_volume_outlines_by_story_id(conn, story_id)
    publish_story_task({
        "taskType": TaskType.VOLUME_OUTLINE_REVISE,
        "storyId": story_id,
        "userId": user_id,
        "suggestion": suggestion,
        "currentVolumes": existing_volumes,
    })
    story_repository.update_story_status(conn, story_id, "generating")
    return "分卷大纲修改任务已提交"


def _story_generate_sections(conn: Connection, user_id: int, args: Dict) -> str:
    story_id = args.get("storyId")
    volume_id = args.get("volumeId")
    if not story_id or not volume_id:
        return "请指定漫剧ID和分卷ID"
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        return "漫剧不存在或无权操作"
    volume = story_repository.find_volume_by_id_and_story_id(conn, volume_id, story_id)
    if not volume:
        return "分卷不存在"
    from services.task_publisher import publish_story_task
    from constants import TaskType
    characters = story_repository.find_characters_by_story_id(conn, story_id)
    publish_story_task({
        "taskType": TaskType.VOLUME_SECTION_GENERATE,
        "storyId": story_id,
        "userId": user_id,
        "volumeId": volume_id,
        "title": story.get("title", ""),
        "genre": story.get("genre", ""),
        "storyStyle": story.get("style", ""),
        "synopsis": story.get("synopsis", ""),
        "outline": story.get("full_content", ""),
        "mainCharacters": [{"name": c["name"], "role_position": c.get("role_position", "")} for c in characters],
        "volumeOutline": volume,
    })
    story_repository.update_story_status(conn, story_id, "generating")
    return "小节故事生成任务已提交"


def _story_generate_assets(conn: Connection, user_id: int, args: Dict) -> str:
    story_id = args.get("storyId")
    section_id = args.get("sectionId")
    if not story_id or not section_id:
        return "请指定漫剧ID和小节ID"
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        return "漫剧不存在或无权操作"
    from services.task_publisher import publish_story_task
    from constants import TaskType
    section = story_repository.find_section_by_id_and_story_id(conn, section_id, story_id)
    if not section:
        return "小节不存在"
    existing_assets = story_repository.find_existing_assets_for_story(conn, story_id)
    publish_story_task({
        "taskType": TaskType.SECTION_ASSET_GENERATE,
        "storyId": story_id,
        "userId": user_id,
        "sectionId": section_id,
        "volumeId": section.get("volume_id"),
        "sectionNumber": section.get("section_number"),
        "section": section,
        "existingAssets": existing_assets,
    })
    story_repository.update_story_status(conn, story_id, "generating")
    return "人物/场景图片生成任务已提交"


def _story_generate_script(conn: Connection, user_id: int, args: Dict) -> str:
    story_id = args.get("storyId")
    section_id = args.get("sectionId")
    if not story_id or not section_id:
        return "请指定漫剧ID和小节ID"
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        return "漫剧不存在或无权操作"
    section = story_repository.find_section_by_id_and_story_id(conn, section_id, story_id)
    if not section:
        return "小节不存在"
    from services.task_publisher import publish_story_task
    from constants import TaskType
    characters = story_repository.find_characters_by_story_id(conn, story_id)
    publish_story_task({
        "taskType": TaskType.SECTION_SCRIPT_GENERATE,
        "storyId": story_id,
        "userId": user_id,
        "sectionId": section_id,
        "volumeId": section.get("volume_id"),
        "sectionNumber": section.get("section_number"),
        "section": section,
        "title": story.get("title", ""),
        "genre": story.get("genre", ""),
        "storyStyle": story.get("style", ""),
        "synopsis": story.get("synopsis", ""),
        "outline": story.get("full_content", ""),
        "mainCharacters": [{"name": c["name"], "role_position": c.get("role_position", "")} for c in characters],
    })
    story_repository.update_story_status(conn, story_id, "generating")
    return "分镜脚本生成任务已提交"


def _story_delete(conn: Connection, user_id: int, args: Dict) -> str:
    story_id = args.get("storyId")
    if not story_id:
        return "请指定漫剧ID"
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        return "漫剧不存在或无权删除"
    story_repository.delete_story_by_id(conn, story_id)
    return "漫剧已删除"


# ── 大纲配置模块 ──────────────────────────────────────────────

def _outline_config_list(conn: Connection) -> str:
    options = outline_option_repository.find_all(conn)
    if not options:
        return "暂无大纲配置"
    genres = [o["name"] for o in options if o["option_type"] == "GENRE"]
    styles = [o["name"] for o in options if o["option_type"] == "STYLE"]
    return f"题材：{'、'.join(genres)}；风格：{'、'.join(styles)}"


def _outline_config_create(conn: Connection, args: Dict) -> str:
    option_type = args.get("optionType")
    name = args.get("name")
    if not option_type or not name:
        return "请指定配置类型和名称"
    existing = outline_option_repository.find_by_type_and_name(conn, option_type, name)
    if existing:
        return f"配置已存在: {name}"
    outline_option_repository.create(
        conn, option_type=option_type, name=name,
        description=args.get("description"), sort_order=args.get("sortOrder", 0),
        enabled=args.get("enabled", True),
    )
    return f"配置已创建: {name}"


def _outline_config_update(conn: Connection, args: Dict) -> str:
    option_id = args.get("id")
    if not option_id:
        return "请指定配置ID"
    existing = outline_option_repository.find_by_id(conn, option_id)
    if not existing:
        return "配置不存在"
    outline_option_repository.update(
        conn, option_id,
        name=args.get("name"), description=args.get("description"),
        sort_order=args.get("sortOrder"), enabled=args.get("enabled"),
    )
    return "配置已更新"


def _outline_config_delete(conn: Connection, args: Dict) -> str:
    option_id = args.get("id")
    if not option_id:
        return "请指定配置ID"
    existing = outline_option_repository.find_by_id(conn, option_id)
    if not existing:
        return "配置不存在"
    outline_option_repository.delete_by_id(conn, option_id)
    return "配置已删除"


# ── Prompt 管理模块 ──────────────────────────────────────────

def _prompt_list(conn: Connection) -> str:
    prompts = prompt_repository.find_all(conn)
    if not prompts:
        return "暂无Prompt"
    names = [p["prompt_name"] for p in prompts]
    return f"Prompt列表：{'、'.join(names)}"


def _prompt_detail(conn: Connection, args: Dict) -> str:
    prompt_id = args.get("id")
    if not prompt_id:
        return "请指定Prompt ID"
    prompt = prompt_repository.find_by_id(conn, prompt_id)
    if not prompt:
        return "Prompt不存在"
    return f"Prompt：{prompt['prompt_name']}（{prompt['category']}）"


def _prompt_create(conn: Connection, args: Dict) -> str:
    prompt_key = args.get("promptKey")
    name = args.get("name")
    template = args.get("templateContent")
    if not prompt_key or not name or not template:
        return "请指定promptKey、名称和模板内容"
    existing = prompt_repository.find_by_prompt_key(conn, prompt_key)
    if existing:
        return f"promptKey已存在: {prompt_key}"
    prompt_repository.create(
        conn, prompt_key=prompt_key, name=name,
        category=args.get("category"), description=args.get("description"),
        template_content=template, enabled=args.get("enabled", True),
        parameters=args.get("parameters", []),
        base_prompt_key=args.get("basePromptKey"),
        prompt_scope=args.get("promptScope"),
        match_genre=args.get("matchGenre"), match_style=args.get("matchStyle"),
        priority=args.get("priority", 0),
    )
    return f"Prompt已创建: {name}"


def _prompt_update(conn: Connection, args: Dict) -> str:
    prompt_id = args.get("id")
    if not prompt_id:
        return "请指定Prompt ID"
    existing = prompt_repository.find_by_id(conn, prompt_id)
    if not existing:
        return "Prompt不存在"
    prompt_repository.update(
        conn, prompt_id,
        name=args.get("name"), category=args.get("category"),
        description=args.get("description"), template_content=args.get("templateContent"),
        enabled=args.get("enabled"), parameters=args.get("parameters"),
        base_prompt_key=args.get("basePromptKey"), prompt_scope=args.get("promptScope"),
        match_genre=args.get("matchGenre"), match_style=args.get("matchStyle"),
        priority=args.get("priority"),
    )
    return "Prompt已更新"


def _prompt_delete(conn: Connection, args: Dict) -> str:
    prompt_id = args.get("id")
    if not prompt_id:
        return "请指定Prompt ID"
    existing = prompt_repository.find_by_id(conn, prompt_id)
    if not existing:
        return "Prompt不存在"
    prompt_repository.delete_by_id(conn, prompt_id)
    return "Prompt已删除"
