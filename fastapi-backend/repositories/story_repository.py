from typing import Optional, List, Dict, Any
from datetime import datetime
from pymysql.connections import Connection


# insert
def create_story(
    conn: Connection,
    user_id: int,
    title: Optional[str] = None,
    genre: Optional[str] = None,
    style: Optional[str] = None,
    synopsis: Optional[str] = None,
    status: str = "draft",
) -> int:
    """创建漫剧，返回 story_id"""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO stories (user_id, title, genre, style, synopsis, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            title,
            genre,
            style,
            synopsis,
            status,
            datetime.now(),
            datetime.now(),
        ),
    )
    conn.commit()
    return cur.lastrowid


def batch_insert_characters(
    conn: Connection, story_id: int, characters: List[Dict[str, Any]]
) -> None:
    """
    批量插入角色
    characters 列表中的字典需包含：name,role_position,description,personality,appearance
    """
    if not characters:
        return

    sql = """
        insert into characters(story_id,name,role,description,personality,appearance)
        values (%s, %s, %s, %s, %s, %s)
        """
    values = [
        (
            story_id,
            c["name"],
            c["role_position"],
            c["description"],
            c["personality"],
            c["appearance"],
        )
        for c in characters
    ]

    cur = conn.cursor()
    cur.executemany(sql, values)
    conn.commit()


def batch_insert_volume_outlines(
    conn: Connection, story_id: int, volumes: List[Dict[str, Any]]
) -> List[int]:
    """
    批量插入分卷大纲，返回插入的分卷 ID 列表
    volumes 列表中的字典包括： volume_number, title, summary, content, ending_hook, detailed_content
    """
    if not volumes:
        return []
    cur = conn.cursor()
    sql = """
        insert into story_volume_outlines
        (story_id, volume_number, title, summary, content, ending_hook, detailed_content, created_at, updated_at)
        values(%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    values = []
    for v in volumes:
        values.append(
            (
                story_id,
                v["volume_number"],
                v["title"],
                v.get("summary"),
                v.get("content"),
                v.get("ending_hook"),
                v.get("detailed_content"),
                datetime.now(),
                datetime.now(),
            )
        )
    cur.executemany(sql, values)
    conn.commit()

    cur.execute(
        "select id from story_volume_outlines where story_id = %s order by volume_number",
        (story_id,),
    )
    result = cur.fetchall()
    return [r["id"] for r in result]


# select
def count_by_user_id(conn: Connection, user_id: int) -> int:
    """统计用户的漫剧总数"""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM stories WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    return result["total"] if result else 0


def find_by_user_id_paginated(
    conn: Connection, user_id: int, offset: int, limit: int
) -> List[Dict[str, Any]]:
    """分页查询用户的漫剧列表"""
    cur = conn.cursor()
    cur.execute(
        """
        select id,user_id,title,genre,style,synopsis,cover_image_path,status,view_count,like_count,created_at,updated_at
        from stories 
        where user_id = %s
        order by updated_at desc, id desc
        limit %s offset %s
        """,
        (user_id, limit, offset),
    )
    return cur.fetchall()


def find_by_id(conn: Connection, story_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 查询漫剧主记录"""

    cur = conn.cursor()
    cur.execute(
        """
        select id, user_id, title, genre, style, synopsis, full_content, cover_image_path, status, view_count, 
        like_count, created_at, updated_at
        from stories
        where id = %s
        """,
        (story_id,),
    )
    return cur.fetchone()


def find_by_id_and_user_id(
    conn: Connection, story_id: int, user_id: int
) -> Optional[Dict[str, Any]]:
    """根据 ID 和用户 ID 查询漫剧（用于权限校验）"""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, user_id, title, genre, style, synopsis, full_content, cover_image_path, status,
               view_count, like_count, created_at, updated_at
        FROM stories
        WHERE id = %s AND user_id = %s
        """,
        (story_id, user_id),
    )
    return cursor.fetchone()


# 关联数据查询
def find_characters_by_story_id(
    conn: Connection, story_id: int
) -> List[Dict[str, Any]]:
    """查询漫剧的所有角色"""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, story_id, name, role AS role_position, description, personality, appearance
        FROM characters
        WHERE story_id = %s
        ORDER BY id
        """,
        (story_id,),
    )
    return cursor.fetchall()


