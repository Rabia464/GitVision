from flask import Blueprint, request

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, ok
from utils.validation import parse_pagination

bp = Blueprint("admin", __name__, url_prefix="/api/internal")


@bp.route("/activity-cursor", methods=["GET"])
@token_required
def activity_cursor_demo():
    """Fetches a batch of Activity_Log rows via a server-side refcursor function."""
    limit, _ = parse_pagination(request.args, default_limit=25, max_limit=200)
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute("SELECT activity_log_open_cursor('gv_curs'::refcursor, %s)", (limit,))
            cur.execute("FETCH ALL FROM gv_curs")
            rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        return err(f"cursor demo failed: {e!s}", 500)
