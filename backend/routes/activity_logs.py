from flask import Blueprint, request

from db.connection import get_cursor, get_db_connection
from db.exceptions import DatabaseUnavailableError
from routes.helpers import err, ok
from utils.validation import parse_pagination

bp = Blueprint("activity_logs", __name__, url_prefix="/api/activity-logs")


@bp.route("", methods=["GET"])
def list_activity_logs():
    limit, offset = parse_pagination(request.args, default_limit=50, max_limit=200)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT log_id, action, table_name, details, timestamp
            FROM activity_log
            ORDER BY log_id DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
