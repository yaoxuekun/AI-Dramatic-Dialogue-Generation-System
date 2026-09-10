from typing import List, Dict, Any
from pymysql.connections import Connection


def insert_message(
    conn: Connection, session_id: int, role: str, content: str, metadata: dict = None
) -> int:
    """插入消息，返回 message_id"""
    import json

    cur = conn.cursor()
    cur.execute(
        """
        insert into messages (session_id,role,content,metadata,created_at)
        values (%s, %s, %s, %s, NOW())
        """,
        (session_id, role, content, json.dumps(metadata or {})),
    )
    conn.commit()
    return cur.lastrowid


def find_by_session(
    conn: Connection, session_id, limit: int = None
) -> List[Dict[str, Any]]:
    """获取会话的所有消息，按创建时间升序，可用limit限制查询条数"""
    cur = conn.cursor()
    sql = "select * from messages where session_id = %s order by created_at"
    if limit:
        sql += f"limit {limit}"
    cur.execute(
        sql,
        (session_id,),
    )
    return cur.fetchall()
