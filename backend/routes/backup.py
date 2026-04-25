from flask import Blueprint, g

from db.exceptions import DatabaseUnavailableError
from middleware.auth import token_required
from routes.helpers import err, get_json, ok
from services import firebase_service
from services import sync_service

bp = Blueprint("backup", __name__, url_prefix="/api/backup")


@bp.route("/to-firebase", methods=["POST"])
@token_required
def backup_to_firebase():
    if not firebase_service.is_configured():
        return err("firebase is not configured (credentials + bucket)", 503)
    try:
        result = sync_service.backup_to_firebase()
        return ok(result, 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        return err(f"backup failed: {e!s}", 500)


@bp.route("/from-firebase", methods=["POST"])
@token_required
def backup_from_firebase():
    if not firebase_service.is_configured():
        return err("firebase is not configured (credentials + bucket)", 503)
    body = get_json()
    if not body or not body.get("object_path"):
        return err("object_path is required")
    path = str(body["object_path"]).strip()
    try:
        result = sync_service.backup_from_firebase(path)
        return ok(result, 201)
    except DatabaseUnavailableError:
        return err("database unavailable", 503)
    except Exception as e:
        return err(f"restore failed: {e!s}", 500)
