from typing import Optional, List, Dict, Any
from pymysql.connections import Connection
from datetime import datetime


PROMPT_COLUMNS = (
    "id, prompt_key, base_prompt_key, prompt_scope, match_genre, match_style, priority, "
    "prompt_name, category, description, template_content, enabled, created_at, updated_at"
)

PARAM_COLUMNS = (
    "id, prompt_id, direction, param_key, param_name, data_type, required_flag, "
    "description, example_value, sort_order, created_at, updated_at"
)


def find_all(conn: Connection) -> List[Dict[str, Any]]:
    """查询所有 Prompt（含参数列表）"""
    cur = conn.cursor()
    cur.execute(f"SELECT {PROMPT_COLUMNS} FROM ai_prompts ORDER BY category ASC, id ASC")
    prompts = cur.fetchall()

    if not prompts:
        return []

    cur.execute(f"SELECT {PARAM_COLUMNS} FROM ai_prompt_parameters ORDER BY prompt_id ASC, sort_order ASC, id ASC")
    params = cur.fetchall()

    param_map: Dict[int, list] = {}
    for p in params:
        param_map.setdefault(p["prompt_id"], []).append(p)

    for prompt in prompts:
        prompt["parameters"] = param_map.get(prompt["id"], [])

    return prompts


def find_by_id(conn: Connection, prompt_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 查询单个 Prompt（含参数列表）"""
    cur = conn.cursor()
    cur.execute(f"SELECT {PROMPT_COLUMNS} FROM ai_prompts WHERE id = %s", (prompt_id,))
    prompt = cur.fetchone()
    if not prompt:
        return None

    cur.execute(
        f"SELECT {PARAM_COLUMNS} FROM ai_prompt_parameters WHERE prompt_id = %s ORDER BY sort_order ASC, id ASC",
        (prompt_id,),
    )
    prompt["parameters"] = cur.fetchall()
    return prompt


def find_by_prompt_key(conn: Connection, prompt_key: str) -> Optional[Dict[str, Any]]:
    """根据 prompt_key 查询（用于唯一性校验）"""
    cur = conn.cursor()
    cur.execute("SELECT id FROM ai_prompts WHERE prompt_key = %s", (prompt_key,))
    return cur.fetchone()


def create(
    conn: Connection,
    prompt_key: str,
    name: str,
    category: Optional[str],
    description: Optional[str],
    template_content: str,
    enabled: bool,
    parameters: List[Dict[str, Any]],
    base_prompt_key: Optional[str],
    prompt_scope: Optional[str],
    match_genre: Optional[str],
    match_style: Optional[str],
    priority: int,
) -> int:
    """新增 Prompt 和参数，返回新记录 ID"""
    now = datetime.now()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO ai_prompts
           (prompt_key, base_prompt_key, prompt_scope, match_genre, match_style, priority,
            prompt_name, category, description, template_content, enabled, created_at, updated_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            prompt_key,
            base_prompt_key or prompt_key,
            prompt_scope or "DEFAULT",
            match_genre,
            match_style,
            priority,
            name,
            category,
            description,
            template_content,
            enabled,
            now,
            now,
        ),
    )
    prompt_id = cur.lastrowid

    for param in parameters:
        cur.execute(
            """INSERT INTO ai_prompt_parameters
               (prompt_id, direction, param_key, param_name, data_type, required_flag,
                description, example_value, sort_order, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                prompt_id,
                param["direction"],
                param["param_key"],
                param["param_name"],
                param["data_type"],
                param.get("required_flag", True),
                param.get("description"),
                param.get("example_value"),
                param.get("sort_order", 0),
                now,
                now,
            ),
        )

    conn.commit()
    return prompt_id


def update(
    conn: Connection,
    prompt_id: int,
    name: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    template_content: Optional[str] = None,
    enabled: Optional[bool] = None,
    parameters: Optional[List[Dict[str, Any]]] = None,
    base_prompt_key: Optional[str] = None,
    prompt_scope: Optional[str] = None,
    match_genre: Optional[str] = None,
    match_style: Optional[str] = None,
    priority: Optional[int] = None,
) -> None:
    """修改 Prompt（只更新非 None 字段），若提供 parameters 则整体替换"""
    updates = []
    params = []

    if name is not None:
        updates.append("prompt_name = %s")
        params.append(name)
    if category is not None:
        updates.append("category = %s")
        params.append(category)
    if description is not None:
        updates.append("description = %s")
        params.append(description)
    if template_content is not None:
        updates.append("template_content = %s")
        params.append(template_content)
    if enabled is not None:
        updates.append("enabled = %s")
        params.append(enabled)
    if base_prompt_key is not None:
        updates.append("base_prompt_key = %s")
        params.append(base_prompt_key)
    if prompt_scope is not None:
        updates.append("prompt_scope = %s")
        params.append(prompt_scope)
    if match_genre is not None:
        updates.append("match_genre = %s")
        params.append(match_genre)
    if match_style is not None:
        updates.append("match_style = %s")
        params.append(match_style)
    if priority is not None:
        updates.append("priority = %s")
        params.append(priority)

    cur = conn.cursor()

    if updates:
        updates.append("updated_at = %s")
        params.append(datetime.now())
        params.append(prompt_id)
        cur.execute(
            f"UPDATE ai_prompts SET {','.join(updates)} WHERE id = %s",
            params,
        )

    if parameters is not None:
        now = datetime.now()
        cur.execute("DELETE FROM ai_prompt_parameters WHERE prompt_id = %s", (prompt_id,))
        for param in parameters:
            cur.execute(
                """INSERT INTO ai_prompt_parameters
                   (prompt_id, direction, param_key, param_name, data_type, required_flag,
                    description, example_value, sort_order, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    prompt_id,
                    param["direction"],
                    param["param_key"],
                    param["param_name"],
                    param["data_type"],
                    param.get("required_flag", True),
                    param.get("description"),
                    param.get("example_value"),
                    param.get("sort_order", 0),
                    now,
                    now,
                ),
            )

    conn.commit()


def delete_by_id(conn: Connection, prompt_id: int) -> bool:
    """删除 Prompt（级联删除关联参数），返回是否成功"""
    cur = conn.cursor()
    cur.execute("DELETE FROM ai_prompts WHERE id = %s", (prompt_id,))
    conn.commit()
    return cur.rowcount > 0
