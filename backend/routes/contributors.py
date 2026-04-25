from flask import Blueprint, g, request

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, get_json, ok
from routes.repositories import _repo_owner
from utils.validation import optional_str, parse_pagination, require_positive_int

bp = Blueprint("contributors", __name__, url_prefix="/api/repos")


@bp.route("/<int:repo_id>/contributors", methods=["GET"])
def list_contributors(repo_id):
    limit, offset = parse_pagination(request.args)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT 1 FROM repository WHERE repo_id = %s", (repo_id,))
        if not cur.fetchone():
            conn.close()
            return err("repository not found", 404)
        cur.execute(
            """
            SELECT repo_id, user_id, role
            FROM repository_contributor
            WHERE repo_id = %s
            ORDER BY user_id
            LIMIT %s OFFSET %s
            """,
            (repo_id, limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:repo_id>/contributors", methods=["POST"])
@token_required
def add_contributor(repo_id):
    body = get_json()
    if not body:
        return err("expected JSON body")
    try:
        uid = require_positive_int(body.get("user_id"), "user_id")
    except ValueError as e:
        return err(str(e))
    role = optional_str(body.get("role"), 50) or "collaborator"
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        if not _repo_owner(cur, repo_id, g.current_user_id):
            conn.close()
            return err("forbidden", 403)
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                """
                INSERT INTO repository_contributor (repo_id, user_id, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (repo_id, user_id) DO UPDATE SET role = EXCLUDED.role
                RETURNING repo_id, user_id, role
                """,
                (repo_id, uid, role),
            )
            row = cur.fetchone()
        conn.close()
        return ok(dict(row), 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:repo_id>/contributors/<int:user_id>", methods=["DELETE"])
@token_required
def remove_contributor(repo_id, user_id):
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        if not _repo_owner(cur, repo_id, g.current_user_id):
            conn.close()
            return err("forbidden", 403)
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "DELETE FROM repository_contributor WHERE repo_id = %s AND user_id = %s RETURNING repo_id",
                (repo_id, user_id),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok({"deleted": True})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
