from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping


def ok(data=None, status=200):
    from flask import jsonify

    return jsonify({"data": _json_safe(data)}), status


def err(message: str, status=400):
    from flask import jsonify

    return jsonify({"error": message}), status


def get_json():
    from flask import request

    body = request.get_json(silent=True)
    if body is None or not isinstance(body, Mapping):
        return None
    return body


def _json_safe(obj: Any):
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, memoryview):
        return obj.tobytes().decode("utf-8", errors="replace")
    return str(obj)
