"""
Workflow API Routes - On-Demand.io Workflow Integration

Provides endpoints for activating On-Demand.io workflows built in their platform.
Workflows are pre-configured in the platform and simply activated via HTTP POST.

Available workflow:
1. Solana Trading Bot (ID: 696abab2c28c63108ddb7dbe) - Automated token analysis & swapping
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.ondemand_workflows import workflow_manager

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


class WorkflowActivateRequest(BaseModel):
    """Request model for activating a workflow."""
    workflow_id: str


@router.get("/")
async def list_workflows():
    """
    List all available On-Demand.io workflows.
    
    Returns workflows built in the On-Demand.io platform that can be
    triggered via HTTP, webhooks, cron jobs, or email.
    """
    workflows = workflow_manager.get_all_workflows()
    return {
        "success": True,
        "workflows": workflows,
        "total": len(workflows),
        "info": "These workflows are built in On-Demand.io platform and triggered via HTTP"
    }


@router.get("/{workflow_key}")
async def get_workflow(workflow_key: str):
    """Get details of a specific workflow."""
    workflow = workflow_manager.get_workflow(workflow_key)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_key}' not found")
    return {
        "success": True,
        "workflow": workflow
    }


@router.post("/activate")
async def activate_workflow(request: WorkflowActivateRequest):
    """
    Activate an On-Demand.io workflow.
    
    Activation prepares the workflow to run but doesn't execute it yet.
    
    Example: {"workflow_id": "696abab2c28c63108ddb7dbe"}
    """
    try:
        result = await workflow_manager.activate_workflow(workflow_id=request.workflow_id)
        return {
            "success": result.get("success", False),
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow activation failed: {str(e)}")


@router.post("/execute")
async def execute_workflow(request: WorkflowActivateRequest):
    """
    Execute an On-Demand.io workflow.
    
    Workflows are pre-configured in the On-Demand.io platform.
    This endpoint executes them via HTTP POST.
    
    Example: {"workflow_id": "696abab2c28c63108ddb7dbe"}
    """
    try:
        result = await workflow_manager.trigger_workflow(workflow_id=request.workflow_id)
        return {
            "success": result.get("success", False),
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.post("/solana-trading-bot")
async def execute_solana_trading_bot():
    """
    🤖 Execute Solana Trading Bot
    
    Automated token analysis and swapping workflow:
    1. Check wallet for existing tokens (Solscan)
    2. Filter tokens by liquidity ≥ $250k, FDV ≥ $250k, Volume ≥ $100k
    3. Perform RSI (30-70) & MACD technical analysis
    4. Select top 2 tokens with strongest signals
    5. Execute multi-token swaps on Raydium
    
    Workflow is pre-configured in On-Demand.io platform.
    ID: 696abab2c28c63108ddb7dbe
    """
    try:
        workflow = workflow_manager.get_workflow("solana_trading_bot")
        result = await workflow_manager.trigger_workflow(workflow["id"])
        return {"success": result.get("success", False), **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trading bot execution failed: {str(e)}")


@router.get("/health")
async def workflows_health():
    """Check workflow system health."""
    return {
        "status": "healthy",
        "workflows_available": len(workflow_manager.get_all_workflows()),
        "api_connected": True,
        "execution_method": "HTTP POST to /workflow/{id}/execute"
    }

