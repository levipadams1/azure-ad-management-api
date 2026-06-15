from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class GPOLinkStatus(str, Enum):
    ENABLED = "Enabled"
    DISABLED = "Disabled"
    ENFORCED = "Enforced"


class DriveLetterEnum(str, Enum):
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"


class PasswordPolicyRequest(BaseModel):
    gpo_name: str = Field(..., description="Name of the GPO to create or update", min_length=1, max_length=255)
    target_ou: str = Field(..., description="Distinguished Name of the OU to link the GPO to")
    min_password_length: int = Field(default=14, ge=8, le=128, description="Minimum password length (SOP: 14)")
    max_password_age_days: int = Field(default=90, ge=1, le=999, description="Maximum password age in days (SOP: 90)")
    min_password_age_days: int = Field(default=1, ge=0, le=998, description="Minimum password age in days (SOP: 1)")
    password_history_count: int = Field(default=24, ge=0, le=24, description="Number of remembered passwords (SOP: 24)")
    complexity_enabled: bool = Field(default=True, description="Enable complexity requirements (SOP: True)")
    reversible_encryption: bool = Field(default=False, description="Store passwords using reversible encryption (SOP: False)")
    account_lockout_threshold: int = Field(default=5, ge=0, le=999, description="Failed attempts before lockout (SOP: 5)")
    lockout_duration_minutes: int = Field(default=30, ge=1, le=99999, description="Account lockout duration in minutes (SOP: 30)")
    lockout_observation_window_minutes: int = Field(default=30, ge=1, le=99999, description="Reset lockout counter after N minutes (SOP: 30)")
    link_enabled: bool = Field(default=True, description="Enable the GPO link immediately")
    enforced: bool = Field(default=False, description="Enforce the GPO link (overrides block inheritance)")

    model_config = {"json_schema_extra": {
        "example": {
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
            "enforced": False
        }
    }}


class PasswordPolicyResponse(BaseModel):
    gpo_name: str
    gpo_id: str
    target_ou: str
    link_status: GPOLinkStatus
    settings_applied: dict
    message: str
    powershell_equivalent: str = Field(..., description="Equivalent PowerShell commands for audit trail")


class InactivityLockRequest(BaseModel):
    gpo_name: str = Field(..., description="Name of the GPO to create or update", min_length=1, max_length=255)
    target_ou: str = Field(..., description="Distinguished Name of the OU to link the GPO to")
    screen_saver_timeout_seconds: int = Field(default=600, ge=60, le=86400, description="Screen saver activation timeout (SOP: 600s = 10 min)")
    screen_saver_password_protected: bool = Field(default=True, description="Require password to unlock screen saver (SOP: True)")
    screen_saver_executable: str = Field(default="scrnsave.scr", description="Screen saver executable name")
    interactive_logon_message_title: Optional[str] = Field(default=None, description="Logon warning message title")
    interactive_logon_message_text: Optional[str] = Field(default=None, description="Logon warning message body")
    machine_inactivity_limit_seconds: int = Field(default=900, ge=0, le=599940, description="Machine account activity limit in seconds (SOP: 900s = 15 min)")
    link_enabled: bool = Field(default=True, description="Enable the GPO link immediately")
    enforced: bool = Field(default=False, description="Enforce the GPO link")

    model_config = {"json_schema_extra": {
        "example": {
            "gpo_name": "GPO-Inactivity-Lock-Corp",
            "target_ou": "OU=Workstations,DC=corp,DC=contoso,DC=com",
            "screen_saver_timeout_seconds": 600,
            "screen_saver_password_protected": True,
            "screen_saver_executable": "scrnsave.scr",
            "interactive_logon_message_title": "AUTHORIZED USE ONLY",
            "interactive_logon_message_text": "This system is for authorized use only. Unauthorized access is prohibited.",
            "machine_inactivity_limit_seconds": 900,
            "link_enabled": True,
            "enforced": False
        }
    }}


class InactivityLockResponse(BaseModel):
    gpo_name: str
    gpo_id: str
    target_ou: str
    link_status: GPOLinkStatus
    settings_applied: dict
    message: str
    powershell_equivalent: str


class StorageRestrictionRequest(BaseModel):
    gpo_name: str = Field(..., description="Name of the GPO to create or update", min_length=1, max_length=255)
    target_ou: str = Field(..., description="Distinguished Name of the OU to link the GPO to")
    block_removable_storage: bool = Field(default=True, description="Block all removable storage devices (USB drives, etc.) (SOP: True)")
    block_cd_dvd: bool = Field(default=True, description="Block CD/DVD drives (SOP: True)")
    block_floppy: bool = Field(default=True, description="Block floppy disk drives (SOP: True)")
    audit_removable_storage: bool = Field(default=True, description="Enable audit logging for removable storage access attempts (SOP: True)")
    allowed_drive_letters: Optional[List[DriveLetterEnum]] = Field(default=None, description="Drive letters explicitly whitelisted (e.g. D for corporate data drive)")
    deny_execute_from_removable: bool = Field(default=True, description="Deny execute access from removable storage (SOP: True)")
    deny_write_to_removable: bool = Field(default=True, description="Deny write access to removable storage (SOP: True)")
    link_enabled: bool = Field(default=True, description="Enable the GPO link immediately")
    enforced: bool = Field(default=False, description="Enforce the GPO link")

    model_config = {"json_schema_extra": {
        "example": {
            "gpo_name": "GPO-Storage-Restrictions-Corp",
            "target_ou": "OU=Workstations,DC=corp,DC=contoso,DC=com",
            "block_removable_storage": True,
            "block_cd_dvd": True,
            "block_floppy": True,
            "audit_removable_storage": True,
            "allowed_drive_letters": None,
            "deny_execute_from_removable": True,
            "deny_write_to_removable": True,
            "link_enabled": True,
            "enforced": False
        }
    }}


class StorageRestrictionResponse(BaseModel):
    gpo_name: str
    gpo_id: str
    target_ou: str
    link_status: GPOLinkStatus
    settings_applied: dict
    message: str
    powershell_equivalent: str


class GPOApplyRequest(BaseModel):
    target: str = Field(..., description="Target scope: 'domain', specific OU DN, or computer name")
    gpo_names: Optional[List[str]] = Field(default=None, description="Specific GPO names to force-apply; None = all applicable GPOs")
    force: bool = Field(default=True, description="Force policy refresh even if settings haven't changed")

    model_config = {"json_schema_extra": {
        "example": {
            "target": "OU=Workstations,DC=corp,DC=contoso,DC=com",
            "gpo_names": ["GPO-Password-Policy-Corp"],
            "force": True
        }
    }}


class GPOApplyResponse(BaseModel):
    target: str
    gpos_applied: List[str]
    errors: List[str] = Field(default_factory=list)
    message: str


class GPOSummary(BaseModel):
    gpo_name: str
    gpo_id: str
    target_ou: str
    link_status: GPOLinkStatus
    created_at: str
    modified_at: str
    category: str = Field(..., description="password_policy | inactivity_lock | storage_restriction | custom")


class GPOListResponse(BaseModel):
    total_count: int
    gpos: List[GPOSummary]
