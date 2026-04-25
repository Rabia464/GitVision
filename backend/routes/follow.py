from flask import Blueprint, g

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, ok
from utils.validation import require_positive_int

bp = Blueprint("follow", __name__, url_prefix="/api/users")


@bp.route("/<int:user_id>/follow", methods=["POST"])
@token_required
def follow(user_id):
    try:
        user_id = require_positive_int(user_id, "user_id")
    except ValueError as e:
        return err(str(e))
    if user_id == g.current_user_id:
        return err("cannot follow yourself", 400)
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute("CALL follow_user_proc(%s, %s)", (g.current_user_id, user_id))
        conn.close()
        return ok({"ok": True})
    except ValueError as e:
        return err(str(e), 400)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        msg = str(e).lower()
        if "check" in msg:
            return err("cannot follow yourself", 400)
        return err("follow failed", 500)


@bp.route("/<int:user_id>/follow", methods=["DELETE"])
@token_required
def unfollow(user_id):
    try:
        user_id = require_positive_int(user_id, "user_id")
    except ValueError as e:
        return err(str(e))
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "DELETE FROM follow WHERE follower_id = %s AND following_id = %s RETURNING follower_id",
                (g.current_user_id, user_id),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return ok({"ok": True, "was_following": False})
        return ok({"ok": True, "was_following": True})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
