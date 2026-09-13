"""
RabbitMQ 结果消费者
监听 aisay.ai.story.result 队列，将 AI 任务结果落库。
在后台 daemon 线程中运行，不阻塞 FastAPI 主进程。
"""

import json
import logging
import threading
import time
from typing import Any, Dict, Optional

import pika

from config import settings
from constants import StoryStatus
import database
from repositories import story_repository, deleted_story_repository

logger = logging.getLogger(__name__)

# 后台线程引用，避免重复启动
_consumer_thread: Optional[threading.Thread] = None

# ── 任务类型 → 下一状态映射 ────────────────────────────────────────
# 当任务 completed 时，将 story.status 更新为对应的下一状态
_NEXT_STATUS: Dict[str, str] = {
    "STORY_OUTLINE_GENERATE": StoryStatus.VOLUME_PENDING,
    "STORY_OUTLINE_REVISE":    StoryStatus.DRAFT,
    "VOLUME_OUTLINE_GENERATE": StoryStatus.VOLUME_SECTION_PENDING,
    "VOLUME_OUTLINE_REVISE":   StoryStatus.DRAFT,
    "VOLUME_SECTION_GENERATE": StoryStatus.SECTION_ASSET_PENDING,
    "SECTION_ASSET_GENERATE":  StoryStatus.SECTION_SCRIPT_PENDING,
    "SECTION_SCRIPT_GENERATE": StoryStatus.DRAFT,
}

# Python worker 使用的任务类型名 → constants 名称 归一化
_NORMALIZE: Dict[str, str] = {
    "STORY_GENERATE":             "STORY_OUTLINE_GENERATE",
    "STORY_REVISE":               "STORY_OUTLINE_REVISE",
    "VOLUME_GENERATE":            "VOLUME_OUTLINE_GENERATE",
    "VOLUME_REVISE":              "VOLUME_OUTLINE_REVISE",
    "VOLUME_STORY_GENERATE":      "VOLUME_STORY_GENERATE",
    "VOLUME_SECTION_GENERATE":    "VOLUME_SECTION_GENERATE",
    "SECTION_ASSET_GENERATE":     "SECTION_ASSET_GENERATE",
    "SECTION_SCRIPT_GENERATE":    "SECTION_SCRIPT_GENERATE",
}


# ── 公共入口 ────────────────────────────────────────────────────────

def start_result_consumer() -> None:
    """启动结果队列消费线程（FastAPI lifespan 中调用）。"""
    global _consumer_thread
    if _consumer_thread and _consumer_thread.is_alive():
        return
    _consumer_thread = threading.Thread(
        target=_reconnect_loop, name="aisay-result-consumer", daemon=True
    )
    _consumer_thread.start()
    logger.info("[result-consumer] 后台消费线程已启动")


# ── 内部：连接循环 ──────────────────────────────────────────────────

def _reconnect_loop() -> None:
    """异常断开后自动重连的外层循环。"""
    while True:
        try:
            _consume_forever()
        except Exception as exc:
            logger.error(f"[result-consumer] 连接异常: {exc}，5 秒后重试")
            time.sleep(5)


def _consume_forever() -> None:
    """声明队列拓扑并持续消费结果消息。"""
    credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        virtual_host=settings.RABBITMQ_VHOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # 声明交换机和结果队列（与 rabbitmq_client.init_rabbitmq 保持一致）
    channel.exchange_declare(
        exchange=settings.RABBITMQ_EXCHANGE, exchange_type="direct", durable=True
    )
    channel.queue_declare(queue=settings.RABBITMQ_QUEUE_STORY_RESULT, durable=True)
    channel.queue_bind(
        queue=settings.RABBITMQ_QUEUE_STORY_RESULT,
        exchange=settings.RABBITMQ_EXCHANGE,
        routing_key=settings.RABBITMQ_ROUTING_KEY_STORY_RESULT,
    )
    channel.basic_qos(prefetch_count=1)

    def on_message(ch: Any, method: Any, properties: Any, body: bytes) -> None:
        message = json.loads(body.decode("utf-8"))
        task_type_raw = message.get("taskType", "UNKNOWN")
        story_id = message.get("storyId")
        logger.info(
            f"[result-consumer] 收到消息: taskType={task_type_raw}, "
            f"storyId={story_id}, success={message.get('success')}, "
            f"partial={message.get('partial')}, completed={message.get('completed')}"
        )
        try:
            _dispatch(message)
        except Exception as exc:
            logger.error(f"[result-consumer] 处理失败: {exc}", exc_info=True)
            if story_id:
                _mark_failed(story_id)
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=settings.RABBITMQ_QUEUE_STORY_RESULT, on_message_callback=on_message
    )
    logger.info(
        f"[result-consumer] 开始消费队列 {settings.RABBITMQ_QUEUE_STORY_RESULT}"
    )
    channel.start_consuming()


