"""
PostgreSQL <-> Firebase Storage backup helpers.

backup_to_firebase: exports selected tables to one JSON document in Cloud Storage
and records Backup_Log (+ Activity companion) via backup_mark_proc in one transaction.

backup_from_firebase: destructive restore (TRUNCATE selected tables + INSERT from JSON).
Restores denormalized counters as stored in the snapshot; use a snapshot taken from
this app for consistency.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from db.connection import get_cursor, get_db_connection, transaction
from services import firebase_service

logger = logging.getLogger(__name__)

EXPORT_TABLES = [
    "language",
    "tag",
    "users",
    "repository",
    "repository_tag",
    "repository_contributor",
    "starred_repository",
    "follow",
    "comment",
    "notification",
    "snapshot",
    "image",
]


def export_database_payload(conn) -> Dict[str, Any]:
    cur = get_cursor(conn)
    payload: Dict[str, Any] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "tables": {},
    }
    for table in EXPORT_TABLES:
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        payload["tables"][table] = [dict(r) for r in rows]
    return payload


def _log_backup_failure():
    try:
        conn = get_db_connection()
        try:
            with transaction(conn):
                c = get_cursor(conn)
                c.execute("CALL backup_mark_proc(%s, %s)", ("Full", "Failed"))
        finally:
            conn.close()
    except Exception:
        logger.exception("failed to write failed backup log")


def backup_to_firebase() -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        payload = export_database_payload(conn)
        raw = json.dumps(payload, default=str).encode("utf-8")
        path = firebase_service.unique_backup_path("json")
        url = firebase_service.upload_bytes(raw, path, content_type="application/json")
        with transaction(conn):
            c = get_cursor(conn)
            c.execute("CALL backup_mark_proc(%s, %s)", ("Full", "Success"))
        return {"object_path": path, "url": url, "tables": list(payload["tables"].keys())}
    except Exception:
        logger.exception("backup_to_firebase failed")
        _log_backup_failure()
        raise
    finally:
        conn.close()


def backup_from_firebase(object_path: str) -> Dict[str, Any]:
    raw = firebase_service.download_bytes(object_path)
    doc = json.loads(raw.decode("utf-8"))
    tables = doc.get("tables") or {}
    conn = get_db_connection()
    try:
        with transaction(conn):
            c = get_cursor(conn)
            c.execute(
                """
                TRUNCATE starred_repository, repository_tag, repository_contributor,
                comment, notification, follow, image, snapshot, repository, users, tag, language
                RESTART IDENTITY CASCADE
                """
            )
            if "language" in tables:
                for row in tables["language"]:
                    c.execute(
                        """
                        INSERT INTO language (language_id, language_name)
                        VALUES (%(language_id)s, %(language_name)s)
                        ON CONFLICT (language_id) DO NOTHING
                        """,
                        row,
                    )
            if "tag" in tables:
                for row in tables["tag"]:
                    c.execute(
                        """
                        INSERT INTO tag (tag_id, tag_name)
                        VALUES (%(tag_id)s, %(tag_name)s)
                        ON CONFLICT (tag_id) DO NOTHING
                        """,
                        row,
                    )
            if "users" in tables:
                for row in tables["users"]:
                    c.execute(
                        """
                        INSERT INTO users (user_id, username, email, password_hash, followers, following, created_at)
                        VALUES (%(user_id)s, %(username)s, %(email)s, %(password_hash)s, %(followers)s, %(following)s, %(created_at)s)
                        ON CONFLICT (user_id) DO NOTHING
                        """,
                        row,
                    )
            if "repository" in tables:
                for row in tables["repository"]:
                    c.execute(
                        """
                        INSERT INTO repository (repo_id, user_id, language_id, repo_name, description, stars, forks, created_at)
                        VALUES (%(repo_id)s, %(user_id)s, %(language_id)s, %(repo_name)s, %(description)s, %(stars)s, %(forks)s, %(created_at)s)
                        ON CONFLICT (repo_id) DO NOTHING
                        """,
                        row,
                    )
            for tbl, sql in [
                (
                    "repository_contributor",
                    "INSERT INTO repository_contributor (repo_id, user_id, role) VALUES (%(repo_id)s, %(user_id)s, %(role)s) ON CONFLICT (repo_id, user_id) DO NOTHING",
                ),
                (
                    "repository_tag",
                    "INSERT INTO repository_tag (repo_id, tag_id) VALUES (%(repo_id)s, %(tag_id)s) ON CONFLICT (repo_id, tag_id) DO NOTHING",
                ),
                (
                    "starred_repository",
                    "INSERT INTO starred_repository (user_id, repo_id, starred_at) VALUES (%(user_id)s, %(repo_id)s, %(starred_at)s) ON CONFLICT (user_id, repo_id) DO NOTHING",
                ),
                (
                    "follow",
                    "INSERT INTO follow (follower_id, following_id, followed_at) VALUES (%(follower_id)s, %(following_id)s, %(followed_at)s) ON CONFLICT (follower_id, following_id) DO NOTHING",
                ),
                (
                    "comment",
                    "INSERT INTO comment (comment_id, user_id, repo_id, content, created_at) VALUES (%(comment_id)s, %(user_id)s, %(repo_id)s, %(content)s, %(created_at)s) ON CONFLICT (comment_id) DO NOTHING",
                ),
                (
                    "notification",
                    "INSERT INTO notification (notification_id, user_id, message, is_read, created_at) VALUES (%(notification_id)s, %(user_id)s, %(message)s, %(is_read)s, %(created_at)s) ON CONFLICT (notification_id) DO NOTHING",
                ),
                (
                    "snapshot",
                    "INSERT INTO snapshot (user_id, date, followers, repo_count) VALUES (%(user_id)s, %(date)s, %(followers)s, %(repo_count)s) ON CONFLICT (user_id, date) DO NOTHING",
                ),
            ]:
                for row in tables.get(tbl, []) or []:
                    c.execute(sql, row)
            for row in tables.get("image", []) or []:
                r = dict(row)
                r.setdefault("image_kind", "profile")
                r.setdefault("repo_id", None)
                c.execute(
                    """
                    INSERT INTO image (image_id, user_id, repo_id, image_url, image_kind, uploaded_at)
                    VALUES (%(image_id)s, %(user_id)s, %(repo_id)s, %(image_url)s, %(image_kind)s, %(uploaded_at)s)
                    ON CONFLICT (image_id) DO NOTHING
                    """,
                    r,
                )
            c.execute("CALL backup_mark_proc(%s, %s)", ("Restore", "Success"))
        return {"restored_tables": list(tables.keys())}
    finally:
        conn.close()
