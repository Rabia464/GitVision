import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "gitvision")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

    # Firebase / backup (optional until credentials are set)
    FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET", "")
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
    BACKUP_STORAGE_PREFIX = os.environ.get("BACKUP_STORAGE_PREFIX", "gitvision-backups/")
    SESSION_TOKEN_BYTES = int(os.environ.get("SESSION_TOKEN_BYTES", "32"))

    # Optional PAT for higher GitHub API rate limits (used by /api/github/import/<username>)
    GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN", "")
