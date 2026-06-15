import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException, status
from models.gpo import (
    PasswordPolicyRequest, PasswordPolicyResponse,
    InactivityLockRequest, InactivityLockResponse,
    StorageRestrictionRequest, StorageRestrictionResponse,
    GPOApplyRequest, GPOApplyResponse,
    GPOListResponse, GPOSummary, GPOLinkStatus,
)
from . import store


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _link_status(enabled: bool, enforced: bool) -> GPOLinkStatus:
    if enforced:
        return GPOLinkStatus.ENFORCED
    return GPOLinkStatus.ENABLED if enabled else GPOLinkStatus.DISABLED


class GPOService:
    # ── SOP Step 11 ── Configure Password Policy GPO ──────────────────────────
    def configure_password_policy(self, req: PasswordPolicyRequest) -> PasswordPolicyResponse:
        gpo_id = str(uuid.uuid4())
        link_status = _link_status(req.link_enabled, req.enforced)
        settings = {
            "MinimumPasswordLength": req.min_password_length,
            "MaximumPasswordAge": f"{req.max_password_age_days} days",
            "MinimumPasswordAge": f"{req.min_password_age_days} days",
            "PasswordHistorySize": req.password_history_count,
            "PasswordComplexity": req.complexity_enabled,
            "ReversibleEncryption": req.reversible_encryption,
            "AccountLockoutThreshold": req.account_lockout_threshold,
            "LockoutDuration": f"{req.lockout_duration_minutes} minutes",
            "LockoutObservationWindow": f"{req.lockout_observation_window_minutes} minutes",
        }

        store.gpos[req.gpo_name] = {
            "gpo_name": req.gpo_name,
            "gpo_id": gpo_id,
            "category": "password_policy",
            "target_ou": req.target_ou,
            "link_status": link_status,
            "settings": settings,
            "created_at": _now_iso(),
            "modified_at": _now_iso(),
        }

        ps_cmd = _build_password_policy_ps(req, gpo_id)

        return PasswordPolicyResponse(
            gpo_name=req.gpo_name,
            gpo_id=gpo_id,
            target_ou=req.target_ou,
            link_status=link_status,
            settings_applied=settings,
            message=f"Password policy GPO '{req.gpo_name}' created and linked to '{req.target_ou}'.",
            powershell_equivalent=ps_cmd,
        )

    # ── SOP Step 12 ── Configure Inactivity / Screen-Lock GPO ─────────────────
    def configure_inactivity_lock(self, req: InactivityLockRequest) -> InactivityLockResponse:
        gpo_id = str(uuid.uuid4())
        link_status = _link_status(req.link_enabled, req.enforced)
        settings = {
            "ScreenSaverTimeout": f"{req.screen_saver_timeout_seconds} seconds",
            "ScreenSaverPasswordProtected": req.screen_saver_password_protected,
            "ScreenSaverExecutable": req.screen_saver_executable,
            "MachineInactivityLimit": f"{req.machine_inactivity_limit_seconds} seconds",
            "LogonMessageTitle": req.interactive_logon_message_title,
            "LogonMessageText": req.interactive_logon_message_text,
        }

        store.gpos[req.gpo_name] = {
            "gpo_name": req.gpo_name,
            "gpo_id": gpo_id,
            "category": "inactivity_lock",
            "target_ou": req.target_ou,
            "link_status": link_status,
            "settings": settings,
            "created_at": _now_iso(),
            "modified_at": _now_iso(),
        }

        ps_cmd = _build_inactivity_lock_ps(req, gpo_id)

        return InactivityLockResponse(
            gpo_name=req.gpo_name,
            gpo_id=gpo_id,
            target_ou=req.target_ou,
            link_status=link_status,
            settings_applied=settings,
            message=f"Inactivity lock GPO '{req.gpo_name}' created and linked to '{req.target_ou}'.",
            powershell_equivalent=ps_cmd,
        )

    # ── SOP Step 13 ── Configure Storage Restriction GPO ──────────────────────
    def configure_storage_restriction(self, req: StorageRestrictionRequest) -> StorageRestrictionResponse:
        gpo_id = str(uuid.uuid4())
        link_status = _link_status(req.link_enabled, req.enforced)
        settings = {
            "BlockRemovableStorage": req.block_removable_storage,
            "BlockCdDvd": req.block_cd_dvd,
            "BlockFloppy": req.block_floppy,
            "AuditRemovableStorage": req.audit_removable_storage,
            "DenyExecuteFromRemovable": req.deny_execute_from_removable,
            "DenyWriteToRemovable": req.deny_write_to_removable,
            "AllowedDriveLetters": [d.value for d in req.allowed_drive_letters] if req.allowed_drive_letters else [],
        }

        store.gpos[req.gpo_name] = {
            "gpo_name": req.gpo_name,
            "gpo_id": gpo_id,
            "category": "storage_restriction",
            "target_ou": req.target_ou,
            "link_status": link_status,
            "settings": settings,
            "created_at": _now_iso(),
            "modified_at": _now_iso(),
        }

        ps_cmd = _build_storage_restriction_ps(req, gpo_id)

        return StorageRestrictionResponse(
            gpo_name=req.gpo_name,
            gpo_id=gpo_id,
            target_ou=req.target_ou,
            link_status=link_status,
            settings_applied=settings,
            message=f"Storage restriction GPO '{req.gpo_name}' created and linked to '{req.target_ou}'.",
            powershell_equivalent=ps_cmd,
        )

    # ── SOP Step 14 ── Force GPO Refresh ──────────────────────────────────────
    def apply_gpo(self, req: GPOApplyRequest) -> GPOApplyResponse:
        applied: List[str] = []
        errors: List[str] = []

        if req.gpo_names:
            for gpo_name in req.gpo_names:
                if gpo_name in store.gpos:
                    applied.append(gpo_name)
                else:
                    errors.append(f"GPO '{gpo_name}' not found in store")
        else:
            applied = list(store.gpos.keys())

        return GPOApplyResponse(
            target=req.target,
            gpos_applied=applied,
            errors=errors,
            message=(
                f"GPO refresh triggered on target '{req.target}'. "
                f"Applied: {len(applied)}, Errors: {len(errors)}."
            ),
        )

    def list_gpos(self) -> GPOListResponse:
        summaries = [
            GPOSummary(
                gpo_name=g["gpo_name"],
                gpo_id=g["gpo_id"],
                target_ou=g["target_ou"],
                link_status=g["link_status"],
                created_at=g["created_at"],
                modified_at=g["modified_at"],
                category=g["category"],
            )
            for g in store.gpos.values()
        ]
        return GPOListResponse(total_count=len(summaries), gpos=summaries)


