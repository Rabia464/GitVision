import logging
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from config import Config
from db.exceptions import DatabaseUnavailableError

logger = logging.getLogger(__name__)


def get_db_connection():
    try:
        return psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            cursor_factory=RealDictCursor,
        )
    except Exception as e:
        logger.exception("PostgreSQL connection failed")
        raise DatabaseUnavailableError(str(e)) from e


def get_cursor(conn):
    return conn.cursor()


@contextmanager
def transaction(conn):
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
