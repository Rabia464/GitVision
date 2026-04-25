import re
from typing import Optional, Tuple

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def require_positive_int(value, name: str = "id") -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a positive integer")
    if n < 1:
        raise ValueError(f"{name} must be a positive integer")
    return n


def parse_pagination(args, default_limit: int = 20, max_limit: int = 100) -> Tuple[int, int]:
    try:
        limit = int(args.get("limit", default_limit))
    except (TypeError, ValueError):
        limit = default_limit
    try:
        offset = int(args.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0
    limit = max(1, min(limit, max_limit))
    offset = max(0, offset)
    return limit, offset


def validate_email(email: str) -> str:
    if not email or not isinstance(email, str):
        raise ValueError("email is required")
    e = email.strip().lower()
    if not _EMAIL_RE.match(e):
        raise ValueError("invalid email format")
    return e


def optional_str(value, max_len: Optional[int] = None) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("expected string")
    s = value.strip()
    if not s:
        return None
    if max_len is not None and len(s) > max_len:
        raise ValueError(f"value too long (max {max_len})")
    return s
