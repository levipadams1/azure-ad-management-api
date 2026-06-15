from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import re


class VMSize(str, Enum):
    STANDARD_B1S = "Standard_B1s"
    STANDARD_B2S = "Standard_B2s"
    STANDARD_B4MS = "Standard_B4ms"
    STANDARD_D2S_V3 = "Standard_D2s_v3"
    STANDARD_D4S_V3 = "Standard_D4s_v3"
    STANDARD_D8S_V3 = "Standard_D8s_v3"


class VMOperatingSystem(str, Enum):
    WINDOWS_SERVER_2022 = "WindowsServer2022Datacenter"
    WINDOWS_SERVER_2019 = "WindowsServer2019Datacenter"
    WINDOWS_SERVER_2016 = "WindowsServer2016Datacenter"
    UBUNTU_20_04 = "UbuntuServer2004"
    UBUNTU_22_04 = "UbuntuServer2204"


class VMStatus(str, Enum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    DEALLOCATED = "deallocated"
    FAILED = "failed"
    RESTARTING = "restarting"
    PROVISIONING = "provisioning"


class NetworkConfig(BaseModel):
    virtual_network_name: str = Field(..., description="Name of the virtual network", min_length=1, max_length=64)
    subnet_name: str = Field(..., description="Name of the subnet", min_length=1, max_length=80)
    public_ip_enabled: bool = Field(default=False, description="Whether to assign a public IP address")
    nsg_name: Optional[str] = Field(default=None, description="Network Security Group name to attach")


class StorageConfig(BaseModel):
    os_disk_size_gb: int = Field(default=128, ge=30, le=4095, description="OS disk size in GB")
    os_disk_type: str = Field(default="Premium_LRS", description="OS disk storage type")
    data_disk_size_gb: Optional[int] = Field(default=None, ge=1, le=32767, description="Additional data disk size")


class VMCreateRequest(BaseModel):
    vm_name: str = Field(..., description="Unique VM name", min_length=1, max_length=15)
    resource_group: str = Field(..., description="Azure resource group name", min_length=1, max_length=90)
    location: str = Field(..., description="Azure region (e.g. eastus, westeurope)", min_length=1)
    vm_size: VMSize = Field(default=VMSize.STANDARD_B2S, description="VM SKU / size")
    os_image: VMOperatingSystem = Field(default=VMOperatingSystem.WINDOWS_SERVER_2022, description="Operating system image")
    admin_username: str = Field(..., description="Administrator account username", min_length=1, max_length=20)
    admin_password: str = Field(..., description="Administrator account password", min_length=12, max_length=123)
    network: NetworkConfig = Field(..., description="Network configuration")
    storage: StorageConfig = Field(default_factory=StorageConfig, description="Storage configuration")
    tags: Optional[dict] = Field(default=None, description="Azure resource tags")

    @field_validator("vm_name")
    @classmethod
    def validate_vm_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9\-]*$", v):
            raise ValueError("VM name must start with a letter and contain only alphanumeric characters or hyphens")
        return v

    @field_validator("admin_password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        checks = [
            any(c.isupper() for c in v),
            any(c.islower() for c in v),
            any(c.isdigit() for c in v),
            any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in v),
        ]
        if sum(checks) < 3:
            raise ValueError("Password must meet complexity requirements: at least 3 of uppercase, lowercase, digit, special char")
        return v

    model_config = {"json_schema_extra": {
        "example": {
            "vm_name": "DC01",
            "resource_group": "rg-ad-prod",
            "location": "eastus",
            "vm_size": "Standard_D2s_v3",
            "os_image": "WindowsServer2022Datacenter",
            "admin_username": "azureadmin",
            "admin_password": "P@ssw0rd!Secure123",
            "network": {
                "virtual_network_name": "vnet-ad-prod",
                "subnet_name": "snet-dc",
                "public_ip_enabled": False,
                "nsg_name": "nsg-dc-01"
            },
            "storage": {
                "os_disk_size_gb": 128,
                "os_disk_type": "Premium_LRS",
                "data_disk_size_gb": 50
            },
            "tags": {"environment": "production", "role": "domain-controller"}
        }
    }}


class VMCreateResponse(BaseModel):
    job_id: str = Field(..., description="Async job identifier for tracking provisioning")
    vm_name: str
    resource_group: str
    location: str
    status: VMStatus
    message: str
    estimated_completion_seconds: int = Field(..., description="Estimated seconds until VM is ready")


class VMRestartRequest(BaseModel):
    vm_name: str = Field(..., description="Name of the VM to restart", min_length=1, max_length=15)
    resource_group: str = Field(..., description="Azure resource group containing the VM", min_length=1, max_length=90)
    force_restart: bool = Field(default=False, description="If True, performs a hard power cycle instead of graceful restart")

    model_config = {"json_schema_extra": {
        "example": {
            "vm_name": "DC01",
            "resource_group": "rg-ad-prod",
            "force_restart": False
        }
    }}


class VMRestartResponse(BaseModel):
    job_id: str
    vm_name: str
    resource_group: str
    status: VMStatus
    message: str
    restart_type: str = Field(..., description="graceful or force")
