from typing import Optional, List, Dict, Any
from pymysql.connections import Connection
from datetime import datetime


def find_all(
    conn: Connection,
    option_type: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """查询大纲配置列表，可按类型和启用状态筛选"""
    sql = "SELECT id, option_type, name, description, sort_order, enabled, created_at, updated_at FROM story_outline_options WHERE 1=1"
    params = []

    if option_type is not None:
        sql += " AND option_type = %s"
        params.append(option_type)

    if enabled is not None:
        sql += " AND enabled = %s"
        params.append(enabled)

    sql += " ORDER BY sort_order ASC, id ASC"

    cur = conn.cursor()
    cur.execute(sql, params)
    return cur.fetchall()


def find_by_id(conn: Connection, option_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 查询单个配置"""
    cur = conn.cursor()
    cur.execute(
        "SELECT id, option_type, name, description, sort_order, enabled, created_at, updated_at FROM story_outline_options WHERE id = %s",
        (option_id,),
    )
    return cur.fetchone()


def find_by_type_and_name(
    conn: Connection, option_type: str, name: str
) -> Optional[Dict[str, Any]]:
    """根据类型和名称查询（用于唯一性校验）"""
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM story_outline_options WHERE option_type = %s AND name = %s",
        (option_type, name),
    )
    return cur.fetchone()


def create(
    conn: Connection,
    option_type: str,
    name: str,
    description: Optional[str],
    sort_order: int,
    enabled: bool,
) -> int:
    """新增配置，返回新记录 ID"""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO story_outline_options (option_type, name, description, sort_order, enabled, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (option_type, name, description, sort_order, enabled, datetime.now(), datetime.now()),
    )
    conn.commit()
    return cur.lastrowid


def update(
    conn: Connection,
    option_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    sort_order: Optional[int] = None,
    enabled: Optional[bool] = None,
) -> None:
    """修改配置（只更新非 None 字段）"""
    updates = []
    params = []

    if name is not None:
        updates.append("name = %s")
        params.append(name)
    if description is not None:
        updates.append("description = %s")
        params.append(description)
    if sort_order is not None:
        updates.append("sort_order = %s")
        params.append(sort_order)
    if enabled is not None:
        updates.append("enabled = %s")
        params.append(enabled)

    if not updates:
        return

    updates.append("updated_at = %s")
    params.append(datetime.now())
    params.append(option_id)

    cur = conn.cursor()
    cur.execute(
        f"UPDATE story_outline_options SET {','.join(updates)} WHERE id = %s",
        params,
    )
    conn.commit()


def delete_by_id(conn: Connection, option_id: int) -> bool:
    """删除配置，返回是否成功"""
    cur = conn.cursor()
    cur.execute("DELETE FROM story_outline_options WHERE id = %s", (option_id,))
    conn.commit()
    return cur.rowcount > 0
