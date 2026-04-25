from datetime import date

from flask import Blueprint, g, request

from db.connection import get_cursor, get_db_connection, transaction
from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, get_json, ok
from utils.validation import parse_pagination, require_positive_int

bp = Blueprint("snapshots", __name__, url_prefix="/api/snapshots")


def _parse_date(s: str) -> date:
    parts = s.split("-")
    if len(parts) != 3:
        raise ValueError("date must be YYYY-MM-DD")
    y, m, d = (int(parts[0]), int(parts[1]), int(parts[2]))
    return date(y, m, d)


@bp.route("", methods=["GET"])
def list_snapshots():
    limit, offset = parse_pagination(request.args)
    uid = request.args.get("user_id", type=int)
    try:
        conn = get_db_connection()
        cur = get_cursor(conn)
        if uid:
            cur.execute(
                """
                SELECT user_id, date, followers, repo_count
                FROM snapshot
                WHERE user_id = %s
                ORDER BY date DESC
                LIMIT %s OFFSET %s
                """,
                (uid, limit, offset),
            )
        else:
            cur.execute(
                """
                SELECT user_id, date, followers, repo_count
                FROM snapshot
                ORDER BY date DESC, user_id
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
        rows = cur.fetchall()
        conn.close()
        return ok([dict(r) for r in rows])
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("", methods=["POST"])
@token_required
def create_snapshot():
    body = get_json()
    if not body:
        return err("expected JSON body")
    try:
        d = _parse_date((body.get("date") or "").strip())
    except Exception:
        return err("invalid date; use YYYY-MM-DD")
    followers = int(body.get("followers") or 0)
    repo_count = int(body.get("repo_count") or 0)
    uid = body.get("user_id", g.current_user_id)
    try:
        uid = int(uid)
    except (TypeError, ValueError):
        return err("invalid user_id")
    if uid != g.current_user_id:
        return err("forbidden", 403)
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                """
                INSERT INTO snapshot (user_id, date, followers, repo_count)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, date) DO UPDATE
                SET followers = EXCLUDED.followers, repo_count = EXCLUDED.repo_count
                RETURNING user_id, date, followers, repo_count
                """,
                (uid, d, followers, repo_count),
            )
            row = cur.fetchone()
        conn.close()
        return ok(dict(row), 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:user_id>/<snapshot_date>", methods=["GET"])
def get_snapshot(user_id, snapshot_date):
    try:
        user_id = require_positive_int(user_id, "user_id")
        d = _parse_date(snapshot_date)
        conn = get_db_connection()
        cur = get_cursor(conn)
        cur.execute(
            "SELECT user_id, date, followers, repo_count FROM snapshot WHERE user_id = %s AND date = %s",
            (user_id, d),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok(dict(row))
    except ValueError as e:
        return err(str(e), 400)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:user_id>/<snapshot_date>", methods=["PATCH"])
@token_required
def patch_snapshot(user_id, snapshot_date):
    if g.current_user_id != user_id:
        return err("forbidden", 403)
    body = get_json()
    if not body:
        return err("expected JSON body")
    try:
        d = _parse_date(snapshot_date)
    except Exception:
        return err("invalid date")
    followers = body.get("followers")
    repo_count = body.get("repo_count")
    if followers is None and repo_count is None:
        return err("nothing to update")
    try:
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            sets = []
            params = []
            if followers is not None:
                sets.append("followers = %s")
                params.append(int(followers))
            if repo_count is not None:
                sets.append("repo_count = %s")
                params.append(int(repo_count))
            params.extend([user_id, d])
            cur.execute(
                f"UPDATE snapshot SET {', '.join(sets)} WHERE user_id = %s AND date = %s RETURNING user_id, date, followers, repo_count",
                tuple(params),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok(dict(row))
    except DatabaseUnavailableError:
        return err("database unavailable", 503)


@bp.route("/<int:user_id>/<snapshot_date>", methods=["DELETE"])
@token_required
def delete_snapshot(user_id, snapshot_date):
    if g.current_user_id != user_id:
        return err("forbidden", 403)
    try:
        d = _parse_date(snapshot_date)
        conn = get_db_connection()
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                "DELETE FROM snapshot WHERE user_id = %s AND date = %s RETURNING user_id",
                (user_id, d),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return err("not found", 404)
        return ok({"deleted": True})
    except ValueError as e:
        return err(str(e), 400)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
