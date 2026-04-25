import secrets

from flask import Blueprint, g, request
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, get_json, ok
from utils.validation import validate_email

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/register", methods=["POST"])
def register():
    body = get_json()
    if not body:
        return err("expected JSON body")
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
    conn = None
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
        return ok(dict(row), 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        msg = str(e)
        if "unique" in msg.lower() or "duplicate" in msg.lower():
            return err("username or email already taken", 409)
        return err("registration failed", 500)
    finally:
        if conn:
            conn.close()


@bp.route("/login", methods=["POST"])
def login():
    body = get_json()
    if not body:
        return err("expected JSON body")
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    if not email or not password:
        return err("email and password required")
    conn = None
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            "SELECT user_id, password_hash FROM users WHERE lower(email) = %s",
            (email,),
        )
        row = cur.fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            return err("invalid credentials", 401)
        token = secrets.token_urlsafe(Config.SESSION_TOKEN_BYTES)
        ip = request.remote_addr
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                """
                INSERT INTO session (user_id, token, ip_address)
                VALUES (%s, %s, %s)
                RETURNING session_id, login_time, token
                """,
                (row["user_id"], token, ip),
            )
            sess = cur.fetchone()
        return ok({"token": sess["token"], "login_time": sess["login_time"], "user_id": row["user_id"]})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    finally:
        if conn:
            conn.close()


@bp.route("/logout", methods=["POST"])
@token_required
def logout():
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "UPDATE session SET logout_time = CURRENT_TIMESTAMP WHERE token = %s AND logout_time IS NULL",
                (g.bearer_token,),
            )
        conn.close()
        return ok({"ok": True})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/me", methods=["GET"])
@token_required
def me():
    return ok(g.current_user)
