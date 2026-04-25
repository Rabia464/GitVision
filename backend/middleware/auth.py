from functools import wraps

from flask import g, jsonify, request

from db.connection import get_cursor, get_db_connection
from db.exceptions import DatabaseUnavailableError


def _bearer_token():
    h = request.headers.get("Authorization", "")
    if h.lower().startswith("bearer "):
        return h[7:].strip() or None
    return None


def fetch_session_user(token: str):
    conn = get_db_connection()
    try:
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT u.user_id, u.username, u.email, u.followers, u.following, u.created_at
            FROM session s
            JOIN users u ON u.user_id = s.user_id
            WHERE s.token = %s AND s.logout_time IS NULL
            """,
            (token,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _bearer_token()
        if not token:
            return jsonify({"error": "missing bearer token"}), 401
        try:
            user = fetch_session_user(token)
        except DatabaseUnavailableError:
            return jsonify({"error": "database unavailable"}), 503
        if not user:
            return jsonify({"error": "invalid or logged out session"}), 401
        g.current_user = user
        g.current_user_id = user["user_id"]
        g.bearer_token = token
        return fn(*args, **kwargs)

    return wrapper