def find_volume_outlines_by_story_id(
    conn: Connection, story_id: int
) -> List[Dict[str, Any]]:
    """查询漫剧的所有分卷大纲"""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, story_id, volume_number, title, summary, content, ending_hook, detailed_content
        FROM story_volume_outlines
        WHERE story_id = %s
        ORDER BY volume_number
        """,
        (story_id,),
    )
    return cursor.fetchall()


def find_volume_by_id_and_story_id(
    conn: Connection, volume_id: int, story_id: int
) -> Optional[Dict[str, Any]]:
    """根据分卷 ID 和 story ID 查询分卷"""
    cur = conn.cursor()
    cur.execute(
        """
        select id, story_id, volume_number, title, summary, content, ending_hook, detailed_content
        from story_volume_outlines
        where id = %s and story_id = %s
        """,
        (volume_id, story_id),
    )
    return cur.fetchone()


def find_sections_by_volume_ids(
    conn: Connection, volume_ids: List[int]
) -> List[Dict[str, Any]]:
    """根据分卷ID列表查询小节"""
    if not volume_ids:
        return []
    placeholders = ",".join(["%s"] * len(volume_ids))
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT id, story_id, volume_id, section_number, title, summary, content, ending_hook
        FROM story_volume_sections
        WHERE volume_id IN ({placeholders})
        ORDER BY volume_id, section_number
        """,
        volume_ids,
    )
    return cursor.fetchall()


def find_scripts_by_section_ids(
    conn: Connection, section_ids: List[int]
) -> List[Dict[str, Any]]:
    """根据小节ID列表查询分镜脚本"""
    if not section_ids:
        return []
    placeholders = ",".join(["%s"] * len(section_ids))
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT id, story_id, section_id, shot_number, duration_seconds, shot_type,
               camera_movement, action, dialogue
        FROM story_section_scripts
        WHERE section_id IN ({placeholders})
        ORDER BY section_id, shot_number
        """,
        section_ids,
    )
    return cursor.fetchall()


def find_assets_by_story_id(conn: Connection, story_id: int) -> List[Dict[str, Any]]:
    """查询漫剧的所有资产"""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, story_id, asset_type, name, description, image_prompt, image_path, audio_path
        FROM story_assets
        WHERE story_id = %s
        ORDER BY id
        """,
        (story_id,),
    )
    return cursor.fetchall()


def find_section_by_id_and_story_id(
    conn: Connection, section_id: int, story_id: int
) -> Optional[Dict[str, Any]]:
    """
    根据小节 ID 和 story ID 查询小节
    """
    cur = conn.cursor()
    cur.execute(
        """
        select s.id,s.story_id,s.volume_id,s.title,s.summary,s.content,s.ending_hook,
        v.volume_number,v.title as volume_title 
        from story_volume_sections s
        left join story_volume_outlines v on s.volume_id=v.id
        where s.id = %s and s.story_id = %s
        """,
        (section_id, story_id),
    )
    return cur.fetchone()


def find_existing_assets_for_story(
    conn: Connection, story_id: int
) -> List[Dict[str, Any]]:
    """查询漫剧的已有资产（用于 AI 复用判断）"""
    cur = conn.cursor()
    cur.execute(
        """
        select id,asset_type,name,description,image_prompt,image_path
        from story_assets
        where story_id=%s
        """,
        (story_id,),
    )
    return cur.fetchall()


