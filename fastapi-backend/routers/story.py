# router/story.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pymysql.connections import Connection
from math import ceil
from repositories import story_repository, chat_session_repository, deleted_story_repository
from schemas.story import (
    StoryUpdateRequest,
    StoryResponse,
    StoryDetailResponse,
    StoryListResponse,
    CharacterResponse,
    VolumeOutlineResponse,
    VolumeSectionResponse,
    SectionScriptResponse,
    AssetResponse,
    StoryGenerateRequest,
    OutlineReviseRequest,
    StoryDetailUpdateRequest,
    CharacterCrateRequest,
    VolumeOutlineItemRequest,
    VolumeOutlineUpdateRequest,
)
from schemas.common import success_response
from database import get_db
from dependencies import get_current_user
import json
from rabbitmq_client import publish_message
from config import settings
from constants import TaskType, StoryStatus, BUSY_STATUSES
from utils.file_storage import save_upload_file, delete_file
from utils.docx_export import export_story_docx

router = APIRouter(prefix="/story")


# 校验 story
def check_story(story: dict):
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="漫剧不存在或不属于当前用户"
        )

    if story["status"] in BUSY_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态为 {story['status']}，请等待上一个任务完成",
        )


@router.get("/list")
def get_story_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """获取当前用户的漫剧列表（分页）"""
    user_id = current_user["id"]

    total = story_repository.count_by_user_id(conn, user_id)
    offset = (page - 1) * size
    records = story_repository.find_by_user_id_paginated(conn, user_id, offset, size)

    story_list = [StoryResponse(**r) for r in records]

    return success_response(
        data=StoryListResponse(
            records=story_list,
            current=page,
            size=size,
            total=total,
            pages=ceil(total / size) if size > 0 else 0,
        ).model_dump(by_alias=True)
    )


def _build_story_detail_response(conn: Connection, story: dict) -> dict:
    """组装完整漫剧详情响应（characters + volume_outlines + sections + scripts + assets）。"""
    story_id = story["id"]

    characters_raw = story_repository.find_characters_by_story_id(conn, story_id)
    characters = [CharacterResponse(**c) for c in characters_raw]

    volumes_raw = story_repository.find_volume_outlines_by_story_id(conn, story_id)
    volume_ids = [v["id"] for v in volumes_raw]

    sections_by_volume = {}
    section_ids = []
    if volume_ids:
        sections_raw = story_repository.find_sections_by_volume_ids(conn, volume_ids)
        for s in sections_raw:
            volume_id = s["volume_id"]
            if volume_id not in sections_by_volume:
                sections_by_volume[volume_id] = []
            sections_by_volume[volume_id].append(s)
            section_ids.append(s["id"])

    scripts_by_section = {}
    if section_ids:
        scripts_raw = story_repository.find_scripts_by_section_ids(conn, section_ids)
        for sc in scripts_raw:
            section_id = sc["section_id"]
            if section_id not in scripts_by_section:
                scripts_by_section[section_id] = []
            scripts_by_section[section_id].append(sc)

    # 查询所有资产，按 first_section_id 分组
    assets_raw = story_repository.find_assets_by_story_id(conn, story_id)
    assets_by_section = {}
    for a in assets_raw:
        sid = a.get("first_section_id")
        if sid:
            assets_by_section.setdefault(sid, []).append(a)

    volumes = []
    for v in volumes_raw:
        sections = sections_by_volume.get(v["id"], [])
        volume_sections = []
        for s in sections:
            scripts = scripts_by_section.get(s["id"], [])
            section_assets = assets_by_section.get(s["id"], [])
            volume_sections.append(
                VolumeSectionResponse(
                    id=s["id"],
                    story_id=s["story_id"],
                    volume_id=s["volume_id"],
                    section_number=s["section_number"],
                    title=s["title"],
                    summary=s.get("summary"),
                    content=s.get("content"),
                    ending_hook=s.get("ending_hook"),
                    assets=[AssetResponse(**a) for a in section_assets],
                    scripts=[SectionScriptResponse(**sc) for sc in scripts],
                )
            )
        volumes.append(
            VolumeOutlineResponse(
                id=v["id"],
                story_id=v["story_id"],
                volume_number=v["volume_number"],
                title=v["title"],
                summary=v["summary"],
                content=v["content"],
                ending_hook=v["ending_hook"],
                detailed_content=v.get("detailed_content"),
                sections=volume_sections,
            )
        )

    assets = [AssetResponse(**a) for a in assets_raw]

    return StoryDetailResponse(
        id=story["id"],
        user_id=story["user_id"],
        title=story["title"],
        genre=story["genre"],
        style=story["style"],
        synopsis=story["synopsis"],
        full_content=story["full_content"],
        cover_image_path=story["cover_image_path"],
        status=story["status"],
        view_count=story["view_count"],
        like_count=story["like_count"],
        created_at=story["created_at"],
        updated_at=story["updated_at"],
        characters=characters,
        volume_outlines=volumes,
        assets=assets,
    ).model_dump(by_alias=True)


