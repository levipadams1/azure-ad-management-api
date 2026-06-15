from fastapi import APIRouter, Query
from models.ad_ds import (
    ADDSInstallRequest, ADDSInstallResponse,
    ADDSPromoteRequest, ADDSPromoteResponse,
    ADDSStructureResponse,
)
from services.ad_ds_service import ADDSService

router = APIRouter(prefix="/ad-ds", tags=["AD DS Role Management"])
_svc = ADDSService()


@router.post(
    "/install",
    response_model=ADDSInstallResponse,
    status_code=202,
    summary="Install AD DS and DNS roles on a VM",
    description=(
        "**SOP Step 3 — Install AD DS Role**\n\n"
        "Installs the *Active Directory Domain Services* and (optionally) *DNS Server* Windows Server roles "
        "on the target VM using Server Manager / PowerShell `Install-WindowsFeature`. "
        "Maps to SOP step: *'Open Server Manager → Manage → Add Roles and Features, select Active Directory Domain Services'*. "
        "Returns a job ID; the VM may reboot automatically if `restart_if_required` is True."
    ),
)
def install_adds(req: ADDSInstallRequest) -> ADDSInstallResponse:
    return _svc.install_adds_role(req)


@router.post(
    "/promote",
    response_model=ADDSPromoteResponse,
    status_code=202,
    summary="Promote VM to Domain Controller / create new forest",
    description=(
        "**SOP Step 4 — Promote to Domain Controller**\n\n"
        "Promotes the target VM to an Active Directory Domain Controller. "
        "Supports creating a **new forest** (default) or joining an existing domain. "
        "Maps to SOP step: *'Run the AD DS Configuration Wizard — Install-ADDSForest '* — "
        "specifying the domain FQDN, NetBIOS name, forest/domain functional level, DSRM password, "
        "and paths for NTDS database, logs, and SYSVOL. The VM will automatically reboot to finalise promotion."
    ),
)
def promote_to_dc(req: ADDSPromoteRequest) -> ADDSPromoteResponse:
    return _svc.promote_to_dc(req)


@router.get(
    "/structure",
    response_model=ADDSStructureResponse,
    summary="Verify AD DS structure (DCs, OUs, objects)",
    description=(
        "**SOP Step 5 — Verify AD DS Structure**\n\n"
        "Returns the current Active Directory structure including the OU hierarchy, domain controllers, "
        "functional levels, and object counts. "
        "Maps to SOP step: *'Open Active Directory Users and Computers and verify the OU structure, "
        "domain controllers, and user/group objects are visible'*."
    ),
)
def get_structure(
    domain_name: str = Query(..., description="Fully qualified domain name to inspect (e.g. corp.contoso.com)")
) -> ADDSStructureResponse:
    return _svc.get_structure(domain_name)
