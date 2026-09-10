from typing import Optional, List, Dict, Any
from pymysql.connections import Connection
from datetime import datetime


def find_all(conn: Connection) -> List[Dict[str, Any]]:
    """查询所有功能权限列表"""
    cur = conn.cursor()
    cur.execute(
        "SELECT id, feature_key, feature_name, category, description, allowed_roles, enabled, sort_order, created_at, updated_at "
        "FROM feature_permissions ORDER BY sort_order ASC, id ASC"
    )
    return cur.fetchall()


def find_by_id(conn: Connection, permission_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 查询单条功能权限"""
    cur = conn.cursor()
    cur.execute(
        "SELECT id, feature_key, feature_name, category, description, allowed_roles, enabled, sort_order, created_at, updated_at "
        "FROM feature_permissions WHERE id = %s",
        (permission_id,),
    )
    return cur.fetchone()


def find_enabled_keys_by_role(conn: Connection, role: str) -> List[str]:
    """查询指定角色可用的已启用功能 key 列表"""
    cur = conn.cursor()
    cur.execute(
        "SELECT feature_key FROM feature_permissions "
        "WHERE enabled = 1 AND FIND_IN_SET(%s, REPLACE(allowed_roles, ' ', '')) > 0 "
        "ORDER BY sort_order ASC, id ASC",
        (role,),
    )
    rows = cur.fetchall()
    return [row["feature_key"] for row in rows]


def update(
    conn: Connection,
    permission_id: int,
    allowed_roles: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> None:
    """修改功能权限（只更新非 None 字段）"""
    updates = []
    params = []

    if allowed_roles is not None:
        updates.append("allowed_roles = %s")
        params.append(allowed_roles)
    if enabled is not None:
        updates.append("enabled = %s")
        params.append(enabled)

    if not updates:
        return

    updates.append("updated_at = %s")
    params.append(datetime.now())
    params.append(permission_id)

    cur = conn.cursor()
    cur.execute(
        f"UPDATE feature_permissions SET {','.join(updates)} WHERE id = %s",
        params,
    )
    conn.commit()
