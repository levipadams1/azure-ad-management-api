"""
Shared in-memory store — simulates a persistence layer for the prototype.
All data is keyed in plain dicts so routers/services can share state across requests.
"""
from typing import Dict, Any, List
import threading

_lock = threading.Lock()

# ── VM store ──────────────────────────────────────────────────────────────────
vms: Dict[str, Any] = {}          # key: "{resource_group}/{vm_name}"
jobs: Dict[str, Any] = {}         # key: job_id

# ── ADDS store ────────────────────────────────────────────────────────────────
domains: Dict[str, Any] = {}      # key: domain_name
adds_jobs: Dict[str, Any] = {}

# ── Identity store ────────────────────────────────────────────────────────────
users: Dict[str, Any] = {}        # key: sam_account_name
groups: Dict[str, Any] = {}       # key: group_name

# ── GPO store ─────────────────────────────────────────────────────────────────
gpos: Dict[str, Any] = {}         # key: gpo_name

def reset_all() -> None:
    """Clear all in-memory state (used in tests)."""
    with _lock:
        vms.clear()
        jobs.clear()
        domains.clear()
        adds_jobs.clear()
        users.clear()
        groups.clear()
        gpos.clear()
