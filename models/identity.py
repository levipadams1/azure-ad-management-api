from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator
import re


class AccountStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    LOCKED = "locked"
    EXPIRED = "expired"
    PASSWORD_EXPIRED = "password_expired"


class GroupScope(str, Enum):
    DOMAIN_LOCAL = "DomainLocal"
    GLOBAL = "Global"
    UNIVERSAL = "Universal"


class GroupCategory(str, Enum):
    SECURITY = "Security"
    DISTRIBUTION = "Distribution"


class UserCreateRequest(BaseModel):
    sam_account_name: str = Field(..., description="sAMAccountName / logon name (≤20 chars)", max_length=20)
    given_name: str = Field(..., description="First name", min_length=1, max_length=64)
    surname: str = Field(..., description="Last name", min_length=1, max_length=64)
    display_name: Optional[str] = Field(default=None, description="Full display name; auto-generated if omitted")
    email: Optional[str] = Field(default=None, description="User email address")
    department: Optional[str] = Field(default=None, description="Department name", max_length=64)
    title: Optional[str] = Field(default=None, description="Job title", max_length=128)
    manager_sam: Optional[str] = Field(default=None, description="sAMAccountName of the user's manager")
    ou_path: str = Field(..., description="Distinguished Name of the target OU (e.g. OU=Finance,DC=corp,DC=contoso,DC=com)")
    password: str = Field(..., description="Initial password; must meet domain complexity policy", min_length=12)
    must_change_password: bool = Field(default=True, description="Force password change at next logon")
    account_enabled: bool = Field(default=True, description="Enable the account immediately after creation")
    groups: Optional[List[str]] = Field(default=None, description="List of group sAMAccountNames to add the user to")

    @field_validator("sam_account_name")
    @classmethod
    def validate_sam(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9._\-]{0,19}$", v):
            raise ValueError("sAMAccountName must start with a letter and contain only alphanumeric, dot, hyphen, or underscore characters")
        return v.lower()

    model_config = {"json_schema_extra": {
        "example": {
            "sam_account_name": "jdoe",
            "given_name": "John",
            "surname": "Doe",
            "display_name": "John Doe",
            "email": "jdoe@corp.contoso.com",
            "department": "Finance",
            "title": "Financial Analyst",
            "manager_sam": "msmith",
            "ou_path": "OU=Finance,OU=Users,DC=corp,DC=contoso,DC=com",
            "password": "P@ssw0rd!Temp123",
            "must_change_password": True,
            "account_enabled": True,
            "groups": ["grp-finance-users", "grp-vpn-access"]
        }
    }}


class UserCreateResponse(BaseModel):
    sam_account_name: str
    distinguished_name: str
    object_guid: str
    status: AccountStatus
    message: str
    groups_added: List[str] = Field(default_factory=list)
    groups_failed: List[str] = Field(default_factory=list)


class GroupCreateRequest(BaseModel):
    group_name: str = Field(..., description="Group sAMAccountName", min_length=1, max_length=64)
    display_name: Optional[str] = Field(default=None, description="Display name; defaults to group_name")
    description: Optional[str] = Field(default=None, description="Group description", max_length=256)
    scope: GroupScope = Field(default=GroupScope.GLOBAL, description="Group scope")
    category: GroupCategory = Field(default=GroupCategory.SECURITY, description="Group category")
    ou_path: str = Field(..., description="Distinguished Name of the target OU")
    members: Optional[List[str]] = Field(default=None, description="Initial member sAMAccountNames")
    managed_by: Optional[str] = Field(default=None, description="sAMAccountName of the group manager")

    model_config = {"json_schema_extra": {
        "example": {
            "group_name": "grp-finance-users",
            "display_name": "Finance Department Users",
            "description": "Security group for all Finance department users",
            "scope": "Global",
            "category": "Security",
            "ou_path": "OU=Groups,DC=corp,DC=contoso,DC=com",
            "members": ["jdoe", "asmith"],
            "managed_by": "msmith"
        }
    }}


class GroupCreateResponse(BaseModel):
    group_name: str
    distinguished_name: str
    object_guid: str
    scope: GroupScope
    category: GroupCategory
    member_count: int
    message: str


class PasswordResetRequest(BaseModel):
    sam_account_name: str = Field(..., description="Target user's sAMAccountName")
    new_password: str = Field(..., description="New password; must meet domain complexity policy", min_length=12)
    must_change_at_logon: bool = Field(default=True, description="Force another change at next logon")
    unlock_account: bool = Field(default=True, description="Unlock account if currently locked during reset")

    @field_validator("new_password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        checks = [
            any(c.isupper() for c in v),
            any(c.islower() for c in v),
            any(c.isdigit() for c in v),
            any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in v),
        ]
        if sum(checks) < 3:
            raise ValueError("Password must contain at least 3 of: uppercase, lowercase, digit, special character")
        return v

    model_config = {"json_schema_extra": {
        "example": {
            "sam_account_name": "jdoe",
            "new_password": "NewP@ssw0rd!2024",
            "must_change_at_logon": True,
            "unlock_account": True
        }
    }}


class PasswordResetResponse(BaseModel):
    sam_account_name: str
    password_reset: bool
    account_unlocked: bool
    must_change_at_logon: bool
    message: str


class AccountUnlockRequest(BaseModel):
    sam_account_name: str = Field(..., description="sAMAccountName of the locked account")
    reason: Optional[str] = Field(default=None, description="Reason for unlock (audit log)", max_length=256)

    model_config = {"json_schema_extra": {
        "example": {
            "sam_account_name": "jdoe",
            "reason": "User called help desk - forgot password after vacation"
        }
    }}


class AccountUnlockResponse(BaseModel):
    sam_account_name: str
    previously_locked: bool
    unlocked: bool
    message: str


class AccountDisableRequest(BaseModel):
    sam_account_name: str = Field(..., description="sAMAccountName of the account to disable")
    reason: str = Field(..., description="Reason for disabling the account (audit log)", min_length=5, max_length=512)
    move_to_disabled_ou: bool = Field(default=True, description="Move the account to the Disabled Users OU")
    remove_group_memberships: bool = Field(default=False, description="Remove from all groups except Domain Users")

    model_config = {"json_schema_extra": {
        "example": {
            "sam_account_name": "jdoe",
            "reason": "Employee terminated on 2024-06-01 - HR ticket #12345",
            "move_to_disabled_ou": True,
            "remove_group_memberships": True
        }
    }}


class AccountDisableResponse(BaseModel):
    sam_account_name: str
    disabled: bool
    moved_to_disabled_ou: bool
    groups_removed: List[str] = Field(default_factory=list)
    message: str


class GroupMemberAddRequest(BaseModel):
    group_name: str = Field(..., description="Target group sAMAccountName")
    members: List[str] = Field(..., description="List of sAMAccountNames to add to the group", min_length=1)

    model_config = {"json_schema_extra": {
        "example": {
            "group_name": "grp-finance-users",
            "members": ["jdoe", "asmith", "bwilson"]
        }
    }}


class GroupMemberAddResponse(BaseModel):
    group_name: str
    members_added: List[str]
    members_failed: List[str]
    total_members: int
    message: str
