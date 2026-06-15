"""Tests for AD DS role management endpoints (SOP Steps 3-5)."""
import pytest
from fastapi.testclient import TestClient


INSTALL_PAYLOAD = {
    "vm_name": "DC01",
    "resource_group": "rg-ad-prod",
    "include_management_tools": True,
    "include_dns_server": True,
    "restart_if_required": True,
}

PROMOTE_PAYLOAD = {
    "vm_name": "DC01",
    "resource_group": "rg-ad-prod",
    "domain_name": "corp.contoso.com",
    "netbios_name": "CORP",
    "forest_mode": "WinThreshold",
    "domain_mode": "WinThreshold",
    "dsrm_password": "Dsrm@P@ssw0rd!Secure",
    "create_new_forest": True,
    "dns_delegation": False,
}


class TestADDSInstall:
    def test_install_returns_202(self, client: TestClient):
        resp = client.post("/ad-ds/install", json=INSTALL_PAYLOAD)
        assert resp.status_code == 202

    def test_install_roles_list_includes_adds(self, client: TestClient):
        resp = client.post("/ad-ds/install", json=INSTALL_PAYLOAD)
        data = resp.json()
        assert "AD-Domain-Services" in data["roles_installed"]

    def test_install_with_dns_includes_dns_role(self, client: TestClient):
        resp = client.post("/ad-ds/install", json=INSTALL_PAYLOAD)
        data = resp.json()
        assert "DNS" in data["roles_installed"]

    def test_install_without_dns_excludes_dns_role(self, client: TestClient):
        payload = {**INSTALL_PAYLOAD, "include_dns_server": False}
        resp = client.post("/ad-ds/install", json=payload)
        data = resp.json()
        assert "DNS" not in data["roles_installed"]

    def test_install_with_management_tools(self, client: TestClient):
        resp = client.post("/ad-ds/install", json=INSTALL_PAYLOAD)
        data = resp.json()
        assert "RSAT-ADDS" in data["roles_installed"]

    def test_install_missing_vm_name(self, client: TestClient):
        bad = {k: v for k, v in INSTALL_PAYLOAD.items() if k != "vm_name"}
        resp = client.post("/ad-ds/install", json=bad)
        assert resp.status_code == 422

    def test_install_job_id_returned(self, client: TestClient):
        resp = client.post("/ad-ds/install", json=INSTALL_PAYLOAD)
        data = resp.json()
        assert "job_id" in data
        assert len(data["job_id"]) == 36  # UUID4


class TestADDSPromote:
    def test_promote_returns_202(self, client: TestClient):
        resp = client.post("/ad-ds/promote", json=PROMOTE_PAYLOAD)
        assert resp.status_code == 202

    def test_promote_response_domain_name(self, client: TestClient):
        resp = client.post("/ad-ds/promote", json=PROMOTE_PAYLOAD)
        data = resp.json()
        assert data["domain_name"] == "corp.contoso.com"
        assert data["netbios_name"] == "CORP"

    def test_promote_invalid_domain_rejected(self, client: TestClient):
        bad = {**PROMOTE_PAYLOAD, "domain_name": "not-a-valid-domain"}
        resp = client.post("/ad-ds/promote", json=bad)
        assert resp.status_code == 422

    def test_promote_short_dsrm_password_rejected(self, client: TestClient):
        bad = {**PROMOTE_PAYLOAD, "dsrm_password": "short"}
        resp = client.post("/ad-ds/promote", json=bad)
        assert resp.status_code == 422

    def test_promote_restart_scheduled(self, client: TestClient):
        resp = client.post("/ad-ds/promote", json=PROMOTE_PAYLOAD)
        data = resp.json()
        assert data["restart_scheduled"] is True


class TestADDSStructure:
    def test_get_structure_200(self, client: TestClient):
        resp = client.get("/ad-ds/structure", params={"domain_name": "corp.contoso.com"})
        assert resp.status_code == 200

    def test_get_structure_fields(self, client: TestClient):
        resp = client.get("/ad-ds/structure", params={"domain_name": "corp.contoso.com"})
        data = resp.json()
        assert data["domain_name"] == "corp.contoso.com"
        assert "ou_tree" in data
        assert "domain_controllers" in data
        assert "functional_levels" in data

    def test_get_structure_ou_tree_has_nodes(self, client: TestClient):
        resp = client.get("/ad-ds/structure", params={"domain_name": "corp.contoso.com"})
        data = resp.json()
        assert len(data["ou_tree"]) > 0

    def test_get_structure_after_promote(self, client: TestClient):
        client.post("/ad-ds/promote", json=PROMOTE_PAYLOAD)
        resp = client.get("/ad-ds/structure", params={"domain_name": "corp.contoso.com"})
        data = resp.json()
        assert "DC01" in data["domain_controllers"]

    def test_get_structure_missing_domain_param(self, client: TestClient):
        resp = client.get("/ad-ds/structure")
        assert resp.status_code == 422
