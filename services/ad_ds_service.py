import uuid
from datetime import datetime, timezone
from models.ad_ds import (
    ADDSInstallRequest, ADDSInstallResponse,
    ADDSPromoteRequest, ADDSPromoteResponse,
    ADDSStructureResponse, OUNode,
)
from . import store


class ADDSService:
    # ── SOP Step 3 ── Install AD DS & DNS Roles ────────────────────────────────
    def install_adds_role(self, req: ADDSInstallRequest) -> ADDSInstallResponse:
        job_id = str(uuid.uuid4())
        roles = ["AD-Domain-Services"]
        if req.include_dns_server:
            roles.append("DNS")
        if req.include_management_tools:
            roles.extend(["RSAT-ADDS", "RSAT-ADDS-Tools", "RSAT-DNS-Server"])

        store.adds_jobs[job_id] = {
            "job_id": job_id,
            "type": "adds_install",
            "vm_name": req.vm_name,
            "roles": roles,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        return ADDSInstallResponse(
            job_id=job_id,
            vm_name=req.vm_name,
            status="running",
            roles_installed=roles,
            message=(
                f"Installing roles {roles} on VM '{req.vm_name}'. "
                f"Restart {'will be triggered' if req.restart_if_required else 'must be done manually'} if required."
            ),
            restart_triggered=req.restart_if_required,
        )

    # ── SOP Step 4 ── Promote DC / Create New Forest ───────────────────────────
    def promote_to_dc(self, req: ADDSPromoteRequest) -> ADDSPromoteResponse:
        job_id = str(uuid.uuid4())
        domain_key = req.domain_name.lower()

        domain_record = {
            "domain_name": req.domain_name,
            "netbios_name": req.netbios_name,
            "forest_mode": req.forest_mode,
            "domain_mode": req.domain_mode,
            "domain_controllers": [req.vm_name],
            "database_path": req.database_path,
            "log_path": req.log_path,
            "sysvol_path": req.sysvol_path,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "functional_levels": {
                "forest": req.forest_mode.value,
                "domain": req.domain_mode.value,
            },
            "ou_tree": _default_ou_tree(req.domain_name),
        }
        store.domains[domain_key] = domain_record
        store.adds_jobs[job_id] = {
            "job_id": job_id,
            "type": "adds_promote",
            "vm_name": req.vm_name,
            "domain_name": req.domain_name,
            "status": "running",
        }

        return ADDSPromoteResponse(
            job_id=job_id,
            vm_name=req.vm_name,
            domain_name=req.domain_name,
            netbios_name=req.netbios_name,
            status="running",
            message=(
                f"Promoting '{req.vm_name}' to Domain Controller for "
                f"{'new forest' if req.create_new_forest else 'existing domain'} "
                f"'{req.domain_name}'. Forest/Domain mode: {req.forest_mode.value}."
            ),
            restart_scheduled=True,
        )

    # ── SOP Step 5 ── Verify AD DS Structure ──────────────────────────────────
    def get_structure(self, domain_name: str) -> ADDSStructureResponse:
        domain_key = domain_name.lower()

        if domain_key in store.domains:
            record = store.domains[domain_key]
            ou_tree = record.get("ou_tree", _default_ou_tree(domain_name))
            dc_list = record.get("domain_controllers", ["DC01"])
            functional = record.get("functional_levels", {"forest": "WinThreshold", "domain": "WinThreshold"})
        else:
            # Return a simulated structure for any domain queried
            ou_tree = _default_ou_tree(domain_name)
            dc_list = ["DC01"]
            functional = {"forest": "WinThreshold", "domain": "WinThreshold"}

        return ADDSStructureResponse(
            domain_name=domain_name,
            forest_name=domain_name,
            domain_controllers=dc_list,
            functional_levels=functional,
            ou_tree=ou_tree,
            site_count=1,
            total_users=len([u for u in store.users.values()]),
            total_groups=len(store.groups),
            total_computers=len(dc_list),
            queried_at=datetime.now(timezone.utc).isoformat(),
        )


def _dn_from_fqdn(fqdn: str) -> str:
    return ",".join(f"DC={part}" for part in fqdn.split("."))


def _default_ou_tree(domain_name: str) -> list:
    base_dn = _dn_from_fqdn(domain_name)
    return [
        OUNode(
            name="Corp",
            distinguished_name=f"OU=Corp,{base_dn}",
            object_count=0,
            children=[
                OUNode(name="Users",      distinguished_name=f"OU=Users,OU=Corp,{base_dn}",      object_count=0),
                OUNode(name="Groups",     distinguished_name=f"OU=Groups,OU=Corp,{base_dn}",     object_count=0),
                OUNode(name="Computers",  distinguished_name=f"OU=Computers,OU=Corp,{base_dn}",  object_count=0),
                OUNode(name="Servers",    distinguished_name=f"OU=Servers,OU=Corp,{base_dn}",    object_count=0),
                OUNode(name="Service Accounts", distinguished_name=f"OU=Service Accounts,OU=Corp,{base_dn}", object_count=0),
                OUNode(name="Disabled",   distinguished_name=f"OU=Disabled,OU=Corp,{base_dn}",   object_count=0),
            ],
        )
    ]
