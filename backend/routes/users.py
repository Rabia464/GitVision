from flask import Blueprint, g, request

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, get_json, ok
from utils.validation import optional_str, parse_pagination, require_positive_int, validate_email

bp = Blueprint("users", __name__, url_prefix="/api/users")


def _public_user(row: dict) -> dict:
    d = dict(row)
    d.pop("password_hash", None)
    return d


@bp.route("", methods=["GET"])
def list_users():
    limit, offset = parse_pagination(request.args)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT user_id, username, email, followers, following, created_at
            FROM users
            ORDER BY user_id
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([_public_user(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("", methods=["POST"])
def create_user():
    """Alias of register-style create (for REST matrix); prefer /api/auth/register."""
    body = get_json()
    if not body:
        return err("expected JSON body")
    from werkzeug.security import generate_password_hash

    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    try:
        email = validate_email(body.get("email", ""))
    except ValueError as e:
        return err(str(e))
    if len(username) < 3 or len(username) > 50:
        return err("username must be 3-50 characters")
    if len(password) < 8:
        return err("password must be at least 8 characters")
    ph = generate_password_hash(password)
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING user_id, username, email, followers, following, created_at
                """,
                (username, email, ph),
            )
            row = cur.fetchone()
        conn.close()
        return ok(_public_user(row), 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        msg = str(e)
        if "unique" in msg.lower() or "duplicate" in msg.lower():
            return err("username or email already taken", 409)
        return err("create failed", 500)


@bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        user_id = require_positive_int(user_id, "user_id")
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            "SELECT user_id, username, email, followers, following, created_at FROM users WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok(_public_user(row))
    except ValueError as e:
        return err(str(e))
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:user_id>", methods=["PATCH"])
@token_required
def patch_user(user_id):
    if g.current_user_id != user_id:
        return err("forbidden", 403)
    body = get_json()
    if not body:
        return err("expected JSON body")
    try:
        username = optional_str(body.get("username"), 50)
        email_raw = body.get("email")
        email = validate_email(email_raw) if email_raw else None
    except ValueError as e:
        return err(str(e))
    if username is None and email is None:
        return err("nothing to update")
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            if username is not None:
                cur.execute("UPDATE users SET username = %s WHERE user_id = %s", (username, user_id))
            if email is not None:
                cur.execute("UPDATE users SET email = %s WHERE user_id = %s", (email, user_id))
        conn.close()
        return get_user(user_id)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        if "unique" in str(e).lower():
            return err("username or email conflict", 409)
        return err("update failed", 500)


@bp.route("/<int:user_id>", methods=["DELETE"])
@token_required
def delete_user(user_id):
    if g.current_user_id != user_id:
        return err("forbidden", 403)
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.close()
        return ok({"deleted": True})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:user_id>/repos", methods=["GET"])
def list_user_repos(user_id):
    limit, offset = parse_pagination(request.args)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
        if not cur.fetchone():
            conn.close()
            return err("user not found", 404)
        cur.execute(
            """
            SELECT repo_id, user_id, language_id, repo_name, description, stars, forks, created_at
            FROM repository
            WHERE user_id = %s
            ORDER BY repo_id
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
