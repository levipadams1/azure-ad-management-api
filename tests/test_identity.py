"""Tests for Identity management endpoints (SOP Steps 6-10)."""
import pytest
from fastapi.testclient import TestClient


USER_PAYLOAD = {
    "sam_account_name": "jdoe",
    "given_name": "John",
    "surname": "Doe",
    "display_name": "John Doe",
    "email": "jdoe@corp.contoso.com",
    "department": "Finance",
    "title": "Financial Analyst",
    "ou_path": "OU=Finance,OU=Users,DC=corp,DC=contoso,DC=com",
    "password": "P@ssw0rd!Temp123",
    "must_change_password": True,
    "account_enabled": True,
}

GROUP_PAYLOAD = {
    "group_name": "grp-finance-users",
    "display_name": "Finance Department Users",
    "description": "Security group for all Finance department users",
    "scope": "Global",
    "category": "Security",
    "ou_path": "OU=Groups,DC=corp,DC=contoso,DC=com",
}


class TestUserCreate:
    def test_create_user_returns_201(self, client: TestClient):
        resp = client.post("/identity/users", json=USER_PAYLOAD)
        assert resp.status_code == 201

    def test_create_user_response_fields(self, client: TestClient):
        resp = client.post("/identity/users", json=USER_PAYLOAD)
        data = resp.json()
        assert data["sam_account_name"] == "jdoe"
        assert data["status"] == "active"
        assert "distinguished_name" in data
        assert "object_guid" in data

    def test_create_user_duplicate_rejected_409(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        resp = client.post("/identity/users", json=USER_PAYLOAD)
        assert resp.status_code == 409

    def test_create_user_invalid_sam_rejected(self, client: TestClient):
        bad = {**USER_PAYLOAD, "sam_account_name": "1invalid"}
        resp = client.post("/identity/users", json=bad)
        assert resp.status_code == 422

    def test_create_user_short_password_rejected(self, client: TestClient):
        bad = {**USER_PAYLOAD, "password": "short"}
        resp = client.post("/identity/users", json=bad)
        assert resp.status_code == 422

    def test_create_user_with_groups_not_found(self, client: TestClient):
        payload = {**USER_PAYLOAD, "groups": ["nonexistent-group"]}
        resp = client.post("/identity/users", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "nonexistent-group" in data["groups_failed"]

    def test_create_user_with_existing_group(self, client: TestClient):
        client.post("/identity/groups", json=GROUP_PAYLOAD)
        payload = {**USER_PAYLOAD, "groups": ["grp-finance-users"]}
        resp = client.post("/identity/users", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "grp-finance-users" in data["groups_added"]

    def test_create_disabled_user(self, client: TestClient):
        payload = {**USER_PAYLOAD, "account_enabled": False}
        resp = client.post("/identity/users", json=payload)
        data = resp.json()
        assert data["status"] == "disabled"


class TestGroupCreate:
    def test_create_group_returns_201(self, client: TestClient):
        resp = client.post("/identity/groups", json=GROUP_PAYLOAD)
        assert resp.status_code == 201

    def test_create_group_response_fields(self, client: TestClient):
        resp = client.post("/identity/groups", json=GROUP_PAYLOAD)
        data = resp.json()
        assert data["group_name"] == "grp-finance-users"
        assert data["scope"] == "Global"
        assert data["category"] == "Security"
        assert "object_guid" in data

    def test_create_group_duplicate_rejected_409(self, client: TestClient):
        client.post("/identity/groups", json=GROUP_PAYLOAD)
        resp = client.post("/identity/groups", json=GROUP_PAYLOAD)
        assert resp.status_code == 409

    def test_create_group_with_initial_members(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        payload = {**GROUP_PAYLOAD, "members": ["jdoe"]}
        resp = client.post("/identity/groups", json=payload)
        data = resp.json()
        assert data["member_count"] == 1

    def test_create_distribution_group(self, client: TestClient):
        payload = {**GROUP_PAYLOAD, "group_name": "dl-finance", "category": "Distribution"}
        resp = client.post("/identity/groups", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["category"] == "Distribution"


class TestGroupMembers:
    def test_add_members_200(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        client.post("/identity/groups", json=GROUP_PAYLOAD)
        resp = client.post("/identity/groups/members", json={
            "group_name": "grp-finance-users",
            "members": ["jdoe"]
        })
        assert resp.status_code == 200

    def test_add_members_nonexistent_group_404(self, client: TestClient):
        resp = client.post("/identity/groups/members", json={
            "group_name": "nonexistent",
            "members": ["jdoe"]
        })
        assert resp.status_code == 404

    def test_add_nonexistent_user_fails(self, client: TestClient):
        client.post("/identity/groups", json=GROUP_PAYLOAD)
        resp = client.post("/identity/groups/members", json={
            "group_name": "grp-finance-users",
            "members": ["ghost"]
        })
        data = resp.json()
        assert "ghost" in data["members_failed"]

    def test_add_idempotent(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        client.post("/identity/groups", json=GROUP_PAYLOAD)
        client.post("/identity/groups/members", json={
            "group_name": "grp-finance-users", "members": ["jdoe"]
        })
        resp = client.post("/identity/groups/members", json={
            "group_name": "grp-finance-users", "members": ["jdoe"]
        })
        assert resp.status_code == 200


class TestPasswordReset:
    def test_reset_password_200(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        resp = client.post("/identity/users/reset-password", json={
            "sam_account_name": "jdoe",
            "new_password": "NewP@ssw0rd!2024",
            "must_change_at_logon": True,
            "unlock_account": True,
        })
        assert resp.status_code == 200

    def test_reset_password_response(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        resp = client.post("/identity/users/reset-password", json={
            "sam_account_name": "jdoe",
            "new_password": "NewP@ssw0rd!2024",
            "must_change_at_logon": False,
            "unlock_account": False,
        })
        data = resp.json()
        assert data["password_reset"] is True
        assert data["must_change_at_logon"] is False

    def test_reset_password_nonexistent_user_404(self, client: TestClient):
        resp = client.post("/identity/users/reset-password", json={
            "sam_account_name": "ghost",
            "new_password": "NewP@ssw0rd!2024",
        })
        assert resp.status_code == 404

    def test_reset_password_weak_new_password_rejected(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        resp = client.post("/identity/users/reset-password", json={
            "sam_account_name": "jdoe",
            "new_password": "alllowercase",
        })
        assert resp.status_code == 422


class TestAccountUnlock:
    def test_unlock_account_200(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        resp = client.post("/identity/users/unlock", json={
            "sam_account_name": "jdoe",
            "reason": "User called help desk",
        })
        assert resp.status_code == 200

    def test_unlock_nonexistent_user_404(self, client: TestClient):
        resp = client.post("/identity/users/unlock", json={"sam_account_name": "ghost"})
        assert resp.status_code == 404

    def test_unlock_not_locked_returns_message(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        resp = client.post("/identity/users/unlock", json={"sam_account_name": "jdoe"})
        data = resp.json()
        assert data["previously_locked"] is False
        assert data["unlocked"] is True


class TestAccountDisable:
    def test_disable_account_200(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        resp = client.post("/identity/users/disable", json={
            "sam_account_name": "jdoe",
            "reason": "Employee terminated HR#12345",
            "move_to_disabled_ou": True,
            "remove_group_memberships": False,
        })
        assert resp.status_code == 200

    def test_disable_account_response(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        resp = client.post("/identity/users/disable", json={
            "sam_account_name": "jdoe",
            "reason": "Employee terminated HR#12345",
            "move_to_disabled_ou": True,
            "remove_group_memberships": True,
        })
        data = resp.json()
        assert data["disabled"] is True
        assert data["moved_to_disabled_ou"] is True

    def test_disable_removes_groups(self, client: TestClient):
        client.post("/identity/groups", json=GROUP_PAYLOAD)
        payload = {**USER_PAYLOAD, "groups": ["grp-finance-users"]}
        client.post("/identity/users", json=payload)
        resp = client.post("/identity/users/disable", json={
            "sam_account_name": "jdoe",
            "reason": "Terminated",
            "remove_group_memberships": True,
        })
        data = resp.json()
        assert "grp-finance-users" in data["groups_removed"]

    def test_disable_nonexistent_user_404(self, client: TestClient):
        resp = client.post("/identity/users/disable", json={
            "sam_account_name": "ghost",
            "reason": "Does not exist",
        })
        assert resp.status_code == 404

    def test_disable_short_reason_rejected(self, client: TestClient):
        client.post("/identity/users", json=USER_PAYLOAD)
        resp = client.post("/identity/users/disable", json={
            "sam_account_name": "jdoe",
            "reason": "X",  # too short
        })
        assert resp.status_code == 422
