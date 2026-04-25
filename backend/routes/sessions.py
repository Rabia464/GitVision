from flask import Blueprint, g, request

from db.connection import get_cursor, get_db_connection
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, ok
from utils.validation import parse_pagination

bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")


@bp.route("", methods=["GET"])
@token_required
def list_sessions():
    limit, offset = parse_pagination(request.args, default_limit=50, max_limit=200)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT session_id, user_id, login_time, logout_time, ip_address
            FROM session
            WHERE user_id = %s
            ORDER BY login_time DESC
            LIMIT %s OFFSET %s
            """,
            (g.current_user_id, limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        out = []
        for r in rows:
            d = dict(r)
            d.pop("token", None)
            out.append(d)
        return ok(out)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