# ── 内部：消息分发 ──────────────────────────────────────────────────

def _normalize_task_type(raw: str) -> str:
    """将 Python worker 的任务类型名归一化为 constants 中的名称。"""
    return _NORMALIZE.get(raw, raw)


def _dispatch(msg: Dict[str, Any]) -> None:
    """按 taskType 分发到对应落库逻辑。"""
    task_type = _normalize_task_type(msg.get("taskType", ""))
    story_id = msg.get("storyId")
    success = msg.get("success", False)
    completed = msg.get("completed", False)

    if not story_id:
        logger.warning("[result-consumer] 消息缺少 storyId，跳过")
        return

    # 检查漫剧是否已被删除，已删除则跳过处理
    if deleted_story_repository.is_deleted(story_id):
        logger.info(f"[result-consumer] storyId={story_id} 已删除，跳过处理")
        return

    # ── 失败消息 ────────────────────────────────────
    if not success:
        logger.warning(
            f"[result-consumer] 任务失败: taskType={task_type}, "
            f"error={msg.get('errorMessage')}"
        )
        _mark_failed(story_id)
        return

    # ── STORY_OUTLINE_GENERATE / STORY_OUTLINE_REVISE ──
    if task_type in ("STORY_OUTLINE_GENERATE", "STORY_OUTLINE_REVISE"):
        _save_story_outline(story_id, msg.get("storyOutline"))
        if completed:
            _update_status(story_id, _NEXT_STATUS.get(task_type, StoryStatus.DRAFT))

    # ── VOLUME_OUTLINE_GENERATE / VOLUME_OUTLINE_REVISE ──
    elif task_type in ("VOLUME_OUTLINE_GENERATE", "VOLUME_OUTLINE_REVISE"):
        if completed:
            # 完成时先清空旧分卷，再插入新分卷
            with database.get_db_cursor() as conn:
                story_repository.delete_volume_outlines_by_story_id(conn, story_id)
        _save_volume_outlines(story_id, msg.get("volumeOutline"))
        if completed:
            _update_status(story_id, _NEXT_STATUS.get(task_type, StoryStatus.DRAFT))

    # ── VOLUME_SECTION_GENERATE ──
    elif task_type == "VOLUME_SECTION_GENERATE":
        volume_id = msg.get("volumeId")
        if volume_id and msg.get("volumeSection"):
            _save_volume_section(story_id, volume_id, msg["volumeSection"])
        if completed:
            _update_status(story_id, _NEXT_STATUS.get(task_type, StoryStatus.DRAFT))

    # ── SECTION_ASSET_GENERATE ──
    elif task_type == "SECTION_ASSET_GENERATE":
        volume_id = msg.get("volumeId")
        if volume_id and msg.get("volumeSection"):
            _save_section_assets(story_id, volume_id, msg["volumeSection"])
        if completed:
            _update_status(story_id, _NEXT_STATUS.get(task_type, StoryStatus.DRAFT))

    # ── SECTION_SCRIPT_GENERATE ──
    elif task_type == "SECTION_SCRIPT_GENERATE":
        if msg.get("sectionScript"):
            _save_section_script(story_id, msg.get("volumeId"), msg["sectionScript"])
        if completed:
            _update_status(story_id, _NEXT_STATUS.get(task_type, StoryStatus.DRAFT))

    # ── VOLUME_STORY_GENERATE（分卷正文，暂不落库）──
    elif task_type == "VOLUME_STORY_GENERATE":
        logger.info(f"[result-consumer] VOLUME_STORY_GENERATE 完成，storyId={story_id}")
        if completed:
            _update_status(story_id, StoryStatus.DRAFT)

    else:
        logger.warning(f"[result-consumer] 未知任务类型: {task_type}")


# ── 内部：落库函数 ──────────────────────────────────────────────────

def _save_story_outline(story_id: int, outline: Optional[Dict[str, Any]]) -> None:
    """保存剧情大纲结果。"""
    if not outline:
        return
    with database.get_db_cursor() as conn:
        story_repository.save_story_outline(
            conn,
            story_id=story_id,
            title=outline.get("novel_name") or outline.get("novelName"),
            synopsis=outline.get("story_summary") or outline.get("storySummary"),
            outline=outline.get("outline"),
            characters=outline.get("main_characters") or outline.get("mainCharacters"),
        )
    logger.info(f"[result-consumer] 剧情大纲已保存, storyId={story_id}")


