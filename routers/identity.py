from fastapi import APIRouter
from models.identity import (
    UserCreateRequest, UserCreateResponse,
    GroupCreateRequest, GroupCreateResponse,
    PasswordResetRequest, PasswordResetResponse,
    AccountUnlockRequest, AccountUnlockResponse,
    AccountDisableRequest, AccountDisableResponse,
    GroupMemberAddRequest, GroupMemberAddResponse,
)
from services.identity_service import IdentityService

router = APIRouter(prefix="/identity", tags=["Identity Management"])
_svc = IdentityService()


@router.post(
    "/users",
    response_model=UserCreateResponse,
    status_code=201,
    summary="Create a new AD user account",
    description=(
        "**SOP Step 6a — Create User Account**\n\n"
        "Creates a new Active Directory user account in the specified OU. "
        "Maps to SOP step: *'In ADUC, right-click the target OU → New → User — fill in First Name, "
        "Last Name, User Logon Name, set initial password and check 'User must change password at next logon''*. "
        "Optionally adds the user to specified security groups immediately."
    ),
)
def create_user(req: UserCreateRequest) -> UserCreateResponse:
    return _svc.create_user(req)


@router.post(
    "/groups",
    response_model=GroupCreateResponse,
    status_code=201,
    summary="Create a new AD security or distribution group",
    description=(
        "**SOP Step 6b — Create Group**\n\n"
        "Creates a new Active Directory group (Security or Distribution) with the specified scope. "
        "Maps to SOP step: *'In ADUC, right-click the Groups OU → New → Group — enter Group Name, "
        "select Group Scope (Global/Universal/Domain Local) and Group Type (Security/Distribution)'*."
    ),
)
def create_group(req: GroupCreateRequest) -> GroupCreateResponse:
    return _svc.create_group(req)


@router.post(
    "/groups/members",
    response_model=GroupMemberAddResponse,
    status_code=200,
    summary="Add members to an existing AD group",
    description=(
        "**SOP Step 7 — Add Group Members**\n\n"
        "Adds one or more user accounts to an existing AD group. "
        "Maps to SOP step: *'Open the group Properties → Members tab → Add — type in user accounts'*. "
        "Idempotent: adding an already-member user does not raise an error."
    ),
)
def add_group_members(req: GroupMemberAddRequest) -> GroupMemberAddResponse:
    return _svc.add_group_members(req)


@router.post(
    "/users/reset-password",
    response_model=PasswordResetResponse,
    status_code=200,
    summary="Reset a user's Active Directory password",
    description=(
        "**SOP Step 8 — Password Reset**\n\n"
        "Resets the password for the specified user account. "
        "Maps to SOP step: *'In ADUC, right-click the user → Reset Password — enter new password, "
        "confirm, and optionally check 'Unlock the user's account' and 'User must change password at next logon''*."
    ),
)
def reset_password(req: PasswordResetRequest) -> PasswordResetResponse:
    return _svc.reset_password(req)


@router.post(
    "/users/unlock",
    response_model=AccountUnlockResponse,
    status_code=200,
    summary="Unlock a locked-out AD account",
    description=(
        "**SOP Step 9 — Unlock Account**\n\n"
        "Unlocks an Active Directory account that has been locked due to failed logon attempts. "
        "Maps to SOP step: *'In ADUC, locate the user, open Properties → Account tab → "
        "uncheck 'Unlock account' checkbox (or use Unlock-ADAccount in PowerShell)'*."
    ),
)
def unlock_account(req: AccountUnlockRequest) -> AccountUnlockResponse:
    return _svc.unlock_account(req)


@router.post(
    "/users/disable",
    response_model=AccountDisableResponse,
    status_code=200,
    summary="Disable / off-board a user account",
    description=(
        "**SOP Step 10 — Disable / Off-board Account**\n\n"
        "Disables the specified user account and optionally moves it to the Disabled OU and strips group memberships. "
        "Maps to SOP step: *'In ADUC, right-click the user → Disable Account; then move to the Disabled Users OU "
        "and remove from all security groups per the off-boarding checklist'*."
    ),
)
def disable_account(req: AccountDisableRequest) -> AccountDisableResponse:
    return _svc.disable_account(req)