def find_asset_by_id_and_story_id(
    conn: Connection, asset_id: int, story_id: int
) -> Optional[Dict[str, Any]]:
    """根据 asset ID 和 story ID 查询资产（用于校验归属）"""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, story_id, asset_type, name, description, image_prompt, image_path, audio_path
        FROM story_assets
        WHERE id = %s AND story_id = %s
        """,
        (asset_id, story_id),
    )
    return cursor.fetchone()


# update
def update_story(
    conn: Connection,
    story_id: int,
    title: Optional[str] = None,
    genre: Optional[str] = None,
    style: Optional[str] = None,
    synopsis: Optional[str] = None,
) -> None:
    updates = []
    params = []

    if title is not None:
        updates.append("title = %s")
        params.append(title)

    if genre is not None:
        updates.append("genre = %s")
        params.append(genre)

    if style is not None:
        updates.append("style = %s")
        params.append(style)

    if synopsis is not None:
        updates.append("synopsis = %s")
        params.append(synopsis)

    if not updates:
        return

    updates.append("updated_at = %s")
    params.append(datetime.now())
    params.append(story_id)

    cur = conn.cursor()
    cur.execute(
        f"""
        update stories set {",".join(updates)}
        where id = %s
        """,
        params,
    )
    conn.commit()


def update_story_status(conn: Connection, story_id: int, status: str) -> None:
    """更新漫剧状态"""
    cur = conn.cursor()
    cur.execute(
        "update stories set status = %s, updated_at = %s where id = %s",
        (status, datetime.now(), story_id),
    )
    conn.commit()


def update_story_chat_sessions(
    conn: Connection, story_id: int, session_id: int
) -> None:
    """更新 chat_sessions 的 story_id 字段，关联会话与漫剧"""
    cur = conn.cursor()
    cur.execute(
        """
        update chat_sessions set story_id = %s where id = %s
        """,
        (story_id, session_id),
    )
    conn.commit()


def update_story_detail(
    conn: Connection,
    story_id: int,
    synopsis: Optional[str] = None,
    full_content: Optional[str] = None,
) -> None:
    """更新故事摘要和完整大纲"""
    updates = []
    params = []

    if synopsis is not None:
        updates.append("synopsis = %s")
        params.append(synopsis)
    if full_content is not None:
        updates.append("full_content = %s")
        params.append(full_content)

    if not updates:
        return

    updates.append("updated_at = %s")
    params.append(datetime.now())
    params.append(story_id)

    cur = conn.cursor()
    cur.execute(
        f"""
        update stories set {",".join(updates)} where id = %s
        """,
        params,
    )
    conn.commit()


def update_asset_audio_path(conn: Connection, asset_id: int, audio_path: str) -> None:
    """更新资产的音频路径"""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE story_assets SET audio_path = %s, updated_at = %s WHERE id = %s",
        (audio_path, datetime.now(), asset_id),
    )
    conn.commit()


# delete
def delete_story_by_id(conn: Connection, story_id: int) -> None:
    """物理删除漫剧（外键级联删除关联数据）"""
    cur = conn.cursor()
    cur.execute(
        "delete from stories where id = %s",
        (story_id,),
    )
    conn.commit()


def delete_characters_by_story_id(conn: Connection, story_id: int) -> None:
    """删除漫剧的所有角色"""
    cur = conn.cursor()
    cur.execute(
        """
        delete from characters where story_id = %s
        """,
        (story_id,),
    )
    conn.commit()


def delete_volume_outlines_by_story_id(conn: Connection, story_id: int) -> None:
    """
    删除漫剧的所有分卷大纲（级联删除小节和脚本）
    由于数据库外键设置了 ON DELETE CASCADE，删除分卷时会自动删除关联的小节和脚本，无需额外操作
    """
    cur = conn.cursor()
    cur.execute(
        """
        delete from story_volume_outlines where story_id = %s
        """,
        (story_id,),
    )
    conn.commit()


def delete_sections_by_volume_id(conn: Connection, volume_id: int) -> None:
    """
    删除指定分卷下的小节（级联删除脚本和资产关联）
    """
    cur = conn.cursor()
    cur.execute(
        "delete from story_volume_sections where volume_id = %s",
        (volume_id,),
    )
    conn.commit()


# ── 结果落库专用函数（RabbitMQ 消费者调用）─────────────────────────


def save_story_outline(
    conn: Connection,
    story_id: int,
    title: Optional[str],
    synopsis: Optional[str],
    outline: Optional[str],
    characters: Optional[List[Dict[str, Any]]],
) -> None:
    """保存剧情大纲结果：更新 stories 表 + 替换角色"""
    cur = conn.cursor()

    # 1. 更新 stories 基本信息
    updates = []
    params = []
    if title is not None:
        updates.append("title = %s")
        params.append(title)
    if synopsis is not None:
        updates.append("synopsis = %s")
        params.append(synopsis)
    if outline is not None:
        updates.append("full_content = %s")
        params.append(outline)
    if updates:
        updates.append("updated_at = %s")
        params.append(datetime.now())
        params.append(story_id)
        cur.execute(f"UPDATE stories SET {','.join(updates)} WHERE id = %s", params)

    # 2. 替换角色
    if characters is not None:
        cur.execute("DELETE FROM characters WHERE story_id = %s", (story_id,))
        for c in characters:
            cur.execute(
                """INSERT INTO characters (story_id, name, role, description, personality, appearance)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    story_id,
                    c.get("name", ""),
                    c.get("role_position") or c.get("role", ""),
                    c.get("description", ""),
                    c.get("personality", ""),
                    c.get("appearance", ""),
                ),
            )

    conn.commit()


