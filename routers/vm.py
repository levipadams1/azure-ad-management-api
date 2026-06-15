from fastapi import APIRouter
from models.vm import VMCreateRequest, VMCreateResponse, VMRestartRequest, VMRestartResponse
from services.vm_service import VMService

router = APIRouter(prefix="/vms", tags=["VM Management"])
_svc = VMService()


@router.post(
    "",
    response_model=VMCreateResponse,
    status_code=202,
    summary="Provision a new Virtual Machine",
    description=(
        "**SOP Step 1 — VM Provisioning**\n\n"
        "Creates a new Windows Server or Linux virtual machine in the specified Azure resource group. "
        "Corresponds to the SOP step: *'Log in to the Azure portal and create a new Windows Server VM '* — "
        "including specifying the VM size, OS image, VNet/subnet, admin credentials, and disk configuration. "
        "Returns a job ID to track async provisioning."
    ),
)
def create_vm(req: VMCreateRequest) -> VMCreateResponse:
    return _svc.create_vm(req)


@router.post(
    "/restart",
    response_model=VMRestartResponse,
    status_code=202,
    summary="Restart an existing VM",
    description=(
        "**SOP Step 2 — VM Restart**\n\n"
        "Initiates a graceful (or forced) restart of the specified VM. "
        "This maps to the SOP step: *'Restart the VM to complete feature installation'* — "
        "triggered after role installations (e.g. AD DS) that require a reboot before configuration continues."
    ),
)
def restart_vm(req: VMRestartRequest) -> VMRestartResponse:
    return _svc.restart_vm(req)