@router.get("/{story_id}")
def get_story_detail(
    story_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """获取漫剧详情（查询主记录 + characters + volume_outlines + sections + scripts + assets）"""
    user_id = current_user["id"]

    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="漫剧不存在或不属于当前用户"
        )

    return success_response(
        _build_story_detail_response(conn, story),
        message="成功获取漫剧详情",
    )


@router.put("/{story_id}")
def update_story(
    story_id: int,
    req: StoryUpdateRequest,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """更新漫剧主记录（只更新非null字段）"""
    user_id = current_user["id"]

    # 1.校验story
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    story_repository.update_story(
        conn, story_id, req.title, req.genre, req.style, req.synopsis
    )

    return get_story_detail(story_id, current_user, conn)


@router.delete("/{story_id}")
def delete_story(
    story_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """物理删除漫剧（级联删除关联数据）"""
    user_id = current_user["id"]

    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="漫剧不存在或不属于当前用户"
        )

    # 标记已删除，防止 RabbitMQ 消费端继续处理该漫剧的消息
    deleted_story_repository.mark_deleted(story_id)
    story_repository.delete_story_by_id(conn, story_id)
    return success_response(data=None, message="删除成功")


@router.post("/generate")
def generate_story(
    req: StoryGenerateRequest,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """生成剧情大纲（异步）"""
    user_id = current_user["id"]

    # 1.校验会话归属
    session = chat_session_repository.find_by_id_and_user_id(
        conn, req.session_id, user_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在或不属于当前用户"
        )

    # 2.创建story记录
    story_id = story_repository.create_story(
        conn,
        user_id,
        f"{req.genre}·{req.style} 漫剧",
        req.genre,
        req.style,
        req.plot,
        "generating",
    )

    # 3. 关联会话与漫剧
    story_repository.update_story_chat_sessions(conn, story_id, req.session_id)

    # 4.投递 RabbitMQ 任务到 aisay.ai.story.request
    task_message = {
        "taskType": TaskType.STORY_OUTLINE_GENERATE,
        "storyId": story_id,
        "userId": user_id,
        "sessionId": req.session_id,
        "genre": req.genre,
        "storyStyle": req.style,
        "plot": req.plot,
    }

    publish_message(
        routing_key=settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
        message_body=json.dumps(task_message, ensure_ascii=False),
    )

    # 5.返回新建的 story 数据
    story = story_repository.find_by_id(conn, story_id)

    return success_response(
        data=StoryResponse(**story).model_dump(by_alias=True), message="任务已提交，正在生成剧情大纲"
    )


# ====== 4.3 修改剧情大纲（异步）=======


@router.post("/{story_id}/outline/revise")
def revise_story_outline(
    story_id: int,
    req: OutlineReviseRequest,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """修改剧情大纲（异步）"""
    user_id = current_user["id"]
    # 1.校验归属
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    # 3.更新状态为revising
    story_repository.update_story_status(conn, story_id, "revising")

    # 4.投递 RabbitMQ 任务
    characters = story_repository.find_characters_by_story_id(conn, story_id)
    task_message = {
        "taskType": TaskType.STORY_OUTLINE_REVISE,
        "storyId": story_id,
        "userId": user_id,
        "title": story["title"] or "",
        "genre": story["genre"] or "",
        "storyStyle": story["style"] or "",
        "storySummary": story["synopsis"] or "",
        "outline": story["full_content"] or "",
        "mainCharacters": [{"name": c["name"], "role": c.get("role", "")} for c in characters],
        "suggestion": req.suggestion,
    }

    publish_message(
        routing_key=settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
        message_body=json.dumps(task_message, ensure_ascii=False),
    )

    # 5.返回最新story
    return get_story_detail(story_id, current_user, conn)


# ====== 4.4 手动保存大纲和角色 ======


@router.put("/{story_id}/detail")
def update_story_detail(
    story_id: int,
    req: StoryDetailUpdateRequest,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """
    手动保存大纲和角色。
    1. 校验 story 存在且属于当前用户
    2. 更新 synopsis 和 full_content
    3. 如有 characters，先删除旧角色，再批量插入新角色
    4. 返回最新 StoryDetailResponse
    """

    user_id = current_user["id"]

    # 1.校验story存在且属于当前用户
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    # 2.更新 synopsis 和 full_content
    story_repository.update_story_detail(conn, story_id, req.synopsis, req.full_content)

    # 3.角色处理
    if req.characters is not None:
        # 删除旧角色
        story_repository.delete_characters_by_story_id(conn, story_id)
        # 批量插入
        if len(req.characters) > 0:
            characters_data = [c.model_dump() for c in req.characters]
            story_repository.batch_insert_characters(conn, story_id, characters_data)

    # 4.返回最新的story数据
    return get_story_detail(story_id, current_user, conn)


# ====== 4.5 分卷大纲生成（异步） ======
@router.post("/{story_id}/volume-outline/generate")
def generate_volume_outline(
    story_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """
    1. 校验story 存在且属于当前用户
    2. 清空旧分卷
    3. 更改 status 为 volume_pending
    4. 投递 RabbitMQ 任务
    5. 返回当前 story
    """

    user_id = current_user["id"]

    # 1.校验归属
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    # 2.更改状态（不删除旧分卷，等新数据生成成功后再清理）
    story_repository.update_story_status(conn, story_id, "generating")

    # 5.投递 RabbitMQ 任务
    characters = story_repository.find_characters_by_story_id(conn, story_id)
    task_message = {
        "taskType": TaskType.VOLUME_OUTLINE_GENERATE,
        "storyId": story_id,
        "userId": user_id,
        "title": story["title"] or "",
        "genre": story["genre"] or "",
        "storyStyle": story["style"] or "",
        "storySummary": story["synopsis"] or "",
        "outline": story["full_content"] or "",
        "mainCharacters": [
            {
                "name": c["name"],
                "role": c.get("role", ""),
                "description": c.get("description", ""),
                "personality": c.get("personality", ""),
            }
            for c in characters
        ],
    }

    publish_message(
        settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
        message_body=json.dumps(task_message, ensure_ascii=False),
    )

    return success_response(
        _build_story_detail_response(conn, story),
        message="分卷大纲生成任务已提交",
    )


# ====== 4.6 分卷大纲自动修改（异步） ======
@router.post("/{story_id}/volume-outline/revise")
def revise_volume_outline(
    story_id: int,
    req: OutlineReviseRequest,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """
    自动修改分卷大纲
    1. 校验 story 存在且属于当前用户
    2. status 改为 volume_revising
    3. 投递 RabbitMQ 任务
    4. 立即返回
    """
    user_id = current_user["id"]

    # 1.校验归属
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    # 3. 检查是否有分卷可修改
    existing_volumes = story_repository.find_volume_outlines_by_story_id(conn, story_id)
    if not existing_volumes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该漫剧还没有分卷大纲，请先生成分卷",
        )

    # 4. 更改状态为 volume_revising
    story_repository.update_story_status(conn, story_id, "volume_revising")

    # 5. 投递 RabbitMQ 任务
    characters = story_repository.find_characters_by_story_id(conn, story_id)
    task_message = {
        "taskType": TaskType.VOLUME_OUTLINE_REVISE,
        "storyId": story_id,
        "userId": user_id,
        "title": story["title"] or "",
        "genre": story["genre"] or "",
        "storyStyle": story["style"] or "",
        "storySummary": story["synopsis"] or "",
        "outline": story["full_content"] or "",
        "mainCharacters": [{"name": c["name"], "role": c.get("role", "")} for c in characters],
        "volumeOutlines": existing_volumes,
        "suggestion": req.suggestion,
    }

    publish_message(
        routing_key=settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
        message_body=json.dumps(task_message, ensure_ascii=False),
    )

    # 6.返回 story
    return get_story_detail(story_id, current_user, conn)


# ====== 4.7 分卷大纲手动修改 ======
@router.put("/{story_id}/volume-outline")
def update_volume_outlines(
    story_id: int,
    req: VolumeOutlineUpdateRequest,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """
    手动修改分卷大纲（整体替换）
    1. 校验归属
    2. 校验状态不能在进行中
    3. 删除旧分卷
    4. 批量插入新分卷
    5. 返回最新 StoryDetailResponse
    """
    user_id = current_user["id"]

    # 1.校验归属
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    # 3.删除旧分卷
    story_repository.delete_volume_outlines_by_story_id(conn, story_id)

    # 4.批量插入分卷
    if req.volume_outlines:
        volumes_data = [v.model_dump() for v in req.volume_outlines]
        story_repository.batch_insert_volume_outlines(conn, story_id, volumes_data)

    return get_story_detail(story_id, current_user, conn)


# ====== 4.8 小节故事生成（异步） ======
@router.post("/{story_id}/volume-outline/{volume_id}/sections/generate")
def generate_volume_sections(
    story_id: int,
    volume_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """
    小节故事生成（异步）
    1. 校验 story 归属
    2. 校验分卷存在
    3. 清空分卷下的旧小节
    4. 更改 status 为 volume_section_pending
    5. 投递 RabbitMQ 任务
    6. 返回 story
    """
    user_id = current_user["id"]

    # 1. 校验归属
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    # 2.校验分卷存在
    volume = story_repository.find_volume_by_id_and_story_id(conn, volume_id, story_id)
    if not volume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="分卷不存在或不属于该漫剧"
        )

    # 3.清空分卷下的旧小节
    story_repository.delete_sections_by_volume_id(conn, volume_id)

    # 4.更改status
    story_repository.update_story_status(conn, story_id, "volume_section_pending")

    # 5.投递 RabbitMQ 任务
    characters = story_repository.find_characters_by_story_id(conn, story_id)
    task_message = {
        "taskType": TaskType.VOLUME_SECTION_GENERATE,
        "storyId": story_id,
        "userId": user_id,
        "volumeId": volume_id,
        "volumeNumber": volume["volume_number"],
        "title": story["title"] or "",
        "genre": story["genre"] or "",
        "storyStyle": story["style"] or "",
        "storySummary": story["synopsis"] or "",
        "outline": story["full_content"] or "",
        "mainCharacters": [
            {
                "name": c["name"],
                "role": c.get("role", ""),
                "description": c.get("description", ""),
                "personality": c.get("personality", ""),
            }
            for c in characters
        ],
        "volumeOutlines": [
            {
                "id": volume["id"],
                "volumeNumber": volume["volume_number"],
                "title": volume["title"],
                "summary": volume.get("summary"),
                "content": volume.get("content"),
                "endingHook": volume.get("ending_hook"),
                "detailedContent": volume.get("detailed_content"),
            }
        ],
    }

    publish_message(
        routing_key=settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
        message_body=json.dumps(task_message, ensure_ascii=False),
    )

    # 6.返回 story
    return get_story_detail(story_id, current_user, conn)


# ====== 分卷正文生成（异步） ======
@router.post("/{story_id}/volume-outline/{volume_id}/story/generate")
def generate_volume_story(
    story_id: int,
    volume_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """
    分卷正文生成（异步）
    """
    user_id = current_user["id"]

    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    volume = story_repository.find_volume_by_id_and_story_id(conn, volume_id, story_id)
    if not volume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="分卷不存在或不属于该漫剧"
        )

    story_repository.update_story_status(conn, story_id, "volume_story_pending")

    characters = story_repository.find_characters_by_story_id(conn, story_id)
    task_message = {
        "taskType": TaskType.VOLUME_STORY_GENERATE,
        "storyId": story_id,
        "userId": user_id,
        "volumeId": volume_id,
        "volumeNumber": volume["volume_number"],
        "volumeTitle": volume["title"],
        "volumeSummary": volume["summary"],
        "volumeContent": volume["content"],
        "volumeEndingHook": volume["ending_hook"],
        "genre": story["genre"] or "",
        "storyStyle": story["style"] or "",
        "synopsis": story["synopsis"] or "",
        "outline": story["full_content"] or "",
        "mainCharacters": [{"name": c["name"], "role": c.get("role", "")} for c in characters],
    }

    publish_message(
        routing_key=settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
        message_body=json.dumps(task_message, ensure_ascii=False),
    )

    return get_story_detail(story_id, current_user, conn)


# ====== 4.9 小节资产图片生成（异步） ======
@router.post("/{story_id}/volume-sections/{section_id}/assets/generate")
def generate_section_assets(
    story_id: int,
    section_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """
    小节资产图片生成（异步）
    1.校验 story 归属及状态
    2.校验小节存在且属于该 story
    3.status 改为 section_asset_pending
    4.投递 RabbitMQ 任务
    5.返回 story
    """
    user_id = current_user["id"]

    # 1.校验归属
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    # 2.校验小节
    section = story_repository.find_section_by_id_and_story_id(
        conn, section_id, story_id
    )
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="小节不存在或不属于该漫剧"
        )

    # 3.更改 status
    story_repository.update_story_status(conn, story_id, "section_asset_pending")

    # 4.获取已有资产
    existing_assets = story_repository.find_assets_by_story_id(conn, story_id)

    # 5.投递 RabbitMQ 任务
    characters = story_repository.find_characters_by_story_id(conn, story_id)
    volume = story_repository.find_volume_by_id_and_story_id(conn, section["volume_id"], story_id)
    task_message = {
        "taskType": TaskType.SECTION_ASSET_GENERATE,
        "storyId": story_id,
        "userId": user_id,
        "volumeId": section["volume_id"],
        "sectionId": section_id,
        "title": story["title"] or "",
        "genre": story["genre"] or "",
        "storyStyle": story["style"] or "",
        "storySummary": story["synopsis"] or "",
        "outline": story["full_content"] or "",
        "mainCharacters": [
            {
                "name": c["name"],
                "role": c.get("role", ""),
                "description": c.get("description", ""),
                "personality": c.get("personality", ""),
            }
            for c in characters
        ],
        "volumeOutlines": [
            {
                "id": volume["id"],
                "volumeNumber": volume["volume_number"],
                "title": volume["title"],
                "summary": volume.get("summary"),
                "content": volume.get("content"),
                "endingHook": volume.get("ending_hook"),
                "detailedContent": volume.get("detailed_content"),
            }
        ],
        "section": {
            "sectionNumber": section["section_number"],
            "title": section["title"],
            "summary": section.get("summary", ""),
            "content": section.get("content", ""),
            "endingHook": section.get("ending_hook", ""),
        },
        "existingAssets": existing_assets,
    }

    publish_message(
        routing_key=settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
        message_body=json.dumps(task_message, ensure_ascii=False, default=str),
    )

    # 6. 返回story
    return get_story_detail(story_id, current_user, conn)


# ====== 4.10 小节分镜脚本生成 (异步) ======
@router.post("/{story_id}/volume-sections/{section_id}/script/generate")
def generate_section_script(
    story_id: int,
    section_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """
    小节分镜脚本生成 (异步)
    1. 校验 story 存在且属于当前用户
    2. 校验小节存在且属于该 story
    3. status 改为 section_script_pending
    4. 投递 RabbitMQ 任务
    5. 立即返回
    """
    user_id = current_user["id"]

    # 1.校验归属
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    # 2.校验小节
    section = story_repository.find_section_by_id_and_story_id(
        conn, section_id, story_id
    )
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="小节不存在或不属于该漫剧"
        )

    # 3.更改 status
    story_repository.update_story_status(conn, story_id, "section_script_pending")

    # 4. 构造 RabbitMQ 任务消息
    characters = story_repository.find_characters_by_story_id(conn, story_id)
    volume = story_repository.find_volume_by_id_and_story_id(conn, section["volume_id"], story_id)
    task_message = {
        "taskType": TaskType.SECTION_SCRIPT_GENERATE,
        "storyId": story_id,
        "userId": user_id,
        "volumeId": section["volume_id"],
        "sectionId": section_id,
        "title": story["title"] or "",
        "genre": story["genre"] or "",
        "storyStyle": story["style"] or "",
        "storySummary": story["synopsis"] or "",
        "outline": story["full_content"] or "",
        "mainCharacters": [
            {
                "name": c["name"],
                "role": c.get("role", ""),
                "description": c.get("description", ""),
                "personality": c.get("personality", ""),
            }
            for c in characters
        ],
        "volumeOutlines": [
            {
                "id": volume["id"],
                "volumeNumber": volume["volume_number"],
                "title": volume["title"],
                "summary": volume.get("summary"),
                "content": volume.get("content"),
                "endingHook": volume.get("ending_hook"),
                "detailedContent": volume.get("detailed_content"),
            }
        ],
        "section": {
            "sectionNumber": section["section_number"],
            "title": section["title"],
            "summary": section.get("summary", ""),
            "content": section.get("content", ""),
            "endingHook": section.get("ending_hook", ""),
        },
    }

    # 5. 投递到 RabbitMQ
    publish_message(
        routing_key=settings.RABBITMQ_ROUTING_KEY_STORY_REQUEST,
        message_body=json.dumps(task_message, ensure_ascii=False, default=str),
    )

    # 6. 返回最新数据
    return get_story_detail(story_id, current_user, conn)


# ====== 4.11 人物音频上传 ======
@router.post("/story/{story_id}/assets/{asset_id}/audio")
def upload_asset_audio(
    story_id: int,
    asset_id: int,
    file: UploadFile = File(
        ..., description="音频文件（支持 mp3, wav, m4a, aac, ogg, flac, wma）"
    ),
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """
    上传人物音频。
    1. 校验 story 存在且属于当前用户
    2. 校验 asset 存在且属于该 story
    3. 保存音频文件
    4. 更新 story_assets.audio_path
    5. 返回成功消息
    """
    user_id = current_user["id"]

    # 1.校验 story
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    check_story(story)

    # 2. 校验 asset
    asset = story_repository.find_asset_by_id_and_story_id(conn, asset_id, story_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="资产不存在或不属于该漫剧"
        )

    # 3.保存文件
    try:
        relative_path = save_upload_file(file, category="character-audio")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}",
        )

    # 4. 如果已有旧音频，删除旧文件
    if asset.get("audio_path"):
        delete_file(asset["audio_path"])

    # 5.更新数据库
    story_repository.update_asset_audio_path(conn, asset_id, relative_path)

    return success_response(
        data={"asset_id": asset_id, "audio_path": relative_path}, message="音频上传成功"
    )


# ====== 导出剧本为 Word 文档 ======
@router.get("/{story_id}/export/docx")
def export_docx(
    story_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """导出漫剧剧本为 Word (.docx) 文件。"""
    user_id = current_user["id"]
    story = story_repository.find_by_id_and_user_id(conn, story_id, user_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="漫剧不存在或不属于当前用户"
        )

    buf = export_story_docx(story_id)
    filename = f"{story.get('title') or '漫剧剧本'}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
