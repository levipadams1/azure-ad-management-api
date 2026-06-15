import uuid
from datetime import datetime, timezone
from typing import Optional
from models.vm import (
    VMCreateRequest, VMCreateResponse,
    VMRestartRequest, VMRestartResponse,
    VMStatus,
)
from . import store


def _vm_key(resource_group: str, vm_name: str) -> str:
    return f"{resource_group.lower()}/{vm_name.lower()}"


class VMService:
    # ── SOP Step 1 ── Provision a new Virtual Machine ─────────────────────────
    def create_vm(self, req: VMCreateRequest) -> VMCreateResponse:
        job_id = str(uuid.uuid4())
        key = _vm_key(req.resource_group, req.vm_name)

        vm_record = {
            "vm_name": req.vm_name,
            "resource_group": req.resource_group,
            "location": req.location,
            "vm_size": req.vm_size,
            "os_image": req.os_image,
            "admin_username": req.admin_username,
            "network": req.network.model_dump(),
            "storage": req.storage.model_dump(),
            "tags": req.tags or {},
            "status": VMStatus.PROVISIONING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "job_id": job_id,
        }
        store.vms[key] = vm_record
        store.jobs[job_id] = {
            "job_id": job_id,
            "type": "vm_create",
            "resource": key,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        return VMCreateResponse(
            job_id=job_id,
            vm_name=req.vm_name,
            resource_group=req.resource_group,
            location=req.location,
            status=VMStatus.PROVISIONING,
            message=(
                f"VM '{req.vm_name}' provisioning started in resource group "
                f"'{req.resource_group}' ({req.location}). "
                f"OS: {req.os_image.value}, Size: {req.vm_size.value}."
            ),
            estimated_completion_seconds=300,
        )

    # ── SOP Step 2 ── Restart VM (e.g. after role installation) ───────────────
    def restart_vm(self, req: VMRestartRequest) -> VMRestartResponse:
        job_id = str(uuid.uuid4())
        key = _vm_key(req.resource_group, req.vm_name)

        if key not in store.vms:
            # Simulate: if VM not tracked locally, still accept gracefully
            store.vms[key] = {
                "vm_name": req.vm_name,
                "resource_group": req.resource_group,
                "status": VMStatus.RUNNING,
            }

        store.vms[key]["status"] = VMStatus.RESTARTING
        store.jobs[job_id] = {
            "job_id": job_id,
            "type": "vm_restart",
            "resource": key,
            "force": req.force_restart,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        restart_type = "force" if req.force_restart else "graceful"
        return VMRestartResponse(
            job_id=job_id,
            vm_name=req.vm_name,
            resource_group=req.resource_group,
            status=VMStatus.RESTARTING,
            message=(
                f"VM '{req.vm_name}' is performing a {restart_type} restart. "
                "The VM will be unavailable briefly during restart."
            ),
            restart_type=restart_type,
        )
