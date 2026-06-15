from .vm import router as vm_router
from .ad_ds import router as ad_ds_router
from .identity import router as identity_router
from .gpo import router as gpo_router
from .audit import router as audit_router

__all__ = ["vm_router", "ad_ds_router", "identity_router", "gpo_router", "audit_router"]
