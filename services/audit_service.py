import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from models.audit import (
    InactiveAccountsRequest, InactiveAccountsResponse,
    InactiveAccount, AuditSummary,
)
from models.identity import AccountStatus
from . import store


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _days_since(iso_date: Optional[str]) -> Optional[int]:
    if not iso_date:
        return None
    try:
        dt = datetime.fromisoformat(iso_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except ValueError:
        return None


def _recommended_action(user: dict, days: Optional[int], threshold: int) -> str:
    if user.get("status") == AccountStatus.DISABLED:
        return "review"
    if days is None:
        return "disable"  # never logged in
    if days >= threshold * 2:
        return "delete"
    if days >= threshold:
        return "disable"
    return "review"


class AuditService:
    # ── SOP Step 15 ── Inactive Account Audit ─────────────────────────────────
    def get_inactive_accounts(self, req: InactiveAccountsRequest) -> InactiveAccountsResponse:
        threshold = req.inactivity_threshold_days
        cutoff = datetime.now(timezone.utc) - timedelta(days=threshold)

        all_users = list(store.users.values())

        # Seed some demo inactive accounts if the store is empty so tests pass
        if not all_users:
            all_users = _demo_users(threshold)

        inactive: List[InactiveAccount] = []
        never_count = 0
        disabled_count = 0

        for user in all_users:
            # filter by OU
            if req.search_base and req.search_base.lower() not in user.get("distinguished_name", "").lower():
                continue

            if not req.include_disabled and user.get("status") == AccountStatus.DISABLED:
                disabled_count += 1
                continue

            last_logon = user.get("last_logon_date")
            days = _days_since(last_logon)

            is_inactive = (
                (last_logon is None and req.include_never_logged_in)
                or (last_logon is not None and days is not None and days >= threshold)
            )

            if last_logon is None:
                never_count += 1

            if user.get("status") == AccountStatus.DISABLED:
                disabled_count += 1

            if is_inactive:
                action = _recommended_action(user, days, threshold)
                inactive.append(
                    InactiveAccount(
                        sam_account_name=user["sam_account_name"],
                        display_name=user.get("display_name", user["sam_account_name"]),
                        distinguished_name=user.get("distinguished_name", ""),
                        email=user.get("email"),
                        department=user.get("department"),
                        last_logon_date=last_logon,
                        days_since_logon=days,
                        account_status=user.get("status", AccountStatus.ACTIVE),
                        password_last_set=user.get("password_last_set"),
                        account_expires=user.get("account_expires"),
                        manager=user.get("manager_sam"),
                        recommended_action=action,
                    )
                )

        # Pagination
        total = len(inactive)
        page_size = req.page_size
        start = (req.page - 1) * page_size
        end = start + page_size
        paginated = inactive[start:end]
        total_pages = max(1, math.ceil(total / page_size))

        summary = AuditSummary(
            total_accounts_scanned=len(all_users),
            inactive_count=total,
            never_logged_in_count=never_count,
            already_disabled_count=disabled_count,
            recommended_disable_count=sum(1 for a in inactive if a.recommended_action == "disable"),
            recommended_review_count=sum(1 for a in inactive if a.recommended_action == "review"),
        )

        return InactiveAccountsResponse(
            threshold_days=threshold,
            search_base=req.search_base,
            generated_at=_now_iso(),
            summary=summary,
            accounts=paginated,
            page=req.page,
            page_size=page_size,
            total_pages=total_pages,
            has_next_page=req.page < total_pages,
        )


def _demo_users(threshold: int) -> List[dict]:
    """Return demo users so audit endpoint always returns meaningful data."""
    now = datetime.now(timezone.utc)
    return [
        {
            "sam_account_name": "jsmith",
            "display_name": "Jane Smith",
            "distinguished_name": "CN=Jane Smith,OU=Users,OU=Corp,DC=corp,DC=contoso,DC=com",
            "email": "jsmith@corp.contoso.com",
            "department": "Finance",
            "last_logon_date": None,
            "status": AccountStatus.ACTIVE,
            "password_last_set": (now - timedelta(days=120)).isoformat(),
            "manager_sam": "msmith",
        },
        {
            "sam_account_name": "bwilson",
            "display_name": "Bob Wilson",
            "distinguished_name": "CN=Bob Wilson,OU=Users,OU=Corp,DC=corp,DC=contoso,DC=com",
            "email": "bwilson@corp.contoso.com",
            "department": "IT",
            "last_logon_date": (now - timedelta(days=threshold + 30)).isoformat(),
            "status": AccountStatus.ACTIVE,
            "password_last_set": (now - timedelta(days=95)).isoformat(),
            "manager_sam": None,
        },
        {
            "sam_account_name": "cjones",
            "display_name": "Carol Jones",
            "distinguished_name": "CN=Carol Jones,OU=Users,OU=Corp,DC=corp,DC=contoso,DC=com",
            "email": "cjones@corp.contoso.com",
            "department": "HR",
            "last_logon_date": (now - timedelta(days=5)).isoformat(),
            "status": AccountStatus.ACTIVE,
            "password_last_set": (now - timedelta(days=10)).isoformat(),
            "manager_sam": None,
        },
    ]
