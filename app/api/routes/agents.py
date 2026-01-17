"""
AI Agents API Routes - Hackathon Edition

Enhanced endpoints for On-Demand.io AI agents with advanced features.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from app.core.ondemand_agents import get_agent_manager


router = APIRouter(prefix="/agents", tags=["AI Agents"])


# ============== Request/Response Models ==============

class ChatRequest(BaseModel):
    """Request to chat with an AI agent."""
    agent_id: str = Field(..., description="ID of the agent to chat with")
    message: str = Field(..., description="User's message/question")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context (code, vulnerabilities)")
    session_id: Optional[str] = Field(None, description="Existing session ID for conversation continuity")
    model: Optional[str] = Field("gpt4o", description="AI model to use (gpt4o, claude, grok, gemini)")


class MultiAgentRequest(BaseModel):
    """Request for multi-agent analysis."""
    code: str = Field(..., description="Smart contract source code")
    language: str = Field("move", description="Programming language (move, solidity, rust)")
    agents: Optional[List[str]] = Field(None, description="Specific agents to use (default: all)")


class QuickAnalysisRequest(BaseModel):
    """Quick analysis request with code."""
    code: str = Field(..., description="Smart contract source code")
    language: str = Field("move", description="Programming language")
    focus: str = Field("security", description="Analysis focus: security, gas, compliance, defi, audit")


class AgentResponse(BaseModel):
    """Response from an AI agent."""
    success: bool
    agent_id: str
    agent_name: str
    message: str
    session_id: str
    timestamp: str
    fallback: Optional[bool] = False
    capabilities: Optional[List[str]] = []
    model_used: Optional[str] = None


# ============== Endpoints ==============

@router.get("/list")
async def list_agents():
    """
    Get list of all available AI agents with their capabilities.
    
    Returns detailed information about each specialized agent including:
    - Agent ID and name
    - Description of expertise
    - Capabilities list
    - Color scheme for UI
    """
    agent_manager = get_agent_manager()
    agents = agent_manager.get_all_agents()
    
    return {
        "agents": agents,
        "total": len(agents),
        "powered_by": "On-Demand.io",
        "available_models": list(agent_manager.ENDPOINTS.keys()),
        "description": "6 specialized AI agents for blockchain security analysis"
    }


@router.get("/info/{agent_id}")
async def get_agent_info(agent_id: str):
    """
    Get detailed information about a specific agent.
    
    Returns:
    - Full agent details
    - System prompt (for transparency)
    - Capabilities
    """
    agent_manager = get_agent_manager()
    info = agent_manager.get_agent_info(agent_id)
    
    if not info:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    return info


@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with a specific AI agent.
    
    **Available Agents:**
    - `threat_hunter`: Security threat detection, rug pull analysis
    - `compliance_auditor`: Regulatory compliance (SEC, MiCA, AML)
    - `gas_wizard`: Gas optimization and cost reduction
    - `defi_guardian`: DeFi protocol security (flash loans, oracles)
    - `audit_master`: Professional audit report generation
    - `move_sensei`: Aptos Move language expertise
    
    **Available Models:**
    - `gpt4o`: GPT-4o (default, best quality)
    - `claude`: Claude Sonnet
    - `grok`: Grok 4.1 Fast
    - `gemini`: Gemini 2.0 Flash
    """
    agent_manager = get_agent_manager()
    
    try:
        result = await agent_manager.chat_with_agent(
            agent_id=request.agent_id,
            message=request.message,
            context=request.context,
            session_id=request.session_id,
            model=request.model or "gpt4o"
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent communication failed: {str(e)}")


@router.post("/analyze/multi")
async def analyze_with_multiple_agents(request: MultiAgentRequest):
    """
    Analyze smart contract code with multiple AI agents.
    
    Runs analysis with all 6 agents (or specified subset) to provide:
    - Security threat assessment
    - Compliance review
    - Gas optimization suggestions
    - DeFi-specific vulnerabilities
    - Professional audit findings
    - Move/Aptos specific analysis
    
    This is the most comprehensive analysis option.
    """
    agent_manager = get_agent_manager()
    
    try:
        result = await agent_manager.analyze_with_all_agents(
            code=request.code,
            language=request.language,
            include_agents=request.agents
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-agent analysis failed: {str(e)}")


@router.post("/analyze/quick")
async def quick_analysis(request: QuickAnalysisRequest):
    """
    Quick focused analysis with a single specialized agent.
    
    **Focus Options:**
    - `security`: Threat Hunter - attack patterns, vulnerabilities
    - `gas`: Gas Wizard - optimization recommendations
    - `compliance`: Compliance Auditor - regulatory checks
    - `defi`: DeFi Guardian - DeFi-specific security
    - `audit`: Audit Master - audit report generation
    - `move`: Move Sensei - Move/Aptos specific
    """
    agent_manager = get_agent_manager()
    
    # Map focus to agent
    focus_to_agent = {
        "security": "threat_hunter",
        "gas": "gas_wizard",
        "compliance": "compliance_auditor",
        "defi": "defi_guardian",
        "audit": "audit_master",
        "move": "move_sensei"
    }
    
    agent_id = focus_to_agent.get(request.focus, "threat_hunter")
    
    # Quick analysis prompts
    quick_prompts = {
        "threat_hunter": "Perform a rapid security scan of this contract. Identify the top 5 most critical security issues with severity ratings.",
        "gas_wizard": "Analyze this contract for gas efficiency. Provide the top 5 optimization opportunities with estimated gas savings.",
        "compliance_auditor": "Quick compliance check. Identify the top 5 regulatory concerns and required actions.",
        "defi_guardian": "DeFi security scan. Identify flash loan risks, oracle issues, and liquidity vulnerabilities.",
        "audit_master": "Generate a quick audit summary with key findings rated by severity.",
        "move_sensei": "Analyze Move-specific patterns. Check resource safety, capabilities, and Aptos framework usage."
    }
    
    try:
        result = await agent_manager.chat_with_agent(
            agent_id=agent_id,
            message=quick_prompts[agent_id],
            context={"code": request.code, "language": request.language}
        )
        
        return {
            "focus": request.focus,
            "agent_used": agent_id,
            "analysis": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick analysis failed: {str(e)}")


@router.post("/analyze/threat-score")
async def analyze_threat_score(request: QuickAnalysisRequest):
    """
    Get a comprehensive threat score for a smart contract.
    
    Returns:
    - Overall threat score (0-100)
    - Risk level (Low, Medium, High, Critical)
    - Key threats identified
    - Recommended actions
    """
    agent_manager = get_agent_manager()
    
    try:
        result = await agent_manager.chat_with_agent(
            agent_id="threat_hunter",
            message="""Analyze this contract and provide a threat assessment in the following JSON format:
{
    "threat_score": <0-100>,
    "risk_level": "<Low|Medium|High|Critical>",
    "threats": [
        {"type": "<threat type>", "severity": "<severity>", "description": "<brief description>"}
    ],
    "is_safe": <true|false>,
    "recommended_actions": ["<action 1>", "<action 2>"],
    "summary": "<one-paragraph summary>"
}

Be strict in scoring. Any critical vulnerability should result in a score above 70.""",
            context={"code": request.code, "language": request.language}
        )
        
        # Try to parse JSON from response
        response_text = result.get("message", "")
        threat_data = None
        
        # Extract JSON if present
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                threat_data = json.loads(json_match.group())
        except:
            pass
        
        return {
            "success": True,
            "threat_assessment": threat_data,
            "raw_analysis": response_text if not threat_data else None,
            "agent_response": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Threat analysis failed: {str(e)}")


@router.post("/compare")
async def compare_contracts(
    code1: str,
    code2: str,
    language: str = "move"
):
    """
    Compare two smart contracts for security differences.
    
    Useful for:
    - Before/after security review
    - Comparing implementations
    - Upgrade safety verification
    """
    agent_manager = get_agent_manager()
    
    combined_context = {
        "code": f"=== CONTRACT 1 ===\n{code1}\n\n=== CONTRACT 2 ===\n{code2}",
        "language": language
    }
    
    try:
        result = await agent_manager.chat_with_agent(
            agent_id="audit_master",
            message="""Compare these two contract versions:
1. Identify security differences between them
2. Note any new vulnerabilities introduced in Contract 2
3. Note any vulnerabilities fixed from Contract 1
4. Provide a recommendation on which is more secure

Format your response with clear sections for:
- New Issues in Contract 2
- Issues Fixed from Contract 1  
- Unchanged Issues
- Overall Recommendation""",
            context=combined_context
        )
        
        return {
            "comparison": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/models")
async def get_available_models():
    """
    Get list of available AI models.
    
    Returns model IDs and their descriptions.
    """
    agent_manager = get_agent_manager()
    
    model_descriptions = {
        "gpt4o": {
            "name": "GPT-4o",
            "description": "OpenAI's most capable model. Best for complex analysis.",
            "speed": "medium",
            "quality": "excellent"
        },
        "gpt4": {
            "name": "GPT-4.1",
            "description": "OpenAI's GPT-4 Turbo. Great balance of speed and quality.",
            "speed": "fast",
            "quality": "very good"
        },
        "claude": {
            "name": "Claude Sonnet",
            "description": "Anthropic's Claude. Excellent for detailed explanations.",
            "speed": "medium",
            "quality": "excellent"
        },
        "grok": {
            "name": "Grok 4.1 Fast",
            "description": "xAI's Grok. Fast responses with good quality.",
            "speed": "very fast",
            "quality": "good"
        },
        "gemini": {
            "name": "Gemini 2.0 Flash",
            "description": "Google's Gemini. Optimized for speed.",
            "speed": "very fast",
            "quality": "good"
        }
    }
    
    return {
        "models": model_descriptions,
        "default": "gpt4o",
        "recommended_for_audit": "gpt4o",
        "recommended_for_quick": "grok"
    }


@router.get("/stats")
async def get_agent_stats():
    """
    Get usage statistics for the agent system.
    """
    agent_manager = get_agent_manager()
    
    return {
        "total_agents": len(agent_manager.AGENTS),
        "available_agents": list(agent_manager.AGENTS.keys()),
        "available_models": list(agent_manager.ENDPOINTS.keys()),
        "api_status": "connected",
        "powered_by": "On-Demand.io",
        "features": [
            "Multi-agent analysis",
            "Streaming responses",
            "Context-aware conversations",
            "Multiple AI model support",
            "Professional audit reports",
            "Threat scoring"
        ]
    }
