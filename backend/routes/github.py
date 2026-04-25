import os
import secrets
from urllib.parse import urlencode

import requests
from flask import Blueprint, g, redirect, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import generate_password_hash

from config import Config
from db.connection import get_cursor, get_db_connection, transaction
from middleware.auth import token_required
from routes.helpers import err, ok

bp = Blueprint("github", __name__, url_prefix="/api/github")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:5000/api/github/callback")
FRONTEND_REDIRECT_URI = os.getenv("FRONTEND_REDIRECT_URI", "http://localhost:5173/")

_STATE_SALT = "github-oauth-state"
_STATE_MAX_AGE_SECONDS = 600
_GITHUB_TIMEOUT_SECONDS = 20


def _state_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(Config.SECRET_KEY, salt=_STATE_SALT)


def _make_state(user_id: int) -> str:
    payload = {"user_id": user_id, "nonce": secrets.token_urlsafe(16)}
    return _state_serializer().dumps(payload)


def _parse_state(state: str) -> int:
    payload = _state_serializer().loads(state, max_age=_STATE_MAX_AGE_SECONDS)
    return int(payload["user_id"])


def _github_get(path: str):
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github+json"}
    if Config.GITHUB_API_TOKEN:
        headers["Authorization"] = f"Bearer {Config.GITHUB_API_TOKEN}"
    resp = requests.get(url, headers=headers, timeout=_GITHUB_TIMEOUT_SECONDS)
    if resp.status_code == 404:
        raise ValueError("github user not found")
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        raise RuntimeError("github api rate limit exceeded")
    if resp.status_code >= 400:
        raise RuntimeError(f"github api error ({resp.status_code})")
    return resp.json()


def _resolve_or_create_language(cur, language_name):
    if not language_name:
        return None
    cur.execute("SELECT language_id FROM language WHERE language_name = %s", (language_name,))
    row = cur.fetchone()
    if row:
        return row["language_id"]
    cur.execute("INSERT INTO language (language_name) VALUES (%s) RETURNING language_id", (language_name,))
    return cur.fetchone()["language_id"]


def _upsert_import_user(cur, gh_user):
    username = gh_user["login"]
    github_id = str(gh_user["id"])
    followers = int(gh_user.get("followers") or 0)
    synthetic_email = f"github_{github_id}@gitvision.local"

    # Prefer github_id match; fallback to username.
    cur.execute(
        """
        SELECT user_id FROM users
        WHERE github_id = %s OR username = %s
        ORDER BY user_id
        LIMIT 1
        """,
        (github_id, username),
    )
    existing = cur.fetchone()
    if existing:
        cur.execute(
            """
            UPDATE users
            SET username = %s, github_id = %s, followers = %s
            WHERE user_id = %s
            RETURNING user_id
            """,
            (username, github_id, followers, existing["user_id"]),
        )
        return cur.fetchone()["user_id"], False

    cur.execute(
        """
        INSERT INTO users (username, email, password_hash, followers, github_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING user_id
        """,
        (username, synthetic_email, generate_password_hash(secrets.token_urlsafe(32)), followers, github_id),
    )
    return cur.fetchone()["user_id"], True


def _upsert_import_repo(cur, user_id: int, repo: dict):
    repo_name = (repo.get("name") or "").strip()[:100]
    if not repo_name:
        return None
    language_id = _resolve_or_create_language(cur, repo.get("language"))
    gh_repo_id = str(repo.get("id"))
    stars = int(repo.get("stargazers_count") or 0)
    forks = int(repo.get("forks_count") or 0)
    description = (repo.get("description") or "")[:10000]
    html_url = (repo.get("html_url") or "")[:255]

    cur.execute(
        """
        INSERT INTO repository (user_id, language_id, repo_name, description, stars, forks, github_repo_id, github_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, repo_name) DO UPDATE SET
            language_id = EXCLUDED.language_id,
            description = EXCLUDED.description,
            stars = EXCLUDED.stars,
            forks = EXCLUDED.forks,
            github_repo_id = EXCLUDED.github_repo_id,
            github_url = EXCLUDED.github_url
        RETURNING repo_id
        """,
        (user_id, language_id, repo_name, description, stars, forks, gh_repo_id, html_url),
    )
    row = cur.fetchone()
    return row["repo_id"] if row else None


@bp.route("/import/<username>", methods=["GET"])
def import_profile(username):
    username = (username or "").strip()
    if not username:
        return err("username is required")

    try:
        gh_user = _github_get(f"/users/{username}")
        gh_repos = _github_get(f"/users/{username}/repos?per_page=100&sort=updated")
    except ValueError as e:
        return err(str(e), 404)
    except RuntimeError as e:
        msg = str(e)
        if "rate limit" in msg.lower():
            return err(msg, 429)
        return err(msg, 502)
    except requests.RequestException:
        return err("failed to reach github api", 502)

    conn = get_db_connection()
    try:
        imported_repo_count = 0
        with transaction(conn):
            cur = get_cursor(conn)
            user_id, created = _upsert_import_user(cur, gh_user)
            for repo in gh_repos:
                if _upsert_import_repo(cur, user_id, repo):
                    imported_repo_count += 1
        return ok(
            {
                "imported_username": gh_user["login"],
                "user_id": user_id,
                "user_created": created,
                "repos_processed": len(gh_repos),
                "repos_upserted": imported_repo_count,
            }
        )
    finally:
        conn.close()


