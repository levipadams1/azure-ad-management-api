from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import re


class ForestMode(str, Enum):
    WIN2016 = "WinThreshold"       # Windows Server 2016+
    WIN2012R2 = "Win2012R2"
    WIN2012 = "Win2012"
    WIN2008R2 = "Win2008R2"


class DomainMode(str, Enum):
    WIN2016 = "WinThreshold"
    WIN2012R2 = "Win2012R2"
    WIN2012 = "Win2012"
    WIN2008R2 = "Win2008R2"


class ADDSInstallRequest(BaseModel):
    vm_name: str = Field(..., description="Target VM name to install ADDS role on", min_length=1, max_length=15)
    resource_group: str = Field(..., description="Azure resource group of the target VM", min_length=1, max_length=90)
    include_management_tools: bool = Field(default=True, description="Install RSAT-ADDS management tools")
    include_dns_server: bool = Field(default=True, description="Install DNS Server role alongside ADDS")
    restart_if_required: bool = Field(default=True, description="Automatically restart VM if required after role install")

    model_config = {"json_schema_extra": {
        "example": {
            "vm_name": "DC01",
            "resource_group": "rg-ad-prod",
            "include_management_tools": True,
            "include_dns_server": True,
            "restart_if_required": True
        }
    }}


class ADDSInstallResponse(BaseModel):
    job_id: str
    vm_name: str
    status: str = Field(..., description="pending | running | succeeded | failed")
    roles_installed: List[str] = Field(default_factory=list)
    message: str
    restart_triggered: bool


class ADDSPromoteRequest(BaseModel):
    vm_name: str = Field(..., description="VM to promote to Domain Controller", min_length=1, max_length=15)
    resource_group: str = Field(..., description="Azure resource group", min_length=1, max_length=90)
    domain_name: str = Field(..., description="Fully qualified domain name (e.g. corp.contoso.com)")
    netbios_name: str = Field(..., description="NetBIOS domain name (≤15 chars, e.g. CORP)", max_length=15)
    forest_mode: ForestMode = Field(default=ForestMode.WIN2016, description="Active Directory forest functional level")
    domain_mode: DomainMode = Field(default=DomainMode.WIN2016, description="Active Directory domain functional level")
    dsrm_password: str = Field(..., description="Directory Services Restore Mode password", min_length=12)
    database_path: str = Field(default="C:\\Windows\\NTDS", description="Path for AD database files")
    log_path: str = Field(default="C:\\Windows\\NTDS", description="Path for AD log files")
    sysvol_path: str = Field(default="C:\\Windows\\SYSVOL", description="Path for SYSVOL")
    create_new_forest: bool = Field(default=True, description="True for new forest; False to join existing domain")
    dns_delegation: bool = Field(default=False, description="Create DNS delegation for the new domain")

    @field_validator("domain_name")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        if not re.match(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$", v):
            raise ValueError("domain_name must be a valid FQDN (e.g. corp.contoso.com)")
        return v.lower()

    @field_validator("netbios_name")
    @classmethod
    def validate_netbios(cls, v: str) -> str:
        if not re.match(r"^[A-Z0-9]{1,15}$", v.upper()):
            raise ValueError("NetBIOS name must be 1-15 alphanumeric characters")
        return v.upper()

    model_config = {"json_schema_extra": {
        "example": {
            "vm_name": "DC01",
            "resource_group": "rg-ad-prod",
            "domain_name": "corp.contoso.com",
            "netbios_name": "CORP",
            "forest_mode": "WinThreshold",
            "domain_mode": "WinThreshold",
            "dsrm_password": "Dsrm@P@ssw0rd!",
            "create_new_forest": True,
            "dns_delegation": False
        }
    }}


class ADDSPromoteResponse(BaseModel):
    job_id: str
    vm_name: str
    domain_name: str
    netbios_name: str
    status: str
    message: str
    restart_scheduled: bool


class OUNode(BaseModel):
    name: str
    distinguished_name: str
    children: List["OUNode"] = Field(default_factory=list)
    object_count: int = Field(default=0, description="Number of objects directly in this OU")


OUNode.model_rebuild()


class ADDSStructureResponse(BaseModel):
    domain_name: str
    forest_name: str
    domain_controllers: List[str]
    functional_levels: dict
    ou_tree: List[OUNode]
    site_count: int
    total_users: int
    total_groups: int
    total_computers: int
    queried_at: str
