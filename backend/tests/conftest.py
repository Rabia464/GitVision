"""
Pytest configuration and shared fixtures for GitVision API tests.
Tests run against the real DB configured in .env / environment.
Each module-scoped fixture creates data once and cleans it up after.
"""
import uuid
import pytest
from app import create_app


# ── app & client ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config["TESTING"] = True
    yield app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


# ── helpers ───────────────────────────────────────────────────────────────────

def uid() -> str:
    """Short unique suffix so parallel runs don't clash."""
    return uuid.uuid4().hex[:8]


def register_and_login(client, suffix=None):
    """Register a fresh user and return (user_id, token, username, email)."""
    s = suffix or uid()
    username = f"tester_{s}"
    email = f"tester_{s}@example.com"
    password = "Password123!"

    r = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
    })
    assert r.status_code == 201, f"register failed: {r.get_json()}"
    user_id = r.get_json()["data"]["user_id"]

    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.get_json()}"
    token = r.get_json()["data"]["token"]

    return user_id, token, username, email


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── session-scoped primary user ───────────────────────────────────────────────

@pytest.fixture(scope="session")
def primary_user(client):
    user_id, token, username, email = register_and_login(client)
    yield {"user_id": user_id, "token": token, "username": username, "email": email}


@pytest.fixture(scope="session")
def secondary_user(client):
    user_id, token, username, email = register_and_login(client)
    yield {"user_id": user_id, "token": token, "username": username, "email": email}
