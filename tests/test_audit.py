"""Tests for audit endpoint (SOP Step 15)."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from services import store
from models.identity import AccountStatus


def seed_users():
    now = datetime.now(timezone.utc)
    store.users["jsmith"] = {
        "sam_account_name": "jsmith",
        "display_name": "Jane Smith",
        "distinguished_name": "CN=Jane Smith,OU=Users,OU=Corp,DC=corp,DC=contoso,DC=com",
        "email": "jsmith@corp.contoso.com",
        "department": "Finance",
        "last_logon_date": None,
        "status": AccountStatus.ACTIVE,
        "password_last_set": (now - timedelta(days=120)).isoformat(),
        "manager_sam": None,
        "locked": False,
    }
    store.users["bwilson"] = {
        "sam_account_name": "bwilson",
        "display_name": "Bob Wilson",
        "distinguished_name": "CN=Bob Wilson,OU=Users,OU=Corp,DC=corp,DC=contoso,DC=com",
        "email": "bwilson@corp.contoso.com",
        "department": "IT",
        "last_logon_date": (now - timedelta(days=120)).isoformat(),
        "status": AccountStatus.ACTIVE,
        "password_last_set": (now - timedelta(days=95)).isoformat(),
        "manager_sam": None,
        "locked": False,
    }
    store.users["cjones"] = {
        "sam_account_name": "cjones",
        "display_name": "Carol Jones",
        "distinguished_name": "CN=Carol Jones,OU=Users,OU=Corp,DC=corp,DC=contoso,DC=com",
        "email": "cjones@corp.contoso.com",
        "department": "HR",
        "last_logon_date": (now - timedelta(days=5)).isoformat(),
        "status": AccountStatus.ACTIVE,
        "password_last_set": (now - timedelta(days=10)).isoformat(),
        "manager_sam": None,
        "locked": False,
    }
    store.users["tdisabled"] = {
        "sam_account_name": "tdisabled",
        "display_name": "Tom Disabled",
        "distinguished_name": "CN=Tom Disabled,OU=Disabled,DC=corp,DC=contoso,DC=com",
        "email": "tdisabled@corp.contoso.com",
        "department": "Finance",
        "last_logon_date": (now - timedelta(days=200)).isoformat(),
        "status": AccountStatus.DISABLED,
        "password_last_set": (now - timedelta(days=200)).isoformat(),
        "manager_sam": None,
        "locked": False,
    }


AUDIT_PAYLOAD = {
    "inactivity_threshold_days": 90,
    "include_never_logged_in": True,
    "include_disabled": False,
    "include_computers": False,
    "page": 1,
    "page_size": 50,
}


class TestInactiveAccounts:
    def test_audit_returns_200(self, client: TestClient):
        resp = client.post("/audit/inactive-accounts", json=AUDIT_PAYLOAD)
        assert resp.status_code == 200

    def test_audit_empty_store_uses_demo_data(self, client: TestClient):
        # Store is empty → demo data kicks in
        resp = client.post("/audit/inactive-accounts", json=AUDIT_PAYLOAD)
        data = resp.json()
        assert data["summary"]["total_accounts_scanned"] > 0

    def test_audit_detects_inactive_user(self, client: TestClient):
        seed_users()
        resp = client.post("/audit/inactive-accounts", json=AUDIT_PAYLOAD)
        data = resp.json()
        sams = [a["sam_account_name"] for a in data["accounts"]]
        assert "bwilson" in sams  # 120 days > threshold 90

    def test_audit_detects_never_logged_in(self, client: TestClient):
        seed_users()
        resp = client.post("/audit/inactive-accounts", json=AUDIT_PAYLOAD)
        data = resp.json()
        sams = [a["sam_account_name"] for a in data["accounts"]]
        assert "jsmith" in sams

    def test_audit_excludes_active_recent(self, client: TestClient):
        seed_users()
        resp = client.post("/audit/inactive-accounts", json=AUDIT_PAYLOAD)
        data = resp.json()
        sams = [a["sam_account_name"] for a in data["accounts"]]
        assert "cjones" not in sams  # logged in 5 days ago

    def test_audit_excludes_disabled_by_default(self, client: TestClient):
        seed_users()
        resp = client.post("/audit/inactive-accounts", json=AUDIT_PAYLOAD)
        data = resp.json()
        sams = [a["sam_account_name"] for a in data["accounts"]]
        assert "tdisabled" not in sams

    def test_audit_includes_disabled_when_flag_set(self, client: TestClient):
        seed_users()
        payload = {**AUDIT_PAYLOAD, "include_disabled": True}
        resp = client.post("/audit/inactive-accounts", json=payload)
        data = resp.json()
        sams = [a["sam_account_name"] for a in data["accounts"]]
        assert "tdisabled" in sams

    def test_audit_summary_fields(self, client: TestClient):
        seed_users()
        resp = client.post("/audit/inactive-accounts", json=AUDIT_PAYLOAD)
        summary = resp.json()["summary"]
        assert "total_accounts_scanned" in summary
        assert "inactive_count" in summary
        assert "never_logged_in_count" in summary
        assert "recommended_disable_count" in summary

    def test_audit_recommended_action_for_never_logged_in(self, client: TestClient):
        seed_users()
        resp = client.post("/audit/inactive-accounts", json=AUDIT_PAYLOAD)
        accounts = resp.json()["accounts"]
        jsmith = next((a for a in accounts if a["sam_account_name"] == "jsmith"), None)
        assert jsmith is not None
        assert jsmith["recommended_action"] == "disable"

    def test_audit_pagination_fields(self, client: TestClient):
        seed_users()
        resp = client.post("/audit/inactive-accounts", json={**AUDIT_PAYLOAD, "page_size": 1})
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 1
        assert "total_pages" in data
        assert "has_next_page" in data

    def test_audit_pagination_page2(self, client: TestClient):
        seed_users()
        resp = client.post("/audit/inactive-accounts", json={**AUDIT_PAYLOAD, "page": 2, "page_size": 1})
        assert resp.status_code == 200

    def test_audit_threshold_change(self, client: TestClient):
        seed_users()
        # With 10-day threshold, cjones (5 days inactive) should NOT appear, bwilson (120) should
        resp = client.post("/audit/inactive-accounts", json={**AUDIT_PAYLOAD, "inactivity_threshold_days": 10})
        data = resp.json()
        sams = [a["sam_account_name"] for a in data["accounts"]]
        assert "bwilson" in sams

    def test_audit_response_structure(self, client: TestClient):
        resp = client.post("/audit/inactive-accounts", json=AUDIT_PAYLOAD)
        data = resp.json()
        assert "threshold_days" in data
        assert "generated_at" in data
        assert "summary" in data
        assert "accounts" in data
        assert data["threshold_days"] == 90


class TestHealthEndpoints:
    def test_root_200(self, client: TestClient):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_health_200(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
