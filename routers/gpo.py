from fastapi import APIRouter
from models.gpo import (
    PasswordPolicyRequest, PasswordPolicyResponse,
    InactivityLockRequest, InactivityLockResponse,
    StorageRestrictionRequest, StorageRestrictionResponse,
    GPOApplyRequest, GPOApplyResponse,
    GPOListResponse,
)
from services.gpo_service import GPOService

router = APIRouter(prefix="/gpo", tags=["GPO Configuration"])
_svc = GPOService()


@router.get(
    "",
    response_model=GPOListResponse,
    summary="List all configured GPOs",
    description="Returns a summary of all Group Policy Objects configured through this API.",
)
def list_gpos() -> GPOListResponse:
    return _svc.list_gpos()


@router.post(
    "/password-policy",
    response_model=PasswordPolicyResponse,
    status_code=201,
    summary="Create/update password policy GPO",
    description=(
        "**SOP Step 11 — Password Policy GPO**\n\n"
        "Creates a new GPO (or updates an existing one) enforcing the domain password policy. "
        "Maps to SOP step: *'Open Group Policy Management Console → Create a GPO → "
        "Computer Configuration → Windows Settings → Security Settings → Account Policies → Password Policy'*. "
        "SOP defaults: min length = **14**, max age = **90 days**, history = **24**, complexity = **enabled**, "
        "lockout threshold = **5**, lockout duration = **30 min**. "
        "Returns the equivalent PowerShell commands for audit trail."
    ),
)
def configure_password_policy(req: PasswordPolicyRequest) -> PasswordPolicyResponse:
    return _svc.configure_password_policy(req)


@router.post(
    "/inactivity-lock",
    response_model=InactivityLockResponse,
    status_code=201,
    summary="Create/update inactivity screen-lock GPO",
    description=(
        "**SOP Step 12 — Inactivity Lock GPO**\n\n"
        "Creates a GPO that locks workstations after a period of inactivity. "
        "Maps to SOP step: *'In GPMC, create GPO → User Configuration → Administrative Templates → "
        "Control Panel → Personalization → Screen saver timeout (600 s), Screen saver password-protected = Enabled'*. "
        "SOP defaults: screen-saver timeout = **600 s (10 min)**, password-protected = **True**, "
        "machine inactivity limit = **900 s (15 min)**."
    ),
)
def configure_inactivity_lock(req: InactivityLockRequest) -> InactivityLockResponse:
    return _svc.configure_inactivity_lock(req)


@router.post(
    "/storage-restrictions",
    response_model=StorageRestrictionResponse,
    status_code=201,
    summary="Create/update removable storage restriction GPO",
    description=(
        "**SOP Step 13 — Storage Restriction GPO**\n\n"
        "Creates a GPO that blocks or restricts removable storage devices (USB, CD/DVD). "
        "Maps to SOP step: *'In GPMC, create GPO → Computer Configuration → Policies → "
        "Administrative Templates → System → Removable Storage Access → set Deny all access'*. "
        "SOP defaults: block USB = **True**, block CD/DVD = **True**, audit access = **True**, "
        "deny write = **True**, deny execute = **True**."
    ),
)
def configure_storage_restrictions(req: StorageRestrictionRequest) -> StorageRestrictionResponse:
    return _svc.configure_storage_restriction(req)


@router.post(
    "/apply",
    response_model=GPOApplyResponse,
    status_code=202,
    summary="Force GPO refresh on a target OU or computer",
    description=(
        "**SOP Step 14 — Force GPO Refresh**\n\n"
        "Triggers an immediate Group Policy refresh (`gpupdate /force`) on the specified target. "
        "Maps to SOP step: *'Run gpupdate /force on target machines or use Invoke-GPUpdate '* "
        "to ensure all GPO settings are applied without waiting for the default 90-minute refresh interval."
    ),
)
def apply_gpo(req: GPOApplyRequest) -> GPOApplyResponse:
    return _svc.apply_gpo(req)
