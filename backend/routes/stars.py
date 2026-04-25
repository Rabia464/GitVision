from flask import Blueprint, g

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, ok

bp = Blueprint("stars", __name__, url_prefix="/api/repos")


@bp.route("/<int:repo_id>/star", methods=["POST"])
@token_required
def star(repo_id):
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "INSERT INTO starred_repository (user_id, repo_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (g.current_user_id, repo_id),
            )
        conn.close()
        return ok({"starred": True}, 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:repo_id>/star", methods=["DELETE"])
@token_required
def unstar(repo_id):
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "DELETE FROM starred_repository WHERE user_id = %s AND repo_id = %s RETURNING repo_id",
                (g.current_user_id, repo_id),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return ok({"starred": False})
        return ok({"starred": False})
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
