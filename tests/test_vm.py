"""Tests for VM management endpoints (SOP Steps 1-2)."""
import pytest
from fastapi.testclient import TestClient


VM_PAYLOAD = {
    "vm_name": "DC01",
    "resource_group": "rg-ad-prod",
    "location": "eastus",
    "vm_size": "Standard_D2s_v3",
    "os_image": "WindowsServer2022Datacenter",
    "admin_username": "azureadmin",
    "admin_password": "P@ssw0rd!Secure123",
    "network": {
        "virtual_network_name": "vnet-ad-prod",
        "subnet_name": "snet-dc",
        "public_ip_enabled": False,
    },
    "storage": {"os_disk_size_gb": 128, "os_disk_type": "Premium_LRS"},
}


class TestVMCreate:
    def test_create_vm_returns_202(self, client: TestClient):
        resp = client.post("/vms", json=VM_PAYLOAD)
        assert resp.status_code == 202

    def test_create_vm_response_fields(self, client: TestClient):
        resp = client.post("/vms", json=VM_PAYLOAD)
        data = resp.json()
        assert data["vm_name"] == "DC01"
        assert data["resource_group"] == "rg-ad-prod"
        assert data["location"] == "eastus"
        assert data["status"] == "provisioning"
        assert "job_id" in data
        assert data["estimated_completion_seconds"] == 300

    def test_create_vm_weak_password_rejected(self, client: TestClient):
        bad = {**VM_PAYLOAD, "admin_password": "weakpassword"}
        resp = client.post("/vms", json=bad)
        assert resp.status_code == 422

    def test_create_vm_invalid_name_rejected(self, client: TestClient):
        bad = {**VM_PAYLOAD, "vm_name": "1StartWithDigit"}
        resp = client.post("/vms", json=bad)
        assert resp.status_code == 422

    def test_create_vm_missing_required_fields(self, client: TestClient):
        resp = client.post("/vms", json={"vm_name": "DC01"})
        assert resp.status_code == 422

    def test_create_vm_custom_tags(self, client: TestClient):
        payload = {**VM_PAYLOAD, "tags": {"environment": "prod", "owner": "infra"}}
        resp = client.post("/vms", json=payload)
        assert resp.status_code == 202


class TestVMRestart:
    def test_restart_vm_returns_202(self, client: TestClient):
        payload = {"vm_name": "DC01", "resource_group": "rg-ad-prod"}
        resp = client.post("/vms/restart", json=payload)
        assert resp.status_code == 202

    def test_restart_vm_response_fields(self, client: TestClient):
        payload = {"vm_name": "DC01", "resource_group": "rg-ad-prod", "force_restart": False}
        resp = client.post("/vms/restart", json=payload)
        data = resp.json()
        assert data["vm_name"] == "DC01"
        assert data["status"] == "restarting"
        assert data["restart_type"] == "graceful"
        assert "job_id" in data

    def test_force_restart(self, client: TestClient):
        payload = {"vm_name": "DC01", "resource_group": "rg-ad-prod", "force_restart": True}
        resp = client.post("/vms/restart", json=payload)
        data = resp.json()
        assert data["restart_type"] == "force"

    def test_restart_missing_fields(self, client: TestClient):
        resp = client.post("/vms/restart", json={"vm_name": "DC01"})
        assert resp.status_code == 422
