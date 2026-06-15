from fastapi import APIRouter
from models.audit import InactiveAccountsRequest, InactiveAccountsResponse
from services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])
_svc = AuditService()


@router.post(
    "/inactive-accounts",
    response_model=InactiveAccountsResponse,
    status_code=200,
    summary="Audit inactive user accounts",
    description=(
        "**SOP Step 15 — Inactive Account Audit**\n\n"
        "Scans Active Directory for user accounts that have not logged in within the specified threshold "
        "(SOP default: **90 days**). Also surfaces accounts that have **never logged in**. "
        "Maps to SOP step: *'Run a quarterly review using Search-ADAccount -AccountInactive -TimeSpan 90.00:00:00 '* "
        "to identify stale accounts — then disable, review, or delete based on the recommended action returned. "
        "Supports OU-scoped searches and pagination for large directories."
    ),
)
def get_inactive_accounts(req: InactiveAccountsRequest) -> InactiveAccountsResponse:
    return _svc.get_inactive_accounts(req)
