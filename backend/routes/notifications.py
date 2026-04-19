from flask import Blueprint, g, request

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, ok
from utils.validation import parse_pagination, require_positive_int

bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@bp.route("", methods=["GET"])
@token_required
def list_notifications():
    limit, offset = parse_pagination(request.args)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT notification_id, user_id, message, is_read, created_at
            FROM notification
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (g.current_user_id, limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:notification_id>/read", methods=["PATCH"])
@token_required
def mark_read(notification_id):
    try:
        notification_id = require_positive_int(notification_id, "notification_id")
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                """
                UPDATE notification SET is_read = TRUE
                WHERE notification_id = %s AND user_id = %s
                RETURNING notification_id, user_id, message, is_read, created_at
                """,
                (notification_id, g.current_user_id),
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
