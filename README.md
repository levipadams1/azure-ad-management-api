# Azure AD / Windows Server Management API

A **FastAPI** application that exposes a RESTful management API for common Active Directory Domain Services (AD DS), Virtual Machine, Identity, Group Policy, and Security Audit operations.  
Every endpoint traces directly to a numbered step in the Standard Operating Procedure (SOP) for provisioning and managing a Windows Server / Azure Active Directory environment.

---

## Table of Contents

1. [Architecture](#architecture)
2. [SOP ↔ Endpoint Mapping](#sop--endpoint-mapping)
3. [Quick Start](#quick-start)
4. [Endpoint Reference](#endpoint-reference)
   - [VM Management](#vm-management-sop-steps-12)
   - [AD DS Role Management](#ad-ds-role-management-sop-steps-35)
   - [Identity Management](#identity-management-sop-steps-610)
   - [GPO Configuration](#gpo-configuration-sop-steps-1114)
   - [Audit](#audit-sop-step-15)
5. [Data Models](#data-models)
6. [Project Structure](#project-structure)
7. [Running Tests](#running-tests)

---

## Architecture

```
azure_ad_api/
├── main.py              ← FastAPI app factory, router registration
├── models/              ← Pydantic v2 request / response schemas
│   ├── vm.py
│   ├── ad_ds.py
│   ├── identity.py
│   ├── gpo.py
│   └── audit.py
├── routers/             ← FastAPI APIRouter per domain area
│   ├── vm.py
│   ├── ad_ds.py
│   ├── identity.py
│   ├── gpo.py
│   └── audit.py
├── services/            ← Business logic (in-memory simulation for prototype)
│   ├── store.py         ← Shared in-memory state
│   ├── vm_service.py
│   ├── ad_ds_service.py
│   ├── identity_service.py
│   ├── gpo_service.py
│   └── audit_service.py
├── tests/               ← pytest test suite (92 tests)
├── requirements.txt
└── README.md
```

> **Note:** This prototype uses an **in-memory store** (`services/store.py`) for all data.  
> In production, replace the service layer with calls to the Azure Resource Manager SDK, Azure AD Graph API, or Active Directory PowerShell Remoting.

---

## SOP ↔ Endpoint Mapping

| SOP Step | Description | HTTP Method | Endpoint |
|---|---|---|---|
| **Step 1** | Provision a new Azure Virtual Machine | `POST` | `/vms` |
| **Step 2** | Restart VM (after role install / config) | `POST` | `/vms/restart` |
| **Step 3** | Install AD DS and DNS Server roles | `POST` | `/ad-ds/install` |
| **Step 4** | Promote VM to Domain Controller / create new forest | `POST` | `/ad-ds/promote` |
| **Step 5** | Verify AD DS structure (OUs, DCs, objects) | `GET` | `/ad-ds/structure` |
| **Step 6a** | Create a new AD user account | `POST` | `/identity/users` |
| **Step 6b** | Create a new security/distribution group | `POST` | `/identity/groups` |
| **Step 7** | Add members to an existing group | `POST` | `/identity/groups/members` |
| **Step 8** | Reset a user's password | `POST` | `/identity/users/reset-password` |
| **Step 9** | Unlock a locked-out account | `POST` | `/identity/users/unlock` |
| **Step 10** | Disable / off-board a user account | `POST` | `/identity/users/disable` |
| **Step 11** | Create/update Password Policy GPO | `POST` | `/gpo/password-policy` |
| **Step 12** | Create/update Inactivity Lock GPO | `POST` | `/gpo/inactivity-lock` |
| **Step 13** | Create/update Storage Restriction GPO | `POST` | `/gpo/storage-restrictions` |
| **Step 14** | Force GPO refresh on target OU / machine | `POST` | `/gpo/apply` |
| **Step 15** | Audit inactive user accounts | `POST` | `/audit/inactive-accounts` |

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Install & Run

```bash
cd azure_ad_api
pip install -r requirements.txt
python main.py
```

The API will start on **http://0.0.0.0:8000**.

| URL | Description |
|---|---|
| `http://localhost:8000/docs` | Swagger UI (interactive) |
| `http://localhost:8000/redoc` | ReDoc documentation |
| `http://localhost:8000/health` | Liveness probe |

---

## Endpoint Reference

### VM Management (SOP Steps 1–2)

#### `POST /vms` — Provision VM *(SOP Step 1)*

> *"Log in to the Azure portal and create a new Windows Server VM, specifying the resource group, VM size, OS image, VNet/subnet, admin credentials, and disk configuration."*

**Request body:**

```json
{
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
    "public_ip_enabled": false
  },
  "storage": {
    "os_disk_size_gb": 128,
    "os_disk_type": "Premium_LRS",
    "data_disk_size_gb": 50
  },
  "tags": { "environment": "production", "role": "domain-controller" }
}
```

**Response** `202 Accepted`:

```json
{
  "job_id": "b3d1a2c4-...",
  "vm_name": "DC01",
  "resource_group": "rg-ad-prod",
  "location": "eastus",
  "status": "provisioning",
  "message": "VM 'DC01' provisioning started ...",
  "estimated_completion_seconds": 300
}
```

**Validation rules:**
- `vm_name`: must start with a letter, max 15 chars
- `admin_password`: minimum 12 chars, must meet 3 of 4 complexity classes
- `os_disk_size_gb`: 30–4095 GB

---

#### `POST /vms/restart` — Restart VM *(SOP Step 2)*

> *"Restart the VM to complete feature installation (e.g. after AD DS role install)."*

```json
{
  "vm_name": "DC01",
  "resource_group": "rg-ad-prod",
  "force_restart": false
}
```

---

### AD DS Role Management (SOP Steps 3–5)

#### `POST /ad-ds/install` — Install AD DS Role *(SOP Step 3)*

#### `POST /ad-ds/promote` — Promote to Domain Controller *(SOP Step 4)*

#### `GET /ad-ds/structure?domain_name=corp.contoso.com` — Verify Structure *(SOP Step 5)*

---

### Identity Management (SOP Steps 6–10)

#### `POST /identity/users` — Create User *(SOP Step 6a)*
#### `POST /identity/groups` — Create Group *(SOP Step 6b)*
#### `POST /identity/groups/members` — Add Members *(SOP Step 7)*
#### `POST /identity/users/reset-password` — Reset Password *(SOP Step 8)*
#### `POST /identity/users/unlock` — Unlock Account *(SOP Step 9)*
#### `POST /identity/users/disable` — Disable Account *(SOP Step 10)*

---

### GPO Configuration (SOP Steps 11–14)

#### `POST /gpo/password-policy` — Password Policy GPO *(SOP Step 11)*
#### `POST /gpo/inactivity-lock` — Inactivity Lock GPO *(SOP Step 12)*
#### `POST /gpo/storage-restrictions` — Storage Restriction GPO *(SOP Step 13)*
#### `POST /gpo/apply` — Force GPO Refresh *(SOP Step 14)*

---

### Audit (SOP Step 15)

#### `POST /audit/inactive-accounts` — Inactive Account Audit *(SOP Step 15)*

---

## Running Tests

```bash
cd azure_ad_api
python -m pytest tests/ -v
```

The test suite includes **92 tests** covering:
- Happy path for every endpoint
- Validation failures (422) for malformed inputs
- Conflict detection (409) for duplicate resources
- Not-found errors (404) for missing resources
- Edge cases: duplicate group add (idempotent), threshold boundary checks, pagination

---

## Environment Variables (Production)

| Variable | Description |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | Service principal app ID |
| `AZURE_CLIENT_SECRET` | Service principal secret |
| `AD_DOMAIN_CONTROLLER` | FQDN of the primary DC for LDAP/WinRM |
| `AD_SERVICE_ACCOUNT` | Service account for AD operations |
| `AD_SERVICE_PASSWORD` | Service account password |

---

## License

MIT
