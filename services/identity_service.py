import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException, status
from models.identity import (
    UserCreateRequest, UserCreateResponse,
    GroupCreateRequest, GroupCreateResponse,
    PasswordResetRequest, PasswordResetResponse,
    AccountUnlockRequest, AccountUnlockResponse,
    AccountDisableRequest, AccountDisableResponse,
    GroupMemberAddRequest, GroupMemberAddResponse,
    AccountStatus,
)
from . import store


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_dn(sam: str, ou_path: str, object_type: str = "CN") -> str:
    return f"{object_type}={sam},{ou_path}"


class IdentityService:
    # ── SOP Step 6a ── Create User Account ────────────────────────────────────
    def create_user(self, req: UserCreateRequest) -> UserCreateResponse:
        sam = req.sam_account_name.lower()
        if sam in store.users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User '{sam}' already exists.",
            )

        display = req.display_name or f"{req.given_name} {req.surname}"
        dn = _build_dn(display, req.ou_path)
        guid = str(uuid.uuid4())

        groups_added: List[str] = []
        groups_failed: List[str] = []

        user_record = {
            "sam_account_name": sam,
            "given_name": req.given_name,
            "surname": req.surname,
            "display_name": display,
            "email": req.email,
            "department": req.department,
            "title": req.title,
            "manager_sam": req.manager_sam,
            "ou_path": req.ou_path,
            "distinguished_name": dn,
            "object_guid": guid,
            "status": AccountStatus.ACTIVE if req.account_enabled else AccountStatus.DISABLED,
            "must_change_password": req.must_change_password,
            "password_last_set": _now_iso(),
            "last_logon_date": None,
            "created_at": _now_iso(),
            "groups": ["Domain Users"],
            "locked": False,
        }
        store.users[sam] = user_record

        # Add to requested groups
        for grp in (req.groups or []):
            grp_key = grp.lower()
            if grp_key in store.groups:
                store.groups[grp_key]["members"].append(sam)
                store.users[sam]["groups"].append(grp_key)
                groups_added.append(grp)
            else:
                groups_failed.append(grp)

        return UserCreateResponse(
            sam_account_name=sam,
            distinguished_name=dn,
            object_guid=guid,
            status=user_record["status"],
            message=f"User '{sam}' ({display}) created successfully in '{req.ou_path}'.",
            groups_added=groups_added,
            groups_failed=groups_failed,
        )

    # ── SOP Step 6b ── Create Security / Distribution Group ───────────────────
    def create_group(self, req: GroupCreateRequest) -> GroupCreateResponse:
        grp_key = req.group_name.lower()
        if grp_key in store.groups:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Group '{grp_key}' already exists.",
            )

        display = req.display_name or req.group_name
        dn = _build_dn(req.group_name, req.ou_path)
        guid = str(uuid.uuid4())
        initial_members = [m.lower() for m in (req.members or [])]

        store.groups[grp_key] = {
            "group_name": req.group_name,
            "display_name": display,
            "description": req.description,
            "scope": req.scope,
            "category": req.category,
            "ou_path": req.ou_path,
            "distinguished_name": dn,
            "object_guid": guid,
            "members": initial_members,
            "managed_by": req.managed_by,
            "created_at": _now_iso(),
        }

        # Back-link users
        for member_sam in initial_members:
            if member_sam in store.users:
                if grp_key not in store.users[member_sam].get("groups", []):
                    store.users[member_sam]["groups"].append(grp_key)

        return GroupCreateResponse(
            group_name=req.group_name,
            distinguished_name=dn,
            object_guid=guid,
            scope=req.scope,
            category=req.category,
            member_count=len(initial_members),
            message=f"Group '{req.group_name}' ({req.scope.value} {req.category.value}) created in '{req.ou_path}'.",
        )

    # ── SOP Step 7 ── Add Members to Group ────────────────────────────────────
    def add_group_members(self, req: GroupMemberAddRequest) -> GroupMemberAddResponse:
        grp_key = req.group_name.lower()
        if grp_key not in store.groups:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group '{grp_key}' not found.",
            )

        added: List[str] = []
        failed: List[str] = []
        for sam in req.members:
            sam_lower = sam.lower()
            if sam_lower not in store.users:
                failed.append(sam)
            elif sam_lower in store.groups[grp_key]["members"]:
                added.append(sam)  # already a member — idempotent
            else:
                store.groups[grp_key]["members"].append(sam_lower)
                store.users[sam_lower]["groups"].append(grp_key)
                added.append(sam)

        return GroupMemberAddResponse(
            group_name=req.group_name,
            members_added=added,
            members_failed=failed,
            total_members=len(store.groups[grp_key]["members"]),
            message=f"Added {len(added)} member(s) to '{req.group_name}'. Failed: {len(failed)}.",
        )

    # ── SOP Step 8 ── Reset User Password ─────────────────────────────────────
    def reset_password(self, req: PasswordResetRequest) -> PasswordResetResponse:
        sam = req.sam_account_name.lower()
        if sam not in store.users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{sam}' not found.",
            )

        user = store.users[sam]
        was_locked = user.get("locked", False)
        user["password_last_set"] = _now_iso()
        user["must_change_password"] = req.must_change_at_logon
        if req.unlock_account and was_locked:
            user["locked"] = False
            user["status"] = AccountStatus.ACTIVE

        return PasswordResetResponse(
            sam_account_name=sam,
            password_reset=True,
            account_unlocked=was_locked and req.unlock_account,
            must_change_at_logon=req.must_change_at_logon,
            message=f"Password reset for '{sam}'. {'Account unlocked. ' if was_locked and req.unlock_account else ''}Must change at logon: {req.must_change_at_logon}.",
        )

    # ── SOP Step 9 ── Unlock Locked Account ───────────────────────────────────
    def unlock_account(self, req: AccountUnlockRequest) -> AccountUnlockResponse:
        sam = req.sam_account_name.lower()
        if sam not in store.users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{sam}' not found.",
            )

        user = store.users[sam]
        was_locked = user.get("locked", False)
        user["locked"] = False
        if user["status"] == AccountStatus.LOCKED:
            user["status"] = AccountStatus.ACTIVE

        return AccountUnlockResponse(
            sam_account_name=sam,
            previously_locked=was_locked,
            unlocked=True,
            message=(
                f"Account '{sam}' unlocked successfully."
                if was_locked
                else f"Account '{sam}' was not locked — no action taken."
            ),
        )

    # ── SOP Step 10 ── Disable / Off-board Account ────────────────────────────
    def disable_account(self, req: AccountDisableRequest) -> AccountDisableResponse:
        sam = req.sam_account_name.lower()
        if sam not in store.users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{sam}' not found.",
            )

        user = store.users[sam]
        user["status"] = AccountStatus.DISABLED
        user["disabled_at"] = _now_iso()
        user["disable_reason"] = req.reason

        moved = False
        if req.move_to_disabled_ou:
            parts = user["distinguished_name"].split(",", 1)
            if len(parts) == 2:
                user["distinguished_name"] = f"{parts[0]},OU=Disabled,{parts[1]}"
            moved = True

        removed_groups: List[str] = []
        if req.remove_group_memberships:
            for grp in list(user.get("groups", [])):
                if grp != "domain users":
                    if grp in store.groups:
                        store.groups[grp]["members"] = [
                            m for m in store.groups[grp]["members"] if m != sam
                        ]
                    removed_groups.append(grp)
            user["groups"] = ["domain users"]

        return AccountDisableResponse(
            sam_account_name=sam,
            disabled=True,
            moved_to_disabled_ou=moved,
            groups_removed=removed_groups,
            message=f"Account '{sam}' disabled. Reason: {req.reason}.",
        )
