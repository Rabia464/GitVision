from flask import Blueprint, request

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from routes.helpers import err, get_json, ok
from utils.validation import optional_str, parse_pagination, require_positive_int

bp = Blueprint("languages", __name__, url_prefix="/api/languages")


@bp.route("", methods=["GET"])
def list_languages():
    limit, offset = parse_pagination(request.args, default_limit=100, max_limit=500)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            "SELECT language_id, language_name FROM language ORDER BY language_id LIMIT %s OFFSET %s",
            (limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("", methods=["POST"])
def create_language():
    body = get_json()
    if not body:
        return err("expected JSON body")
    name = optional_str(body.get("language_name") or body.get("name"), 50)
    if not name:
        return err("language_name is required")
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "INSERT INTO language (language_name) VALUES (%s) RETURNING language_id, language_name",
                (name,),
            )
            row = cur.fetchone()
        conn.close()
        return ok(dict(row), 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        if "unique" in str(e).lower():
            return err("language already exists", 409)
        return err("create failed", 500)


@bp.route("/<int:language_id>", methods=["GET"])
def get_language(language_id):
    try:
        language_id = require_positive_int(language_id, "language_id")
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT language_id, language_name FROM language WHERE language_id = %s", (language_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok(dict(row))
    except ValueError as e:
        return err(str(e))
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:language_id>", methods=["PATCH"])
def patch_language(language_id):
    body = get_json()
    if not body:
        return err("expected JSON body")
    name = optional_str(body.get("language_name") or body.get("name"), 50)
    if not name:
        return err("language_name is required")
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "UPDATE language SET language_name = %s WHERE language_id = %s RETURNING language_id, language_name",
                (name, language_id),
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
            return err("language name conflict", 409)
        return err("update failed", 500)


@bp.route("/<int:language_id>", methods=["DELETE"])
def delete_language(language_id):
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute("DELETE FROM language WHERE language_id = %s RETURNING language_id", (language_id,))
            row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok({"deleted": True})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
