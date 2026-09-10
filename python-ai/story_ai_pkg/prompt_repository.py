# Read-only MySQL-backed prompt repository.
# Python only reads prompt templates from the Java-managed MySQL table at runtime.
# Create/update/delete management stays in the Java backend.

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

import yaml
from langchain_core.prompts import PromptTemplate


_CACHE_TTL_SECONDS = 30
_prompt_cache: dict[str, tuple[float, str]] = {}


def load_prompt_content(
    prompt_key: str,
    fallback_content: str,
    *,
    genre: str | None = None,
    story_style: str | None = None,
) -> str:
    """Load a prompt template from MySQL by key, falling back to prompt.py.

    Args:
        prompt_key:        Stable base prompt key, such as "generate_story_outline".
        fallback_content:  Existing prompt.py content used when DB is unavailable.
        genre:             Optional story genre used to find a specific prompt.
        story_style:       Optional story style used to find a specific prompt.

    Returns:
        str: Enabled prompt template content.
    """
    cache_key = build_prompt_cache_key(prompt_key, genre, story_style)
    cached = _prompt_cache.get(cache_key)
    now = time.monotonic()
    if cached and now - cached[0] <= _CACHE_TTL_SECONDS:
        return cached[1]

    try:
        content = _load_prompt_content_from_mysql(prompt_key, genre, story_style)
    except Exception as exc:
        print(f"[prompt-repository] fallback to prompt.py for {prompt_key}: {exc}")
        content = fallback_content

    if not content or not content.strip():
        content = fallback_content

    _prompt_cache[cache_key] = (now, content)
    return content


def get_prompt_template(
    prompt_key: str,
    fallback_content: str,
    *,
    genre: str | None = None,
    story_style: str | None = None,
) -> PromptTemplate:
    """Build a LangChain PromptTemplate from a DB-managed prompt.

    Args:
        prompt_key:       Stable base prompt key.
        fallback_content: Existing prompt.py fallback content.
        genre:            Optional story genre used to find a specific prompt.
        story_style:      Optional story style used to find a specific prompt.

    Returns:
        PromptTemplate: LangChain template object used by chains.
    """
    return PromptTemplate.from_template(
        load_prompt_content(prompt_key, fallback_content, genre=genre, story_style=story_style)
    )


def clear_prompt_cache() -> None:
    """Clear the local read cache only.

    This is not prompt management; it never writes to MySQL.
    """
    _prompt_cache.clear()


def _load_prompt_content_from_mysql(
    prompt_key: str,
    genre: str | None = None,
    story_style: str | None = None,
) -> str | None:
    import pymysql

    config = _load_mysql_config()
    config["cursorclass"] = pymysql.cursors.DictCursor
    normalized_genre = normalize_optional_match_value(genre)
    normalized_style = normalize_optional_match_value(story_style)
    with pymysql.connect(**config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT template_content
                FROM ai_prompts
                WHERE enabled = 1
                  AND (
                    (
                      base_prompt_key = %s
                      AND prompt_scope = 'SPECIFIC'
                      AND (
                        (match_genre IS NOT NULL AND match_genre <> '' AND match_genre = %s)
                        OR (match_style IS NOT NULL AND match_style <> '' AND match_style = %s)
                      )
                      AND (match_genre IS NULL OR match_genre = '' OR match_genre = %s)
                      AND (match_style IS NULL OR match_style = '' OR match_style = %s)
                    )
                    OR (
                      prompt_scope = 'DEFAULT'
                      AND (base_prompt_key = %s OR prompt_key = %s)
                    )
                  )
                ORDER BY
                  CASE WHEN prompt_scope = 'SPECIFIC' THEN 0 ELSE 1 END,
                  (
                    CASE WHEN match_genre IS NOT NULL AND match_genre <> '' AND match_genre = %s THEN 1 ELSE 0 END
                    + CASE WHEN match_style IS NOT NULL AND match_style <> '' AND match_style = %s THEN 1 ELSE 0 END
                  ) DESC,
                  priority DESC,
                  updated_at DESC,
                  id DESC
                LIMIT 1
                """,
                (
                    prompt_key,
                    normalized_genre,
                    normalized_style,
                    normalized_genre,
                    normalized_style,
                    prompt_key,
                    prompt_key,
                    normalized_genre,
                    normalized_style,
                ),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return row["template_content"]


def build_prompt_cache_key(prompt_key: str, genre: str | None, story_style: str | None) -> str:
    return "|".join(
        [
            prompt_key,
            normalize_optional_match_value(genre) or "",
            normalize_optional_match_value(story_style) or "",
        ]
    )


def normalize_optional_match_value(value: str | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    return str(value).strip()


def _load_mysql_config() -> dict[str, Any]:
    workspace_root = Path(__file__).resolve().parents[2]
    config_path = workspace_root / "config.txt"
    file_config = _load_config_txt(config_path)
    mysql_config = file_config.get("mysql", {}).get("datasource", {})
    jdbc_url = os.getenv("AISAY_MYSQL_URL") or mysql_config.get("url") or ""
    host, port, database = _parse_jdbc_url(jdbc_url)

    return {
        "host": os.getenv("AISAY_MYSQL_HOST") or host or "127.0.0.1",
        "port": int(os.getenv("AISAY_MYSQL_PORT") or port or 3306),
        "user": os.getenv("AISAY_MYSQL_USER") or mysql_config.get("username") or "root",
        "password": os.getenv("AISAY_MYSQL_PASSWORD") or mysql_config.get("password") or "root",
        "database": os.getenv("AISAY_MYSQL_DATABASE") or database or "springcloud",
        "charset": "utf8mb4",
        "connect_timeout": 5,
        "read_timeout": 10,
        "write_timeout": 10,
        "autocommit": True,
    }


def _load_config_txt(config_path: Path) -> dict[str, Any]:
    if not config_path.is_file():
        return {}
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _parse_jdbc_url(jdbc_url: str) -> tuple[str | None, int | None, str | None]:
    match = re.search(r"jdbc:mysql://([^:/?]+)(?::(\d+))?/([^?]+)", jdbc_url)
    if not match:
        return None, None, None
    host = match.group(1)
    port = int(match.group(2)) if match.group(2) else 3306
    database = match.group(3)
    return host, port, database
