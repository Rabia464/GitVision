from flask import Blueprint, g, request

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, get_json, ok
from routes.repositories import _repo_owner
from utils.validation import optional_str, parse_pagination, require_positive_int

bp = Blueprint("tags", __name__, url_prefix="/api/tags")


@bp.route("", methods=["GET"])
def list_tags():
    limit, offset = parse_pagination(request.args, default_limit=100, max_limit=500)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            "SELECT tag_id, tag_name FROM tag ORDER BY tag_id LIMIT %s OFFSET %s",
            (limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("", methods=["POST"])
def create_tag():
    body = get_json()
    if not body:
        return err("expected JSON body")
    name = optional_str(body.get("tag_name") or body.get("name"), 50)
    if not name:
        return err("tag_name is required")
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "INSERT INTO tag (tag_name) VALUES (%s) RETURNING tag_id, tag_name",
                (name,),
            )
            row = cur.fetchone()
        conn.close()
        return ok(dict(row), 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        if "unique" in str(e).lower():
            return err("tag already exists", 409)
        return err("create failed", 500)


@bp.route("/<int:tag_id>", methods=["GET"])
def get_tag(tag_id):
    try:
        tag_id = require_positive_int(tag_id, "tag_id")
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT tag_id, tag_name FROM tag WHERE tag_id = %s", (tag_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok(dict(row))
    except ValueError as e:
        return err(str(e))
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:tag_id>", methods=["PATCH"])
def patch_tag(tag_id):
    body = get_json()
    if not body:
        return err("expected JSON body")
    name = optional_str(body.get("tag_name") or body.get("name"), 50)
    if not name:
        return err("tag_name is required")
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "UPDATE tag SET tag_name = %s WHERE tag_id = %s RETURNING tag_id, tag_name",
                (name, tag_id),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok(dict(row))
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        if "unique" in str(e).lower():
            return err("tag name conflict", 409)
        return err("update failed", 500)


@bp.route("/<int:tag_id>", methods=["DELETE"])
def delete_tag(tag_id):
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute("DELETE FROM tag WHERE tag_id = %s RETURNING tag_id", (tag_id,))
            row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok({"deleted": True})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


repo_tags_bp = Blueprint("repo_tags", __name__, url_prefix="/api/repos")


@repo_tags_bp.route("/<int:repo_id>/tags/<int:tag_id>", methods=["POST"])
@token_required
def attach_tag(repo_id, tag_id):
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        if not _repo_owner(cur, repo_id, g.current_user_id):
            conn.close()
            return err("forbidden", 403)
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "INSERT INTO repository_tag (repo_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (repo_id, tag_id),
            )
        conn.close()
        return ok({"attached": True}, 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@repo_tags_bp.route("/<int:repo_id>/tags/<int:tag_id>", methods=["DELETE"])
@token_required
def detach_tag(repo_id, tag_id):
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        if not _repo_owner(cur, repo_id, g.current_user_id):
            conn.close()
            return err("forbidden", 403)
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "DELETE FROM repository_tag WHERE repo_id = %s AND tag_id = %s RETURNING repo_id",
                (repo_id, tag_id),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok({"detached": True})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
