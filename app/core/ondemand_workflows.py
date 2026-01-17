"""
On-Demand.io Workflow Integration - Hackathon Edition

Activates On-Demand.io workflows built in their platform via HTTP activation endpoint.
Workflows are pre-built in the On-Demand.io platform and simply activated via API.

Example workflow: Solana Trading Bot (ID: 696abab2c28c63108ddb7dbe)
- Automated token analysis and swapping
- Multi-step agent orchestration
- Real-time notifications

Uses On-Demand.io Workflow Activation API:
POST https://api.on-demand.io/automation/api/workflow/{id}/activate
"""

import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.config import get_settings


class OnDemandWorkflowManager:
    """
    Manages On-Demand.io Workflow activations via HTTP.
    
    Workflows are built in the On-Demand.io platform and activated
    via simple HTTP POST requests.
    """
    
    # On-Demand.io Automation API
    AUTOMATION_API_URL = "https://api.on-demand.io/automation/api"
    
    # Pre-configured Workflows (built in On-Demand.io platform)
    WORKFLOWS = {
        "solana_trading_bot": {
            "id": "696abab2c28c63108ddb7dbe",
            "name": "🤖 Solana Trading Bot",
            "tagline": "Automated token analysis & swapping",
            "description": "AI-powered Solana trading bot that analyzes tokens using DEX data, performs RSI/MACD technical analysis, and executes swaps on Raydium. Automatically filters tokens by liquidity, FDV, and volume.",
            "icon": "🤖",
            "gradient": "linear-gradient(135deg, #14F195 0%, #9945FF 50%, #14F195 100%)",
            "accentColor": "#14F195",
            "trigger_type": "activate",
            "steps": [
                {"agent": "Solscan Wallet Checker", "task": "Check wallet for existing tokens", "icon": "👛"},
                {"agent": "Token Filter", "task": "Filter by liquidity, FDV, volume", "icon": "🔍"},
                {"agent": "Technical Analyzer", "task": "Calculate RSI & MACD signals", "icon": "📊"},
                {"agent": "Token Selector", "task": "Select top 2 tokens", "icon": "🎯"},
                {"agent": "Raydium Swapper", "task": "Execute multi-token swaps", "icon": "⚡"}
            ]
        }
    }
    
    def __init__(self):
        """Initialize the workflow manager."""
        settings = get_settings()
        self.api_key = settings.ondemand_api_key
    
    async def activate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Activate an On-Demand.io workflow.
        
        Activation prepares the workflow to run but doesn't execute it yet.
        
        Args:
            workflow_id: The workflow ID from On-Demand.io platform
            
        Returns:
            Dict containing activation status and details
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Activation endpoint - POST with apikey header
                url = f"{self.AUTOMATION_API_URL}/workflow/{workflow_id}/activate"
                
                response = await client.post(
                    url,
                    headers={
                        "apikey": self.api_key,
                        "Content-Type": "application/json"
                    }
                )
                
                # Try to parse JSON response
                result = None
                try:
                    if response.content:
                        result = response.json()
                except Exception:
                    result = None
                
                if response.status_code == 200 or response.status_code == 201:
                    return {
                        "success": True,
                        "workflow_id": workflow_id,
                        "execution_id": result.get("execution_id", "") if result else "",
                        "status": result.get("status", "activated") if result else "activated",
                        "message": result.get("message", "Workflow activated successfully") if result else "Workflow activated successfully",
                        "response_data": result,
                        "execution_time": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "workflow_id": workflow_id,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "url": url,
                        "response_data": result,
                        "execution_time": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": f"Exception: {str(e)}",
                "error_type": type(e).__name__,
                "execution_time": datetime.now().isoformat()
            }
    
    async def trigger_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Execute an On-Demand.io workflow.
        
        Workflows are pre-configured in the On-Demand.io platform.
        This executes them via HTTP POST.
        
        Args:
            workflow_id: The workflow ID from On-Demand.io platform
            
        Returns:
            Dict containing execution status and details
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Execution endpoint - POST with apikey header
                url = f"{self.AUTOMATION_API_URL}/workflow/{workflow_id}/execute"
                
                response = await client.post(
                    url,
                    headers={
                        "apikey": self.api_key,
                        "Content-Type": "application/json"
                    }
                )
                
                # Try to parse JSON response
                result = None
                try:
                    if response.content:
                        result = response.json()
                except Exception:
                    result = None
                
                if response.status_code == 200 or response.status_code == 201:
                    return {
                        "success": True,
                        "workflow_id": workflow_id,
                        "execution_id": result.get("execution_id", "") if result else "",
                        "status": result.get("status", "executed") if result else "executed",
                        "message": result.get("message", "Workflow executed successfully") if result else "Workflow executed successfully",
                        "response_data": result,
                        "execution_time": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "workflow_id": workflow_id,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "url": url,
                        "response_data": result,
                        "execution_time": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": f"Exception: {str(e)}",
                "error_type": type(e).__name__,
                "execution_time": datetime.now().isoformat()
            }
    
    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get all available workflow definitions."""
        return [
            {
                "id": w["id"],
                "name": w["name"],
                "tagline": w["tagline"],
                "description": w["description"],
                "icon": w["icon"],
                "gradient": w["gradient"],
                "accentColor": w["accentColor"],
                "trigger_type": w["trigger_type"],
                "steps": w["steps"],
                "params": w.get("params", {})
            }
            for key, w in self.WORKFLOWS.items()
        ]
    
    def get_workflow(self, workflow_key: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow definition by key."""
        return self.WORKFLOWS.get(workflow_key)
    
    def get_workflow_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow definition by ID."""
        for key, workflow in self.WORKFLOWS.items():
            if workflow["id"] == workflow_id:
                return workflow
        return None


# Global instance
workflow_manager = OnDemandWorkflowManager()

