from pymysql.connections import Connection
from datetime import datetime
from typing import Optional, Dict, Any


def find_by_username(conn: Connection, username: str) -> Optional[Dict[str, Any]]:
    """根据用户名查询用户（包含哈希密码）"""
    cursor = conn.cursor()
    cursor.execute(
        """
        select id,username,email,password_hash,avatar_path,role,created_at
        from users
        where username=%s and role !='deleted'
        """,
        (username,),
    )
    return cursor.fetchone()


def find_by_email(conn: Connection, email: str) -> Optional[Dict[str, Any]]:
    """根据邮箱查询用户"""
    cursor = conn.cursor()
    cursor.execute(
        "select id from users where email=%s and role != 'deleted'", (email,)
    )
    return cursor.fetchone()


def find_by_id(conn: Connection, user_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 查询用户（不含哈希密码）"""
    cursor = conn.cursor()
    cursor.execute(
        """
        select id,username,email,avatar_path,role,created_at
        from users
        where id = %s and role != 'deleted'
        """,
        (user_id,),
    )
    return cursor.fetchone()


def create_user(conn: Connection, username: str, email: str, password_hash: str) -> int:
    """创建新用户，返回用户 ID"""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users(username,email,password_hash,role,created_at)
        values(%s, %s, %s, %s, %s)
        """,
        (username, email, password_hash, "USER", datetime.now()),
    )
    conn.commit()
    return cursor.lastrowid


def update_user_profile(
    conn: Connection,
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    avatar_path: Optional[str] = None,
) -> None:
    """更新用户资料（只更新非 None 字段）"""
    updates = []
    params = []

    if username:
        updates.append("username = %s")
        params.append(username)

    if email:
        updates.append("email = %s")
        params.append(email)

    if avatar_path:
        updates.append("avatar_path = %s")
        params.append(avatar_path)

    if not updates:
        return

    params.append(user_id)
    sql = f"update users set {','.join(updates)} where id = %s"
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()


def check_username_exists_excluding_user(
    conn: Connection, username: str, user_id: int
) -> bool:
    """
    检查用户名是否被其他用户占用（更新资料时使用）
    :return: True表示已占用，False表示未占用
    """
    cursor = conn.cursor()
    cursor.execute(
        "select id from users where username = %s and user_id != %s and role != 'deleted'",
        (username, user_id),
    )
    return cursor.fetchone() is not None

def check_email_exists_excluding_user(conn: Connection, email: str, user_id: int) -> bool:
    """检查邮箱是否被其他用户占用"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE email = %s AND id != %s AND role != 'deleted'",
        (email, user_id)
    )
    return cursor.fetchone() is not None


def find_all_users(conn: Connection) -> list:
    """查询所有用户（管理后台用）"""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, username, email, avatar_path, role, created_at
        FROM users
        WHERE role != 'deleted'
        ORDER BY id DESC
        """
    )
    return cursor.fetchall()


def update_user_role(conn: Connection, user_id: int, new_role: str) -> None:
    """更新用户角色"""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET role = %s WHERE id = %s",
        (new_role, user_id)
    )
    conn.commit()