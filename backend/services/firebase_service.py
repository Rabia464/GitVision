import json
import logging
import uuid
from typing import BinaryIO, Optional

import firebase_admin
from firebase_admin import credentials, storage

from config import Config

logger = logging.getLogger(__name__)
_initialized = False


def _init_firebase() -> None:
    global _initialized
    if _initialized:
        return
    if Config.FIREBASE_CREDENTIALS_JSON:
        info = json.loads(Config.FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(info)
    elif Config.GOOGLE_APPLICATION_CREDENTIALS:
        cred = credentials.Certificate(Config.GOOGLE_APPLICATION_CREDENTIALS)
    else:
        raise RuntimeError(
            "Firebase is not configured: set GOOGLE_APPLICATION_CREDENTIALS or FIREBASE_CREDENTIALS_JSON"
        )
    if not Config.FIREBASE_STORAGE_BUCKET:
        raise RuntimeError("FIREBASE_STORAGE_BUCKET is not set")
    firebase_admin.initialize_app(cred, {"storageBucket": Config.FIREBASE_STORAGE_BUCKET})
    _initialized = True


def is_configured() -> bool:
    return bool(
        Config.FIREBASE_STORAGE_BUCKET
        and (Config.GOOGLE_APPLICATION_CREDENTIALS or Config.FIREBASE_CREDENTIALS_JSON)
    )


def upload_bytes(data: bytes, object_path: str, content_type: str = "application/octet-stream") -> str:
    _init_firebase()
    bucket = storage.bucket()
    blob = bucket.blob(object_path)
    blob.upload_from_string(data, content_type=content_type)
    try:
        blob.make_public()
        return blob.public_url
    except Exception:
        return f"gs://{bucket.name}/{object_path}"


def upload_stream(stream: BinaryIO, object_path: str, content_type: str) -> str:
    _init_firebase()
    bucket = storage.bucket()
    blob = bucket.blob(object_path)
    blob.upload_from_file(stream, content_type=content_type)
    try:
        blob.make_public()
        return blob.public_url
    except Exception:
        return f"gs://{bucket.name}/{object_path}"


def download_bytes(object_path: str) -> bytes:
    _init_firebase()
    bucket = storage.bucket()
    blob = bucket.blob(object_path)
    return blob.download_as_bytes()


def unique_backup_path(suffix: str = "json") -> str:
    base = Config.BACKUP_STORAGE_PREFIX.rstrip("/") + "/"
    return f"{base}export-{uuid.uuid4().hex}.{suffix}"