@bp.route("/profile/<username>", methods=["GET"])
def imported_profile(username):
    username = (username or "").strip()
    if not username:
        return err("username is required")
    conn = get_db_connection()
    try:
        cur = get_cursor(conn)
        cur.execute(
            """
            SELECT user_id, username, followers, following, created_at, github_id
            FROM users
            WHERE lower(username) = lower(%s)
            LIMIT 1
            """,
            (username,),
        )
        user = cur.fetchone()
        if not user:
            return err("user not found in GitVision database", 404)
        cur.execute(
            """
            SELECT COALESCE(SUM(stars), 0) AS total_stars, COUNT(*) AS repo_count
            FROM repository
            WHERE user_id = %s
            """,
            (user["user_id"],),
        )
        aggregate = cur.fetchone()
        result = dict(user)
        result["total_stars"] = int(aggregate["total_stars"] or 0)
        result["repo_count"] = int(aggregate["repo_count"] or 0)
        return ok(result)
    finally:
        conn.close()


@bp.route("/repositories/<username>", methods=["GET"])
def imported_repositories(username):
    username = (username or "").strip()
    if not username:
        return err("username is required")
    conn = get_db_connection()
    try:
        cur = get_cursor(conn)
        cur.execute("SELECT user_id FROM users WHERE lower(username) = lower(%s) LIMIT 1", (username,))
        row = cur.fetchone()
        if not row:
            return err("user not found in GitVision database", 404)
        cur.execute(
            """
            SELECT r.repo_id, r.repo_name, r.description, r.stars, r.forks, r.github_url, l.language_name
            FROM repository r
            LEFT JOIN language l ON l.language_id = r.language_id
            WHERE r.user_id = %s
            ORDER BY r.stars DESC, r.repo_id DESC
            """,
            (row["user_id"],),
        )
        repos = [dict(r) for r in cur.fetchall()]
        return ok(repos)
    finally:
        conn.close()


@bp.route("/connect", methods=["GET"])
@token_required
def connect():
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return err("GitHub OAuth is not configured", 500)

    state = _make_state(g.current_user_id)
    query = urlencode(
        {
            "client_id": GITHUB_CLIENT_ID,
            "redirect_uri": GITHUB_REDIRECT_URI,
            "scope": "repo,user",
            "state": state,
        }
    )
    github_auth_url = f"https://github.com/login/oauth/authorize?{query}"
    return ok({"url": github_auth_url})


@bp.route("/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state:
        return err("Missing code or state parameters from GitHub", 400)

    try:
        user_id = _parse_state(state)
    except SignatureExpired:
        return err("OAuth state expired. Please reconnect GitHub.", 401)
    except (BadSignature, ValueError, KeyError):
        return err("Invalid OAuth state", 401)

    token_resp = requests.post(
        "https://github.com/login/oauth/access_token",
        json={"client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET, "code": code},
        headers={"Accept": "application/json"},
        timeout=20,
    )
    if token_resp.status_code != 200:
        return err("Failed to obtain token from GitHub", 500)
    access_token = token_resp.json().get("access_token")
    if not access_token:
        return err("No access token found in GitHub response", 500)

    user_resp = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        timeout=_GITHUB_TIMEOUT_SECONDS,
    )
    if user_resp.status_code != 200:
        return err("Failed to fetch GitHub profile details", 500)
    github_user_id = str(user_resp.json().get("id") or "")
    if not github_user_id:
        return err("GitHub profile did not include user id", 500)

    conn = get_db_connection()
    try:
        with transaction(conn):
            cur = get_cursor(conn)
            cur.execute(
                """
                UPDATE users
                SET github_id = %s, github_access_token = %s
                WHERE user_id = %s
                """,
                (github_user_id, access_token, user_id),
            )
        return redirect(FRONTEND_REDIRECT_URI)
    finally:
        conn.close()


@bp.route("/sync", methods=["POST"])
@token_required
def sync_repos():
    conn = get_db_connection()
    try:
        cur = get_cursor(conn)
        cur.execute("SELECT github_access_token FROM users WHERE user_id = %s", (g.current_user_id,))
        row = cur.fetchone()
        if not row or not row["github_access_token"]:
            return err("GitHub account is not connected", 400)

        access_token = row["github_access_token"]
        repos_resp = requests.get(
            "https://api.github.com/user/repos?per_page=100&sort=updated",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
            timeout=30,
        )
        if repos_resp.status_code != 200:
            return err("Failed to fetch repositories from GitHub. Token may have expired.", 500)

        github_repos = repos_resp.json()
        synced_count = 0

        with transaction(conn):
            cur = get_cursor(conn)
            for grepo in github_repos:
                gh_repo_id = str(grepo["id"])
                name = grepo["name"][:100]
                desc = (grepo.get("description", "") or "")[:10000]
                url = grepo.get("html_url", "")
                stars = grepo.get("stargazers_count", 0)
                forks = grepo.get("forks_count", 0)
                lang = grepo.get("language")

                lang_id = None
                if lang:
                    cur.execute("SELECT language_id FROM language WHERE language_name = %s", (lang,))
                    lang_row = cur.fetchone()
                    if lang_row:
                        lang_id = lang_row["language_id"]
                    else:
                        cur.execute(
                            "INSERT INTO language (language_name) VALUES (%s) RETURNING language_id",
                            (lang,),
                        )
                        lang_id = cur.fetchone()["language_id"]

                cur.execute(
                    """
                    INSERT INTO repository (user_id, language_id, repo_name, description, stars, forks, github_repo_id, github_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, repo_name) DO UPDATE SET
                        description = EXCLUDED.description,
                        stars = EXCLUDED.stars,
                        forks = EXCLUDED.forks,
                        github_repo_id = EXCLUDED.github_repo_id,
                        github_url = EXCLUDED.github_url,
                        language_id = EXCLUDED.language_id
                    """,
                    (g.current_user_id, lang_id, name, desc, stars, forks, gh_repo_id, url),
                )
                synced_count += 1

        return ok({"synced_count": synced_count})
    finally:
        conn.close()