# ── PowerShell snippet builders (audit trail helpers) ─────────────────────────

def _build_password_policy_ps(req: PasswordPolicyRequest, gpo_id: str) -> str:
    return (
        f'New-GPO -Name "{req.gpo_name}" | New-GPLink -Target "{req.target_ou}"\n'
        f'Set-GPRegistryValue -Name "{req.gpo_name}" -Key "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" '
        f'-ValueName "MinimumPasswordLength" -Type DWord -Value {req.min_password_length}\n'
        f'# AccountLockoutThreshold={req.account_lockout_threshold}, LockoutDuration={req.lockout_duration_minutes}min'
    )


def _build_inactivity_lock_ps(req: InactivityLockRequest, gpo_id: str) -> str:
    return (
        f'New-GPO -Name "{req.gpo_name}" | New-GPLink -Target "{req.target_ou}"\n'
        f'Set-GPRegistryValue -Name "{req.gpo_name}" '
        f'-Key "HKCU\\Software\\Policies\\Microsoft\\Windows\\Control Panel\\Desktop" '
        f'-ValueName "ScreenSaveTimeOut" -Type String -Value "{req.screen_saver_timeout_seconds}"\n'
        f'Set-GPRegistryValue -Name "{req.gpo_name}" '
        f'-Key "HKCU\\Software\\Policies\\Microsoft\\Windows\\Control Panel\\Desktop" '
        f'-ValueName "ScreenSaverIsSecure" -Type String -Value "{"1" if req.screen_saver_password_protected else "0"}"'
    )


def _build_storage_restriction_ps(req: StorageRestrictionRequest, gpo_id: str) -> str:
    deny_val = "1" if req.block_removable_storage else "0"
    return (
        f'New-GPO -Name "{req.gpo_name}" | New-GPLink -Target "{req.target_ou}"\n'
        f'Set-GPRegistryValue -Name "{req.gpo_name}" '
        f'-Key "HKLM\\Software\\Policies\\Microsoft\\Windows\\RemovableStorageDevices" '
        f'-ValueName "Deny_All" -Type DWord -Value {deny_val}\n'
        f'# Audit: {req.audit_removable_storage}, DenyWrite: {req.deny_write_to_removable}, DenyExecute: {req.deny_execute_from_removable}'
    )