def upsert_volume_outline(
    conn: Connection,
    story_id: int,
    volume_number: int,
    title: str,
    summary: Optional[str] = None,
    content: Optional[str] = None,
    ending_hook: Optional[str] = None,
) -> None:
    """插入或更新单个分卷大纲（按 story_id + volume_number 唯一）"""
    cur = conn.cursor()
    now = datetime.now()
    cur.execute(
        """INSERT INTO story_volume_outlines
               (story_id, volume_number, title, summary, content, ending_hook, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
               title = VALUES(title), summary = VALUES(summary),
               content = VALUES(content), ending_hook = VALUES(ending_hook),
               updated_at = VALUES(updated_at)""",
        (story_id, volume_number, title, summary, content, ending_hook, now, now),
    )
    conn.commit()


def upsert_volume_section(
    conn: Connection,
    story_id: int,
    volume_id: int,
    section_number: int,
    title: str,
    summary: Optional[str] = None,
    content: Optional[str] = None,
    ending_hook: Optional[str] = None,
) -> None:
    """插入或更新单个小节（按 volume_id + section_number 唯一）"""
    cur = conn.cursor()
    now = datetime.now()
    cur.execute(
        """INSERT INTO story_volume_sections
               (story_id, volume_id, section_number, title, summary, content, ending_hook, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
               title = VALUES(title), summary = VALUES(summary),
               content = VALUES(content), ending_hook = VALUES(ending_hook),
               updated_at = VALUES(updated_at)""",
        (story_id, volume_id, section_number, title, summary, content, ending_hook, now, now),
    )
    conn.commit()


def save_section_assets(
    conn: Connection,
    story_id: int,
    section_id: int,
    characters: List[Dict[str, Any]],
    scenes: List[Dict[str, Any]],
) -> None:
    """保存小节资产结果：更新已有资产或插入新资产 + 关联到小节"""
    cur = conn.cursor()
    now = datetime.now()

    def _save_one_asset(asset_type: str, item: Dict[str, Any]) -> None:
        name = item.get("name", "")
        matched = item.get("matchedExistingName")
        image_prompt = item.get("imagePrompt", "")
        description = item.get("description", "")

        if matched:
            # 更新已有资产的 image_prompt
            cur.execute(
                "UPDATE story_assets SET image_prompt = %s, updated_at = %s "
                "WHERE story_id = %s AND asset_type = %s AND name = %s",
                (image_prompt, now, story_id, asset_type, matched),
            )
            # 获取已有资产 ID 并关联到当前小节
            cur.execute(
                "SELECT id FROM story_assets WHERE story_id = %s AND asset_type = %s AND name = %s",
                (story_id, asset_type, matched),
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    "INSERT IGNORE INTO story_section_assets (story_id, section_id, asset_id) VALUES (%s, %s, %s)",
                    (story_id, section_id, row["id"]),
                )
        else:
            # 插入新资产
            cur.execute(
                """INSERT INTO story_assets
                   (story_id, asset_type, name, description, image_prompt, first_section_id, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (story_id, asset_type, name, description, image_prompt, section_id, now, now),
            )
            asset_id = cur.lastrowid
            # 关联到当前小节
            cur.execute(
                "INSERT IGNORE INTO story_section_assets (story_id, section_id, asset_id) VALUES (%s, %s, %s)",
                (story_id, section_id, asset_id),
            )

    for c in characters:
        _save_one_asset("CHARACTER", c)

    for s in scenes:
        _save_one_asset("SCENE", s)

    conn.commit()


def replace_section_scripts(
    conn: Connection,
    story_id: int,
    section_id: int,
    shots: List[Dict[str, Any]],
) -> None:
    """保存小节分镜脚本：删除旧脚本后重新插入"""
    cur = conn.cursor()
    cur.execute("DELETE FROM story_section_scripts WHERE section_id = %s", (section_id,))
    now = datetime.now()
    for shot in shots:
        cur.execute(
            """INSERT INTO story_section_scripts
               (story_id, section_id, shot_number, duration_seconds, shot_type, camera_movement, action, dialogue, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                story_id,
                section_id,
                shot.get("shotNumber", 0),
                shot.get("durationSeconds", 0),
                shot.get("shotType", ""),
                shot.get("cameraMovement", ""),
                shot.get("action", ""),
                shot.get("dialogue", ""),
                now,
                now,
            ),
        )
    conn.commit()
