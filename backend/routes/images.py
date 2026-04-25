from flask import Blueprint, g, request

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, get_json, ok
from utils.validation import optional_str, parse_pagination, require_positive_int

bp = Blueprint("images", __name__, url_prefix="/api/images")


@bp.route("", methods=["GET"])
def list_images():
    limit, offset = parse_pagination(request.args)
    user_id = request.args.get("user_id", type=int)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        if user_id:
            cur.execute(
                """
                SELECT image_id, user_id, repo_id, image_url, image_kind, uploaded_at
                FROM image
                WHERE user_id = %s
                ORDER BY image_id DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
        else:
            cur.execute(
                """
                SELECT image_id, user_id, repo_id, image_url, image_kind, uploaded_at
                FROM image
                ORDER BY image_id DESC
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
def create_image():
    body = get_json()
    if not body:
        return err("expected JSON body")
    url = optional_str(body.get("image_url"), 512)
    if not url:
        return err("image_url is required")
    kind = (body.get("image_kind") or "profile").strip().lower()
    if kind not in ("profile", "repo"):
        return err("image_kind must be profile or repo")
    repo_id = body.get("repo_id")
    if kind == "repo" and not repo_id:
        return err("repo_id is required when image_kind is repo")
    try:
        rid = int(repo_id) if repo_id is not None else None
    except (TypeError, ValueError):
        return err("invalid repo_id")
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                """
                INSERT INTO image (user_id, repo_id, image_url, image_kind)
                VALUES (%s, %s, %s, %s)
                RETURNING image_id, user_id, repo_id, image_url, image_kind, uploaded_at
                """,
                (g.current_user_id, rid, url, kind),
            )
            row = cur.fetchone()
        conn.close()
        return ok(dict(row), 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
