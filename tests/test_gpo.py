"""Tests for GPO configuration endpoints (SOP Steps 11-14)."""
import pytest
from fastapi.testclient import TestClient


PASSWORD_POLICY_PAYLOAD = {
    "gpo_name": "GPO-Password-Policy-Corp",
    "target_ou": "DC=corp,DC=contoso,DC=com",
    "min_password_length": 14,
    "max_password_age_days": 90,
    "min_password_age_days": 1,
    "password_history_count": 24,
    "complexity_enabled": True,
    "reversible_encryption": False,
    "account_lockout_threshold": 5,
    "lockout_duration_minutes": 30,
    "lockout_observation_window_minutes": 30,
    "link_enabled": True,
    "enforced": False,
}

INACTIVITY_LOCK_PAYLOAD = {
    "gpo_name": "GPO-Inactivity-Lock-Corp",
    "target_ou": "OU=Workstations,DC=corp,DC=contoso,DC=com",
    "screen_saver_timeout_seconds": 600,
    "screen_saver_password_protected": True,
    "machine_inactivity_limit_seconds": 900,
    "link_enabled": True,
    "enforced": False,
}

STORAGE_RESTRICTION_PAYLOAD = {
    "gpo_name": "GPO-Storage-Restrictions-Corp",
    "target_ou": "OU=Workstations,DC=corp,DC=contoso,DC=com",
    "block_removable_storage": True,
    "block_cd_dvd": True,
    "block_floppy": True,
    "audit_removable_storage": True,
    "deny_execute_from_removable": True,
    "deny_write_to_removable": True,
    "link_enabled": True,
    "enforced": False,
}


class TestPasswordPolicyGPO:
    def test_create_password_policy_returns_201(self, client: TestClient):
        resp = client.post("/gpo/password-policy", json=PASSWORD_POLICY_PAYLOAD)
        assert resp.status_code == 201

    def test_create_password_policy_response_fields(self, client: TestClient):
        resp = client.post("/gpo/password-policy", json=PASSWORD_POLICY_PAYLOAD)
        data = resp.json()
        assert data["gpo_name"] == "GPO-Password-Policy-Corp"
        assert data["target_ou"] == "DC=corp,DC=contoso,DC=com"
        assert data["link_status"] == "Enabled"
        assert "settings_applied" in data
        assert "gpo_id" in data
        assert "powershell_equivalent" in data

    def test_password_policy_settings_values(self, client: TestClient):
        resp = client.post("/gpo/password-policy", json=PASSWORD_POLICY_PAYLOAD)
        settings = resp.json()["settings_applied"]
        assert settings["MinimumPasswordLength"] == 14
        assert settings["PasswordHistorySize"] == 24
        assert settings["PasswordComplexity"] is True
        assert settings["ReversibleEncryption"] is False
        assert settings["AccountLockoutThreshold"] == 5

    def test_enforced_gpo_link_status(self, client: TestClient):
        payload = {**PASSWORD_POLICY_PAYLOAD, "enforced": True}
        resp = client.post("/gpo/password-policy", json=payload)
        assert resp.json()["link_status"] == "Enforced"

    def test_disabled_gpo_link_status(self, client: TestClient):
        payload = {**PASSWORD_POLICY_PAYLOAD, "link_enabled": False}
        resp = client.post("/gpo/password-policy", json=payload)
        assert resp.json()["link_status"] == "Disabled"

    def test_min_password_length_too_short_rejected(self, client: TestClient):
        bad = {**PASSWORD_POLICY_PAYLOAD, "min_password_length": 3}
        resp = client.post("/gpo/password-policy", json=bad)
        assert resp.status_code == 422

    def test_powershell_equivalent_present(self, client: TestClient):
        resp = client.post("/gpo/password-policy", json=PASSWORD_POLICY_PAYLOAD)
        ps = resp.json()["powershell_equivalent"]
        assert "GPO-Password-Policy-Corp" in ps


