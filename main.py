"""
Azure AD / Windows Server Management API
==========================================
A FastAPI-based management API that automates common Active Directory Domain Services (AD DS),
Virtual Machine, Identity, Group Policy, and Security Audit operations described in the
Windows Server / Azure AD Standard Operating Procedure (SOP).

SOP Step Mapping
----------------
Step 1  → POST /vms                               VM Provisioning
Step 2  → POST /vms/restart                       VM Restart
Step 3  → POST /ad-ds/install                     Install AD DS & DNS Roles
Step 4  → POST /ad-ds/promote                     Promote to Domain Controller
Step 5  → GET  /ad-ds/structure                   Verify AD DS Structure
Step 6a → POST /identity/users                    Create User Account
Step 6b → POST /identity/groups                   Create Security/Distribution Group
Step 7  → POST /identity/groups/members           Add Group Members
Step 8  → POST /identity/users/reset-password     Reset Password
Step 9  → POST /identity/users/unlock             Unlock Account
Step 10 → POST /identity/users/disable            Disable / Off-board Account
Step 11 → POST /gpo/password-policy              Password Policy GPO
Step 12 → POST /gpo/inactivity-lock              Inactivity Lock GPO
Step 13 → POST /gpo/storage-restrictions         Storage Restriction GPO
Step 14 → POST /gpo/apply                        Force GPO Refresh
Step 15 → POST /audit/inactive-accounts          Inactive Account Audit
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from routers import vm_router, ad_ds_router, identity_router, gpo_router, audit_router

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Azure AD / Windows Server Management API",
    description=__doc__,
    version="1.0.0",
    contact={
        "name": "Infrastructure Team",
        "email": "infra-team@corp.contoso.com",
    },
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "VM Management",        "description": "SOP Steps 1–2: Provision and manage Azure VMs"},
        {"name": "AD DS Role Management","description": "SOP Steps 3–5: Install roles, promote DCs, verify structure"},
        {"name": "Identity Management",  "description": "SOP Steps 6–10: Users, groups, passwords, accounts"},
        {"name": "GPO Configuration",    "description": "SOP Steps 11–14: Password policy, lock, storage, refresh"},
        {"name": "Audit",                "description": "SOP Step 15: Inactive account auditing"},
    ],
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(vm_router)
app.include_router(ad_ds_router)
app.include_router(identity_router)
app.include_router(gpo_router)
app.include_router(audit_router)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# ── Health / Root ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"], summary="API health check")
def root():
    return {
        "service": "Azure AD / Windows Server Management API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"], summary="Liveness probe")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
