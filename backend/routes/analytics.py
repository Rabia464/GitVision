from flask import Blueprint, request

from db.connection import get_cursor, get_db_connection
from db.exceptions import DatabaseUnavailableError
from routes.helpers import err, ok
from utils.validation import parse_pagination

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@bp.route("/user-repo-summary", methods=["GET"])
def user_repo_summary():
    limit, offset = parse_pagination(request.args, default_limit=100, max_limit=500)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT user_id, username, total_repos, total_stars
            FROM user_repo_summary
            ORDER BY user_id
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/repo-engagement", methods=["GET"])
def repo_engagement():
    limit, offset = parse_pagination(request.args, default_limit=100, max_limit=500)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT repo_id, repo_name, owner_id, stars, comment_count, contributor_count, star_rows
            FROM repo_engagement_summary
            ORDER BY repo_id
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
