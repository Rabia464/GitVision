"""
GitVision API - Day 5 Verification Tests
Run from backend/ directory:
    pytest tests/ -v
"""
import pytest
from tests.conftest import auth, register_and_login, uid


# =============================================================================
# HEALTH
# =============================================================================

class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.get_json()["data"]["status"] == "healthy"


# =============================================================================
# AUTH
# =============================================================================

class TestAuth:
    def test_register_success(self, client):
        s = uid()
        r = client.post("/api/auth/register", json={
            "username": f"auth_{s}",
            "email": f"auth_{s}@test.com",
            "password": "Password123!",
        })
        assert r.status_code == 201
        d = r.get_json()["data"]
        assert "user_id" in d
        assert "password_hash" not in d

    def test_register_duplicate(self, client, primary_user):
        r = client.post("/api/auth/register", json={
            "username": primary_user["username"],
            "email": primary_user["email"],
            "password": "Password123!",
        })
        assert r.status_code == 409

    def test_register_bad_email(self, client):
        r = client.post("/api/auth/register", json={
            "username": f"u_{uid()}",
            "email": "not-an-email",
            "password": "Password123!",
        })
        assert r.status_code == 400

    def test_register_short_password(self, client):
        s = uid()
        r = client.post("/api/auth/register", json={
            "username": f"u_{s}",
            "email": f"u_{s}@test.com",
            "password": "abc",
        })
        assert r.status_code == 400

    def test_login_success(self, client, primary_user):
        r = client.post("/api/auth/login", json={
            "email": primary_user["email"],
            "password": "Password123!",
        })
        assert r.status_code == 200
        assert "token" in r.get_json()["data"]

    def test_login_wrong_password(self, client, primary_user):
        r = client.post("/api/auth/login", json={
            "email": primary_user["email"],
            "password": "WrongPass999!",
        })
        assert r.status_code == 401

    def test_me_authenticated(self, client, primary_user):
        r = client.get("/api/auth/me", headers=auth(primary_user["token"]))
        assert r.status_code == 200
        assert r.get_json()["data"]["user_id"] == primary_user["user_id"]

    def test_me_unauthenticated(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_logout(self, client):
        # Create a throwaway user just for logout test
        _, token, _, _ = register_and_login(client)
        r = client.post("/api/auth/logout", headers=auth(token))
        assert r.status_code == 200
        # Token should now be invalid
        r2 = client.get("/api/auth/me", headers=auth(token))
        assert r2.status_code == 401


# =============================================================================
# USERS
# =============================================================================

class TestUsers:
    def test_list_users(self, client):
        r = client.get("/api/users")
        assert r.status_code == 200
        assert isinstance(r.get_json()["data"], list)

    def test_get_user(self, client, primary_user):
        r = client.get(f"/api/users/{primary_user['user_id']}")
        assert r.status_code == 200
        d = r.get_json()["data"]
        assert d["user_id"] == primary_user["user_id"]
        assert "password_hash" not in d

    def test_get_user_not_found(self, client):
        r = client.get("/api/users/9999999")
        assert r.status_code == 404

    def test_patch_user(self, client, primary_user):
        new_name = f"updated_{uid()}"
        r = client.patch(
            f"/api/users/{primary_user['user_id']}",
            json={"username": new_name},
            headers=auth(primary_user["token"]),
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["username"] == new_name
        # restore original username
        client.patch(
            f"/api/users/{primary_user['user_id']}",
            json={"username": primary_user["username"]},
            headers=auth(primary_user["token"]),
        )

    def test_patch_user_forbidden(self, client, primary_user, secondary_user):
        r = client.patch(
            f"/api/users/{primary_user['user_id']}",
            json={"username": f"hacked_{uid()}"},
            headers=auth(secondary_user["token"]),
        )
        assert r.status_code == 403

    def test_list_user_repos(self, client, primary_user):
        r = client.get(f"/api/users/{primary_user['user_id']}/repos")
        assert r.status_code == 200
        assert isinstance(r.get_json()["data"], list)

    def test_pagination(self, client):
        r = client.get("/api/users?limit=2&offset=0")
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert len(data) <= 2


# =============================================================================
# LANGUAGES
# =============================================================================

class TestLanguages:
    @pytest.fixture(scope="class")
    def lang(self, client):
        r = client.post("/api/languages", json={"language_name": f"Lang_{uid()}"})
        assert r.status_code == 201
        return r.get_json()["data"]

    def test_create_language(self, lang):
        assert "language_id" in lang
        assert "language_name" in lang

    def test_list_languages(self, client):
        r = client.get("/api/languages")
        assert r.status_code == 200
        assert isinstance(r.get_json()["data"], list)

    def test_get_language(self, client, lang):
        r = client.get(f"/api/languages/{lang['language_id']}")
        assert r.status_code == 200
        assert r.get_json()["data"]["language_id"] == lang["language_id"]

    def test_patch_language(self, client, lang):
        new_name = f"Lang_{uid()}"
        r = client.patch(f"/api/languages/{lang['language_id']}", json={"language_name": new_name})
        assert r.status_code == 200
        assert r.get_json()["data"]["language_name"] == new_name

    def test_delete_language(self, client):
        r = client.post("/api/languages", json={"language_name": f"ToDelete_{uid()}"})
        lid = r.get_json()["data"]["language_id"]
        r = client.delete(f"/api/languages/{lid}")
        assert r.status_code == 200
        assert r.get_json()["data"]["deleted"] is True

    def test_duplicate_language(self, client, lang):
        # patch updated name; fetch current
        r = client.get(f"/api/languages/{lang['language_id']}")
        current_name = r.get_json()["data"]["language_name"]
        r2 = client.post("/api/languages", json={"language_name": current_name})
        assert r2.status_code == 409


# =============================================================================
# REPOSITORIES
# =============================================================================

class TestRepositories:
    @pytest.fixture(scope="class")
    def repo(self, client, primary_user):
        r = client.post("/api/repos", json={
            "repo_name": f"repo_{uid()}",
            "description": "Test repo",
            "language_name": "Python",
        }, headers=auth(primary_user["token"]))
        assert r.status_code == 201
        return r.get_json()["data"]

    def test_create_repo(self, repo):
        assert "repo_id" in repo
        assert repo["stars"] == 0

    def test_list_repos(self, client):
        r = client.get("/api/repos")
        assert r.status_code == 200
        assert isinstance(r.get_json()["data"], list)

    def test_get_repo(self, client, repo):
        r = client.get(f"/api/repos/{repo['repo_id']}")
        assert r.status_code == 200
        assert r.get_json()["data"]["repo_id"] == repo["repo_id"]

    def test_get_repo_not_found(self, client):
        r = client.get("/api/repos/9999999")
        assert r.status_code == 404

    def test_patch_repo(self, client, repo, primary_user):
        r = client.patch(
            f"/api/repos/{repo['repo_id']}",
            json={"description": "Updated description"},
            headers=auth(primary_user["token"]),
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["description"] == "Updated description"

    def test_patch_repo_forbidden(self, client, repo, secondary_user):
        r = client.patch(
            f"/api/repos/{repo['repo_id']}",
            json={"description": "Hacked"},
            headers=auth(secondary_user["token"]),
        )
        assert r.status_code == 403

    def test_create_repo_requires_auth(self, client):
        r = client.post("/api/repos", json={"repo_name": f"r_{uid()}"})
        assert r.status_code == 401

    def test_duplicate_repo_name(self, client, repo, primary_user):
        r = client.post("/api/repos", json={
            "repo_name": repo["repo_name"],
        }, headers=auth(primary_user["token"]))
        assert r.status_code == 409


# =============================================================================
# TAGS
# =============================================================================

class TestTags:
    @pytest.fixture(scope="class")
    def tag(self, client):
        r = client.post("/api/tags", json={"tag_name": f"tag_{uid()}"})
        assert r.status_code == 201
        return r.get_json()["data"]

    def test_create_tag(self, tag):
        assert "tag_id" in tag

    def test_list_tags(self, client):
        r = client.get("/api/tags")
        assert r.status_code == 200

    def test_get_tag(self, client, tag):
        r = client.get(f"/api/tags/{tag['tag_id']}")
        assert r.status_code == 200

    def test_patch_tag(self, client, tag):
        new_name = f"tag_{uid()}"
        r = client.patch(f"/api/tags/{tag['tag_id']}", json={"tag_name": new_name})
        assert r.status_code == 200


# =============================================================================
# REPO TAGS (attach/detach)
# =============================================================================

class TestRepoTags:
    @pytest.fixture(scope="class")
    def setup(self, client, primary_user):
        repo_r = client.post("/api/repos", json={"repo_name": f"rt_{uid()}"}, headers=auth(primary_user["token"]))
        repo_id = repo_r.get_json()["data"]["repo_id"]
        tag_r = client.post("/api/tags", json={"tag_name": f"rt_{uid()}"})
        tag_id = tag_r.get_json()["data"]["tag_id"]
        return repo_id, tag_id

    def test_attach_tag(self, client, primary_user, setup):
        repo_id, tag_id = setup
        r = client.post(f"/api/repos/{repo_id}/tags/{tag_id}", headers=auth(primary_user["token"]))
        assert r.status_code == 201

    def test_attach_tag_idempotent(self, client, primary_user, setup):
        repo_id, tag_id = setup
        r = client.post(f"/api/repos/{repo_id}/tags/{tag_id}", headers=auth(primary_user["token"]))
        assert r.status_code == 201  # ON CONFLICT DO NOTHING still 201

    def test_detach_tag(self, client, primary_user, setup):
        repo_id, tag_id = setup
        r = client.delete(f"/api/repos/{repo_id}/tags/{tag_id}", headers=auth(primary_user["token"]))
        assert r.status_code == 200

    def test_attach_tag_forbidden(self, client, secondary_user, setup):
        repo_id, tag_id = setup
        r = client.post(f"/api/repos/{repo_id}/tags/{tag_id}", headers=auth(secondary_user["token"]))
        assert r.status_code == 403


# =============================================================================
# FOLLOW
# =============================================================================

class TestFollow:
    def test_follow_user(self, client, primary_user, secondary_user):
        r = client.post(
            f"/api/users/{secondary_user['user_id']}/follow",
            headers=auth(primary_user["token"]),
        )
        assert r.status_code == 200
        # Check following count increased
        r2 = client.get(f"/api/users/{primary_user['user_id']}")
        assert r2.get_json()["data"]["following"] >= 1

    def test_follow_self(self, client, primary_user):
        r = client.post(
            f"/api/users/{primary_user['user_id']}/follow",
            headers=auth(primary_user["token"]),
        )
        assert r.status_code == 400

    def test_unfollow_user(self, client, primary_user, secondary_user):
        r = client.delete(
            f"/api/users/{secondary_user['user_id']}/follow",
            headers=auth(primary_user["token"]),
        )
        assert r.status_code == 200

    def test_follow_creates_notification(self, client, primary_user, secondary_user):
        # Follow again to trigger notification
        client.post(
            f"/api/users/{secondary_user['user_id']}/follow",
            headers=auth(primary_user["token"]),
        )
        r = client.get("/api/notifications", headers=auth(secondary_user["token"]))
        assert r.status_code == 200
        notifications = r.get_json()["data"]
        assert any(str(primary_user["user_id"]) in n["message"] for n in notifications)


# =============================================================================
# STARS
# =============================================================================

class TestStars:
    @pytest.fixture(scope="class")
    def repo_id(self, client, primary_user):
        r = client.post("/api/repos", json={"repo_name": f"star_{uid()}"}, headers=auth(primary_user["token"]))
        return r.get_json()["data"]["repo_id"]

    def test_star_repo(self, client, secondary_user, repo_id):
        r = client.post(f"/api/repos/{repo_id}/star", headers=auth(secondary_user["token"]))
        assert r.status_code == 201
        # Check stars incremented
        r2 = client.get(f"/api/repos/{repo_id}")
        assert r2.get_json()["data"]["stars"] >= 1

    def test_star_idempotent(self, client, secondary_user, repo_id):
        r = client.post(f"/api/repos/{repo_id}/star", headers=auth(secondary_user["token"]))
        assert r.status_code == 201  # ON CONFLICT DO NOTHING

    def test_unstar_repo(self, client, secondary_user, repo_id):
        r = client.delete(f"/api/repos/{repo_id}/star", headers=auth(secondary_user["token"]))
        assert r.status_code == 200


# =============================================================================
# COMMENTS
# =============================================================================

class TestComments:
    @pytest.fixture(scope="class")
    def repo_id(self, client, primary_user):
        r = client.post("/api/repos", json={"repo_name": f"cmt_{uid()}"}, headers=auth(primary_user["token"]))
        return r.get_json()["data"]["repo_id"]

    @pytest.fixture(scope="class")
    def comment(self, client, primary_user, repo_id):
        r = client.post(
            f"/api/repos/{repo_id}/comments",
            json={"content": "Great repo!"},
            headers=auth(primary_user["token"]),
        )
        assert r.status_code == 201
        return r.get_json()["data"]

    def test_create_comment(self, comment):
        assert "comment_id" in comment
        assert comment["content"] == "Great repo!"

    def test_list_comments(self, client, repo_id):
        r = client.get(f"/api/repos/{repo_id}/comments")
        assert r.status_code == 200
        assert isinstance(r.get_json()["data"], list)

    def test_patch_comment(self, client, primary_user, comment):
        r = client.patch(
            f"/api/comments/{comment['comment_id']}",
            json={"content": "Updated comment"},
            headers=auth(primary_user["token"]),
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["content"] == "Updated comment"

    def test_patch_comment_forbidden(self, client, secondary_user, comment):
        r = client.patch(
            f"/api/comments/{comment['comment_id']}",
            json={"content": "Hacked"},
            headers=auth(secondary_user["token"]),
        )
        assert r.status_code == 403

    def test_delete_comment(self, client, primary_user, repo_id):
        r = client.post(
            f"/api/repos/{repo_id}/comments",
            json={"content": "To be deleted"},
            headers=auth(primary_user["token"]),
        )
        cid = r.get_json()["data"]["comment_id"]
        r = client.delete(f"/api/comments/{cid}", headers=auth(primary_user["token"]))
        assert r.status_code == 200


# =============================================================================
# NOTIFICATIONS
# =============================================================================

class TestNotifications:
    def test_list_notifications_auth_required(self, client):
        r = client.get("/api/notifications")
        assert r.status_code == 401

    def test_list_notifications(self, client, secondary_user):
        r = client.get("/api/notifications", headers=auth(secondary_user["token"]))
        assert r.status_code == 200
        assert isinstance(r.get_json()["data"], list)

    def test_mark_notification_read(self, client, primary_user, secondary_user):
        # Ensure there's a notification (follow creates one)
        client.post(
            f"/api/users/{secondary_user['user_id']}/follow",
            headers=auth(primary_user["token"]),
        )
        r = client.get("/api/notifications", headers=auth(secondary_user["token"]))
        notifications = r.get_json()["data"]
        if notifications:
            nid = notifications[0]["notification_id"]
            r2 = client.patch(f"/api/notifications/{nid}/read", headers=auth(secondary_user["token"]))
            assert r2.status_code == 200
            assert r2.get_json()["data"]["is_read"] is True


# =============================================================================
# CONTRIBUTORS
# =============================================================================

class TestContributors:
    @pytest.fixture(scope="class")
    def repo_id(self, client, primary_user):
        r = client.post("/api/repos", json={"repo_name": f"contrib_{uid()}"}, headers=auth(primary_user["token"]))
        return r.get_json()["data"]["repo_id"]

    def test_list_contributors(self, client, repo_id):
        r = client.get(f"/api/repos/{repo_id}/contributors")
        assert r.status_code == 200
        data = r.get_json()["data"]
        # Owner is auto-added by create_repository_proc
        assert len(data) >= 1
        assert data[0]["role"] == "owner"

    def test_add_contributor(self, client, primary_user, secondary_user, repo_id):
        r = client.post(
            f"/api/repos/{repo_id}/contributors",
            json={"user_id": secondary_user["user_id"], "role": "collaborator"},
            headers=auth(primary_user["token"]),
        )
        assert r.status_code == 201
        assert r.get_json()["data"]["role"] == "collaborator"

    def test_add_contributor_forbidden(self, client, secondary_user, repo_id):
        r = client.post(
            f"/api/repos/{repo_id}/contributors",
            json={"user_id": secondary_user["user_id"], "role": "collaborator"},
            headers=auth(secondary_user["token"]),
        )
        assert r.status_code == 403

    def test_remove_contributor(self, client, primary_user, secondary_user, repo_id):
        r = client.delete(
            f"/api/repos/{repo_id}/contributors/{secondary_user['user_id']}",
            headers=auth(primary_user["token"]),
        )
        assert r.status_code == 200


# =============================================================================
# SNAPSHOTS
# =============================================================================

class TestSnapshots:
    @pytest.fixture(scope="class")
    def snap_date(self):
        return "2024-01-15"

    def test_create_snapshot(self, client, primary_user, snap_date):
        r = client.post("/api/snapshots", json={
            "date": snap_date,
            "followers": 10,
            "repo_count": 3,
        }, headers=auth(primary_user["token"]))
        assert r.status_code == 201
        d = r.get_json()["data"]
        assert d["followers"] == 10

    def test_get_snapshot(self, client, primary_user, snap_date):
        r = client.get(f"/api/snapshots/{primary_user['user_id']}/{snap_date}")
        assert r.status_code == 200

    def test_list_snapshots(self, client, primary_user):
        r = client.get(f"/api/snapshots?user_id={primary_user['user_id']}")
        assert r.status_code == 200
        assert len(r.get_json()["data"]) >= 1

    def test_patch_snapshot(self, client, primary_user, snap_date):
        r = client.patch(
            f"/api/snapshots/{primary_user['user_id']}/{snap_date}",
            json={"followers": 20},
            headers=auth(primary_user["token"]),
        )
        assert r.status_code == 200
        assert r.get_json()["data"]["followers"] == 20

    def test_delete_snapshot(self, client, primary_user):
        # Create a throwaway snapshot
        r = client.post("/api/snapshots", json={
            "date": "2024-02-20",
            "followers": 5,
            "repo_count": 1,
        }, headers=auth(primary_user["token"]))
        assert r.status_code == 201
        r2 = client.delete(
            f"/api/snapshots/{primary_user['user_id']}/2024-02-20",
            headers=auth(primary_user["token"]),
        )
        assert r2.status_code == 200

    def test_snapshot_forbidden(self, client, secondary_user, primary_user, snap_date):
        r = client.patch(
            f"/api/snapshots/{primary_user['user_id']}/{snap_date}",
            json={"followers": 999},
            headers=auth(secondary_user["token"]),
        )
        assert r.status_code == 403


# =============================================================================
# ANALYTICS (views)
# =============================================================================

class TestAnalytics:
    def test_user_repo_summary(self, client):
        r = client.get("/api/analytics/user-repo-summary")
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert isinstance(data, list)
        if data:
            row = data[0]
            assert "user_id" in row
            assert "total_repos" in row
            assert "total_stars" in row

    def test_repo_engagement(self, client):
        r = client.get("/api/analytics/repo-engagement")
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert isinstance(data, list)
        if data:
            row = data[0]
            assert "repo_id" in row
            assert "comment_count" in row
            assert "contributor_count" in row


# =============================================================================
# ACTIVITY LOGS
# =============================================================================

class TestActivityLogs:
    def test_list_activity_logs(self, client):
        r = client.get("/api/activity-logs")
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert isinstance(data, list)
        # Should have entries from all our test actions
        assert len(data) > 0


# =============================================================================
# BACKUP LOGS
# =============================================================================

class TestBackupLogs:
    def test_list_backup_logs(self, client):
        r = client.get("/api/backup-logs")
        assert r.status_code == 200
        assert isinstance(r.get_json()["data"], list)


# =============================================================================
# DELETE USER (cleanup - must run last)
# =============================================================================

class TestDeleteUser:
    def test_delete_user_forbidden(self, client, primary_user, secondary_user):
        r = client.delete(
            f"/api/users/{primary_user['user_id']}",
            headers=auth(secondary_user["token"]),
        )
        assert r.status_code == 403

    def test_delete_own_user(self, client):
        uid_val, token, _, _ = register_and_login(client)
        r = client.delete(f"/api/users/{uid_val}", headers=auth(token))
        assert r.status_code == 200
        # Confirm gone
        r2 = client.get(f"/api/users/{uid_val}")
        assert r2.status_code == 404
