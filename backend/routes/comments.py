from flask import Blueprint, g, request

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, get_json, ok
from utils.validation import optional_str, parse_pagination

bp = Blueprint("comments", __name__, url_prefix="/api")


@bp.route("/repos/<int:repo_id>/comments", methods=["GET"])
def list_comments(repo_id):
    limit, offset = parse_pagination(request.args)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT comment_id, user_id, repo_id, content, created_at
            FROM comment
            WHERE repo_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (repo_id, limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/repos/<int:repo_id>/comments", methods=["POST"])
@token_required
def add_comment(repo_id):
    body = get_json()
    if not body:
        return err("expected JSON body")
    content = optional_str(body.get("content"), 20_000)
    if not content:
        return err("content is required")
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                """
                INSERT INTO comment (user_id, repo_id, content)
                VALUES (%s, %s, %s)
                RETURNING comment_id, user_id, repo_id, content, created_at
                """,
                (g.current_user_id, repo_id, content),
            )
            row = cur.fetchone()
        conn.close()
        return ok(dict(row), 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/comments/<int:comment_id>", methods=["PATCH"])
@token_required
def patch_comment(comment_id):
    body = get_json()
    if not body:
        return err("expected JSON body")
    content = optional_str(body.get("content"), 20_000)
    if not content:
        return err("content is required")
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT user_id FROM comment WHERE comment_id = %s", (comment_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return err("not found", 404)
        if row["user_id"] != g.current_user_id:
            conn.close()
            return err("forbidden", 403)
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                """
                UPDATE comment SET content = %s
                WHERE comment_id = %s
                RETURNING comment_id, user_id, repo_id, content, created_at
                """,
                (content, comment_id),
            )
            row = cur.fetchone()
        conn.close()
        return ok(dict(row))
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@token_required
def delete_comment(comment_id):
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT user_id FROM comment WHERE comment_id = %s", (comment_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return err("not found", 404)
        if row["user_id"] != g.current_user_id:
            conn.close()
            return err("forbidden", 403)
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute("DELETE FROM comment WHERE comment_id = %s RETURNING comment_id", (comment_id,))
            cur.fetchone()
        conn.close()
        return ok({"deleted": True})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
