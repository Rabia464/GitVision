from flask import Blueprint, g, request

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, get_json, ok
from utils.validation import optional_str, parse_pagination, require_positive_int

bp = Blueprint("repos", __name__, url_prefix="/api/repos")


def _repo_owner(cur, repo_id: int, user_id: int) -> bool:
    cur.execute(
        "SELECT 1 FROM repository WHERE repo_id = %s AND user_id = %s",
        (repo_id, user_id),
    )
    return cur.fetchone() is not None


@bp.route("", methods=["GET"])
def list_repos():
    limit, offset = parse_pagination(request.args)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT repo_id, user_id, language_id, repo_name, description, stars, forks, created_at
            FROM repository
            ORDER BY repo_id
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("", methods=["POST"])
@token_required
def create_repo():
    body = get_json()
    if not body:
        return err("expected JSON body")
    name = optional_str(body.get("repo_name") or body.get("name"), 100)
    desc = optional_str(body.get("description"), 10_000)
    lang = optional_str(body.get("language_name") or body.get("language"), 50)
    if not name:
        return err("repo_name is required")
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "CALL create_repository_proc(%s, %s, %s, %s)",
                (g.current_user_id, name, desc, lang),
            )
            cur.execute(
                """
                SELECT repo_id, user_id, language_id, repo_name, description, stars, forks, created_at
                FROM repository
                WHERE user_id = %s AND repo_name = %s
                ORDER BY repo_id DESC
                LIMIT 1
                """,
                (g.current_user_id, name),
            )
            row = cur.fetchone()
        conn.close()
        return ok(dict(row), 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        if "unique" in str(e).lower():
            return err("repository name already exists for this user", 409)
        return err("create failed", 500)


@bp.route("/<int:repo_id>", methods=["GET"])
def get_repo(repo_id):
    try:
        repo_id = require_positive_int(repo_id, "repo_id")
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT repo_id, user_id, language_id, repo_name, description, stars, forks, created_at
            FROM repository WHERE repo_id = %s
            """,
            (repo_id,),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok(dict(row))
    except ValueError as e:
        return err(str(e))
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:repo_id>", methods=["PATCH"])
@token_required
def patch_repo(repo_id):
    body = get_json()
    if not body:
        return err("expected JSON body")
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        if not _repo_owner(cur, repo_id, g.current_user_id):
            conn.close()
            return err("forbidden", 403)
        name = optional_str(body.get("repo_name") or body.get("name"), 100)
        desc = body.get("description")
        lang_id = body.get("language_id")
        sets = []
        params = []
        if name is not None:
            sets.append("repo_name = %s")
            params.append(name)
        if desc is not None:
            sets.append("description = %s")
            params.append(desc)
        if lang_id is not None:
            sets.append("language_id = %s")
            params.append(int(lang_id))
        if not sets:
            conn.close()
            return err("nothing to update")
        params.append(repo_id)
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                f"UPDATE repository SET {', '.join(sets)} WHERE repo_id = %s",
                tuple(params),
            )
        conn.close()
        return get_repo(repo_id)
    except ValueError:
        return err("invalid payload")
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        if "unique" in str(e).lower():
            return err("repository name conflict", 409)
        return err("update failed", 500)


@bp.route("/<int:repo_id>", methods=["DELETE"])
@token_required
def delete_repo(repo_id):
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        if not _repo_owner(cur, repo_id, g.current_user_id):
            conn.close()
            return err("forbidden", 403)
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute("DELETE FROM repository WHERE repo_id = %s", (repo_id,))
        conn.close()
        return ok({"deleted": True})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
