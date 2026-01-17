"""
Compliance API Routes

Endpoints for managing compliance policies and checking transactions.
"""

from fastapi import APIRouter, HTTPException
from typing import Any

from app.models.schemas import (
    ComplianceCheckRequest,
    ComplianceResultResponse,
    PolicyViolationResponse,
    PolicyCreateRequest,
    PolicyResponse,
    SeverityEnum
)
from app.ai.policy_engine import (
    get_policy_engine,
    CompliancePolicy,
    PolicyType,
    PolicySeverity
)


router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get("/policies", response_model=list[PolicyResponse])
async def list_policies():
    """List all configured compliance policies."""
    engine = get_policy_engine()
    policies = engine.list_policies()
    
    return [
        PolicyResponse(
            name=p.name,
            policy_type=p.policy_type.value,
            severity=SeverityEnum(p.severity.value),
            description=p.description,
            enabled=p.enabled,
            config=p.config
        )
        for p in policies
    ]


@router.get("/policies/{name}", response_model=PolicyResponse)
async def get_policy(name: str):
    """Get a specific policy by name."""
    engine = get_policy_engine()
    policy = engine.get_policy(name)
    
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy '{name}' not found")
    
    return PolicyResponse(
        name=policy.name,
        policy_type=policy.policy_type.value,
        severity=SeverityEnum(policy.severity.value),
        description=policy.description,
        enabled=policy.enabled,
        config=policy.config
    )


@router.post("/policies", response_model=PolicyResponse)
async def create_policy(request: PolicyCreateRequest):
    """Create a new compliance policy."""
    engine = get_policy_engine()
    
    try:
        policy_type = PolicyType(request.policy_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy type. Valid types: {[t.value for t in PolicyType]}"
        )
    
    policy = CompliancePolicy(
        name=request.name,
        policy_type=policy_type,
        severity=PolicySeverity(request.severity.value),
        description=request.description,
        enabled=request.enabled,
        config=request.config
    )
    
    engine.add_policy(policy)
    
    return PolicyResponse(
        name=policy.name,
        policy_type=policy.policy_type.value,
        severity=SeverityEnum(policy.severity.value),
        description=policy.description,
        enabled=policy.enabled,
        config=policy.config
    )


@router.delete("/policies/{name}")
async def delete_policy(name: str):
    """Delete a compliance policy."""
    engine = get_policy_engine()
    
    if not engine.get_policy(name):
        raise HTTPException(status_code=404, detail=f"Policy '{name}' not found")
    
    engine.remove_policy(name)
    return {"status": "deleted", "name": name}


@router.put("/policies/{name}/toggle")
async def toggle_policy(name: str):
    """Enable or disable a policy."""
    engine = get_policy_engine()
    policy = engine.get_policy(name)
    
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy '{name}' not found")
    
    policy.enabled = not policy.enabled
    engine.add_policy(policy)  # Re-add to update
    
    return {
        "name": name,
        "enabled": policy.enabled
    }


@router.post("/check", response_model=ComplianceResultResponse)
async def check_compliance(request: ComplianceCheckRequest):
    """Check a transaction against all active compliance policies."""
    engine = get_policy_engine()
    
    result = engine.check_transaction(
        sender=request.sender,
        receiver=request.receiver,
        value=request.value,
        gas_used=request.gas_used,
        payload=request.payload
    )
    
    return ComplianceResultResponse(
        passed=result.passed,
        violations=[
            PolicyViolationResponse(
                policy_name=v.policy_name,
                policy_type=v.policy_type.value,
                severity=SeverityEnum(v.severity.value),
                message=v.message,
                details=v.details
            )
            for v in result.violations
        ],
        policies_checked=result.policies_checked
    )


@router.post("/blocked-addresses")
async def add_blocked_address(address: str):
    """Add an address to the blocked list."""
    engine = get_policy_engine()
    engine.add_blocked_address(address)
    
    return {
        "status": "added",
        "address": address
    }


@router.delete("/blocked-addresses/{address}")
async def remove_blocked_address(address: str):
    """Remove an address from the blocked list."""
    engine = get_policy_engine()
    engine.remove_blocked_address(address)
    
    return {
        "status": "removed",
        "address": address
    }


@router.get("/stats")
async def get_policy_stats() -> dict[str, Any]:
    """Get statistics about configured policies."""
    engine = get_policy_engine()
    return engine.get_policy_stats()
