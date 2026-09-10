from typing import Optional, List, Dict, Any
import uuid  # 用于生成唯一标识符
from datetime import datetime
from pymysql.connections import Connection


def create_session(
    conn: Connection,
    user_id: int,
    title: Optional[str] = None,
    story_id: Optional[int] = None,
) -> int:
    """创建新对话，返回 session_id"""
    session_key = str(uuid.uuid4())
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO chat_sessions 
           (user_id, session_key, title, status, current_stage, progress_percentage, story_id, started_at, last_active) 
           VALUES (%s, %s, %s, 'active', 'INITIAL', 0, %s, NOW(), NOW())""",
        (user_id, session_key, title or "新对话", story_id),
    )
    conn.commit()
    return cur.lastrowid


def find_by_id(
    conn: Connection, session_id: int, user_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """根据session_id查询，若user_id不为空则校验归属"""
    cur = conn.cursor()
    
    sql = "SELECT * FROM chat_sessions WHERE id = %s AND status != 'deleted'"
    params = [session_id]
    
    if user_id is not None:
        sql += " AND user_id = %s"
        params.append(user_id)
    
    cur.execute(sql, params)
    return cur.fetchone()


def find_by_user(conn: Connection, user_id: int) -> List[Dict[str, Any]]:
    """获取用户所有活跃对话，按 last_active 倒序"""
    cur = conn.cursor()
    cur.execute(
        """
        select * from chat_sessions where status != 'deleted' and user_id = %s order by last_active desc, id desc
        """,
        (user_id,),
    )
    return cur.fetchall()


def soft_delete(conn: Connection, session_id: int, user_id: int) -> bool:
    """软删除，返回是否成功"""
    cur = conn.cursor()
    cur.execute(
        """
        update chat_sessions set status='deleted',last_active = NOW() where id = %s and user_id = %s and status != 'deleted'
        """,
        (
            session_id,
            user_id,
        ),
    )
    conn.commit()
    return cur.rowcount > 0


def update_last_active(conn: Connection, session_id: int) -> None:
    """更新最后活跃时间"""
    cur = conn.cursor()
    cur.execute(
        """
        update chat_sessions set last_active = NOW() where id = %s
        """,
        (session_id,),
    )
    conn.commit()


def find_by_id_and_user_id(
    conn: Connection, session_id: int, user_id: int
) -> Optional[Dict[str, Any]]:
    """根据会话ID和用户ID查询对话（校验归属）"""
    cur = conn.cursor()
    cur.execute(
        """
        select id,user_id,session_key,title,story_id,status,current_stage,progress_percentage
        from chat_sessions
        where id = %s and user_id = %s and status != 'deleted'
        """,
        (session_id, user_id),
    )
    return cur.fetchone()
