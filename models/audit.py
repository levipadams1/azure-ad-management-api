from typing import Optional, List
from pydantic import BaseModel, Field
from .identity import AccountStatus


class InactiveAccountsRequest(BaseModel):
    inactivity_threshold_days: int = Field(default=90, ge=1, le=3650, description="Number of days without logon to flag as inactive (SOP: 90)")
    search_base: Optional[str] = Field(default=None, description="OU Distinguished Name to scope the search; None = entire domain")
    include_never_logged_in: bool = Field(default=True, description="Include accounts that have never logged in")
    include_disabled: bool = Field(default=False, description="Include already-disabled accounts in results")
    include_computers: bool = Field(default=False, description="Include computer accounts in the search")
    page: int = Field(default=1, ge=1, description="Result page number")
    page_size: int = Field(default=50, ge=1, le=500, description="Results per page")

    model_config = {"json_schema_extra": {
        "example": {
            "inactivity_threshold_days": 90,
            "search_base": "OU=Users,DC=corp,DC=contoso,DC=com",
            "include_never_logged_in": True,
            "include_disabled": False,
            "include_computers": False,
            "page": 1,
            "page_size": 50
        }
    }}


class InactiveAccount(BaseModel):
    sam_account_name: str
    display_name: str
    distinguished_name: str
    email: Optional[str] = None
    department: Optional[str] = None
    last_logon_date: Optional[str] = Field(default=None, description="ISO 8601 date of last logon; None if never logged in")
    days_since_logon: Optional[int] = Field(default=None, description="Days since last logon; None if never logged in")
    account_status: AccountStatus
    password_last_set: Optional[str] = None
    account_expires: Optional[str] = None
    manager: Optional[str] = None
    recommended_action: str = Field(..., description="disable | review | delete")


class AuditSummary(BaseModel):
    total_accounts_scanned: int
    inactive_count: int
    never_logged_in_count: int
    already_disabled_count: int
    recommended_disable_count: int
    recommended_review_count: int


class InactiveAccountsResponse(BaseModel):
    threshold_days: int
    search_base: Optional[str]
    generated_at: str
    summary: AuditSummary
    accounts: List[InactiveAccount]
    page: int
    page_size: int
    total_pages: int
    has_next_page: bool