def _save_volume_outlines(story_id: int, volume_outline: Optional[Dict[str, Any]]) -> None:
    """保存分卷大纲结果（支持逐卷 partial）。"""
    if not volume_outline:
        return
    volumes = volume_outline.get("volumes", [])
    if not volumes:
        return
    with database.get_db_cursor() as conn:
        for v in volumes:
            story_repository.upsert_volume_outline(
                conn,
                story_id=story_id,
                volume_number=v.get("volumeNumber", 0),
                title=v.get("title", ""),
                summary=v.get("summary"),
                content=v.get("content"),
                ending_hook=v.get("endingHook"),
            )
    logger.info(f"[result-consumer] 分卷大纲已保存 {len(volumes)} 卷, storyId={story_id}")


def _save_volume_section(story_id: int, volume_id: int, section_data: Dict[str, Any]) -> None:
    """保存小节结果（支持逐节 partial）。"""
    sections = section_data.get("sections", [])
    if not sections:
        return
    with database.get_db_cursor() as conn:
        for s in sections:
            story_repository.upsert_volume_section(
                conn,
                story_id=story_id,
                volume_id=volume_id,
                section_number=s.get("sectionNumber", 0),
                title=s.get("title", ""),
                summary=s.get("summary"),
                content=s.get("content"),
                ending_hook=s.get("endingHook"),
            )
    logger.info(f"[result-consumer] 小节已保存 {len(sections)} 节, storyId={story_id}")


def _save_section_assets(story_id: int, volume_id: int, asset_data: Dict[str, Any]) -> None:
    """保存小节资产结果。"""
    characters = asset_data.get("characters", [])
    scenes = asset_data.get("scenes", [])
    if not characters and not scenes:
        return

    # 获取 section_id：从 volumeSection 中的 sectionNumber + volumeId 查找
    section_number = None
    if characters:
        section_number = characters[0].get("sectionNumber")
    if not section_number and scenes:
        section_number = scenes[0].get("sectionNumber")

    with database.get_db_cursor() as conn:
        section_id = _find_section_id(conn, volume_id, section_number) if section_number else None
        if not section_id:
            logger.warning(
                f"[result-consumer] 未找到小节, volumeId={volume_id}, "
                f"sectionNumber={section_number}，跳过资产保存"
            )
            return
        story_repository.save_section_assets(
            conn,
            story_id=story_id,
            section_id=section_id,
            characters=characters,
            scenes=scenes,
        )
    logger.info(f"[result-consumer] 资产已保存, storyId={story_id}, sectionId={section_id}")


def _save_section_script(story_id: int, volume_id: Optional[int], script_data: Dict[str, Any]) -> None:
    """保存分镜脚本结果。"""
    shots = script_data.get("shots", [])
    section_number = script_data.get("sectionNumber")
    if not shots or not section_number or not volume_id:
        return

    with database.get_db_cursor() as conn:
        section_id = _find_section_id(conn, volume_id, section_number)
        if not section_id:
            logger.warning(
                f"[result-consumer] 未找到小节, volumeId={volume_id}, "
                f"sectionNumber={section_number}，跳过脚本保存"
            )
            return
        story_repository.replace_section_scripts(
            conn,
            story_id=story_id,
            section_id=section_id,
            shots=shots,
        )
    logger.info(f"[result-consumer] 分镜脚本已保存 {len(shots)} 镜头, storyId={story_id}")


# ── 内部：工具函数 ──────────────────────────────────────────────────

def _find_section_id(conn: Any, volume_id: int, section_number: int) -> Optional[int]:
    """根据 volume_id + section_number 查找小节 ID。"""
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM story_volume_sections WHERE volume_id = %s AND section_number = %s",
        (volume_id, section_number),
    )
    row = cur.fetchone()
    return row["id"] if row else None


def _update_status(story_id: int, status: str) -> None:
    """更新漫剧状态。"""
    try:
        with database.get_db_cursor() as conn:
            story_repository.update_story_status(conn, story_id, status)
        logger.info(f"[result-consumer] 状态已更新: storyId={story_id} → {status}")
    except Exception as exc:
        logger.error(f"[result-consumer] 更新状态失败: storyId={story_id}, {exc}")


def _mark_failed(story_id: int) -> None:
    """标记漫剧为失败状态。"""
    _update_status(story_id, StoryStatus.FAILED)