class TestInactivityLockGPO:
    def test_create_inactivity_lock_returns_201(self, client: TestClient):
        resp = client.post("/gpo/inactivity-lock", json=INACTIVITY_LOCK_PAYLOAD)
        assert resp.status_code == 201

    def test_inactivity_lock_response_fields(self, client: TestClient):
        resp = client.post("/gpo/inactivity-lock", json=INACTIVITY_LOCK_PAYLOAD)
        data = resp.json()
        assert data["gpo_name"] == "GPO-Inactivity-Lock-Corp"
        assert "settings_applied" in data
        assert "powershell_equivalent" in data

    def test_inactivity_lock_settings(self, client: TestClient):
        resp = client.post("/gpo/inactivity-lock", json=INACTIVITY_LOCK_PAYLOAD)
        settings = resp.json()["settings_applied"]
        assert "600 seconds" in settings["ScreenSaverTimeout"]
        assert settings["ScreenSaverPasswordProtected"] is True
        assert "900 seconds" in settings["MachineInactivityLimit"]

    def test_logon_message_stored(self, client: TestClient):
        payload = {
            **INACTIVITY_LOCK_PAYLOAD,
            "interactive_logon_message_title": "AUTHORIZED USE ONLY",
            "interactive_logon_message_text": "This system is authorized use only.",
        }
        resp = client.post("/gpo/inactivity-lock", json=payload)
        settings = resp.json()["settings_applied"]
        assert settings["LogonMessageTitle"] == "AUTHORIZED USE ONLY"

    def test_screen_saver_timeout_too_low_rejected(self, client: TestClient):
        bad = {**INACTIVITY_LOCK_PAYLOAD, "screen_saver_timeout_seconds": 10}
        resp = client.post("/gpo/inactivity-lock", json=bad)
        assert resp.status_code == 422


class TestStorageRestrictionGPO:
    def test_create_storage_restriction_returns_201(self, client: TestClient):
        resp = client.post("/gpo/storage-restrictions", json=STORAGE_RESTRICTION_PAYLOAD)
        assert resp.status_code == 201

    def test_storage_restriction_response_fields(self, client: TestClient):
        resp = client.post("/gpo/storage-restrictions", json=STORAGE_RESTRICTION_PAYLOAD)
        data = resp.json()
        assert data["gpo_name"] == "GPO-Storage-Restrictions-Corp"
        assert "settings_applied" in data
        assert "powershell_equivalent" in data

    def test_storage_restriction_settings(self, client: TestClient):
        resp = client.post("/gpo/storage-restrictions", json=STORAGE_RESTRICTION_PAYLOAD)
        settings = resp.json()["settings_applied"]
        assert settings["BlockRemovableStorage"] is True
        assert settings["BlockCdDvd"] is True
        assert settings["AuditRemovableStorage"] is True
        assert settings["DenyWriteToRemovable"] is True

    def test_allowed_drive_letters_stored(self, client: TestClient):
        payload = {**STORAGE_RESTRICTION_PAYLOAD, "allowed_drive_letters": ["D"]}
        resp = client.post("/gpo/storage-restrictions", json=payload)
        settings = resp.json()["settings_applied"]
        assert "D" in settings["AllowedDriveLetters"]


class TestGPOApply:
    def test_apply_gpo_returns_202(self, client: TestClient):
        client.post("/gpo/password-policy", json=PASSWORD_POLICY_PAYLOAD)
        resp = client.post("/gpo/apply", json={
            "target": "DC=corp,DC=contoso,DC=com",
            "force": True,
        })
        assert resp.status_code == 202

    def test_apply_specific_gpo(self, client: TestClient):
        client.post("/gpo/password-policy", json=PASSWORD_POLICY_PAYLOAD)
        resp = client.post("/gpo/apply", json={
            "target": "DC=corp,DC=contoso,DC=com",
            "gpo_names": ["GPO-Password-Policy-Corp"],
            "force": True,
        })
        data = resp.json()
        assert "GPO-Password-Policy-Corp" in data["gpos_applied"]

    def test_apply_nonexistent_gpo_reports_error(self, client: TestClient):
        resp = client.post("/gpo/apply", json={
            "target": "DC=corp,DC=contoso,DC=com",
            "gpo_names": ["GPO-Does-Not-Exist"],
            "force": True,
        })
        data = resp.json()
        assert len(data["errors"]) > 0


class TestGPOList:
    def test_list_gpos_empty(self, client: TestClient):
        resp = client.get("/gpo")
        assert resp.status_code == 200
        assert resp.json()["total_count"] == 0

    def test_list_gpos_after_creation(self, client: TestClient):
        client.post("/gpo/password-policy", json=PASSWORD_POLICY_PAYLOAD)
        client.post("/gpo/inactivity-lock", json=INACTIVITY_LOCK_PAYLOAD)
        resp = client.get("/gpo")
        data = resp.json()
        assert data["total_count"] == 2
        names = [g["gpo_name"] for g in data["gpos"]]
        assert "GPO-Password-Policy-Corp" in names
        assert "GPO-Inactivity-Lock-Corp" in names
