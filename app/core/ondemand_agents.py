"""
On-Demand.io AI Agents Integration - Hackathon Edition

Powerful AI agents for blockchain smart contract security analysis,
compliance checking, and real-time threat detection.

Uses On-Demand.io Chat API with advanced AI models for intelligent analysis.
"""

import json
import os
import uuid
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.config import get_settings


class OnDemandAgentManager:
    """
    Manages interactions with On-Demand.io AI agents for blockchain security.
    
    Features:
    - Real-time smart contract vulnerability detection
    - Compliance checking against industry standards
    - AI-powered threat assessment
    - Multi-model support with streaming responses
    """
    
    # On-Demand.io API Configuration
    BASE_URL = "https://api.on-demand.io/chat/v1"
    MEDIA_URL = "https://api.on-demand.io/media/v1"
    
    # Available AI Models/Endpoints
    ENDPOINTS = {
        "gpt4o": "predefined-openai-gpt4o",
        "gpt4": "predefined-openai-gpt4.1",
        "claude": "predefined-anthropic-claude-sonnet",
        "grok": "predefined-xai-grok4.1-fast",
        "gemini": "predefined-google-gemini-2.0-flash"
    }
    
    # 6 Specialized Blockchain Security Agents
    AGENTS = {
        "threat_hunter": {
            "name": "🎯 Threat Hunter",
            "description": "Real-time blockchain threat detection and attack pattern analysis. Identifies rug pulls, honeypots, and malicious contracts.",
            "icon": "🎯",
            "color": "#ef4444",
            "system_prompt": """You are an elite blockchain threat hunter and security researcher. Your expertise includes:

1. ATTACK PATTERN DETECTION:
- Reentrancy attacks (single, cross-function, cross-contract)
- Flash loan exploits and MEV attacks
- Front-running and sandwich attacks
- Oracle manipulation and price exploits
- Governance attacks and vote manipulation

2. MALICIOUS CONTRACT IDENTIFICATION:
- Rug pull patterns (hidden mint, ownership manipulation)
- Honeypot detection (transfer restrictions, fee manipulation)
- Backdoor functions and hidden admin controls
- Fake token implementations

3. ON-CHAIN THREAT INTELLIGENCE:
- Known attacker addresses and patterns
- Recent exploit techniques
- DeFi vulnerability trends

Analyze smart contracts with extreme scrutiny. Provide specific line numbers, attack vectors, and risk assessments. Be direct about threats - user safety is paramount.""",
            "capabilities": ["Attack Pattern Detection", "Rug Pull Analysis", "Honeypot Detection", "Exploit Identification"]
        },
        "compliance_auditor": {
            "name": "⚖️ Compliance Auditor",
            "description": "Regulatory compliance verification for DeFi protocols. Checks against SEC, MiCA, and global crypto regulations.",
            "icon": "⚖️",
            "color": "#3b82f6",
            "system_prompt": """You are a blockchain regulatory compliance expert with deep knowledge of:

1. REGULATORY FRAMEWORKS:
- SEC cryptocurrency guidelines and Howey Test analysis
- MiCA (Markets in Crypto-Assets) EU regulation
- FATF Travel Rule requirements
- AML/KYC implementation standards
- FinCEN regulations and reporting requirements

2. COMPLIANCE REQUIREMENTS:
- Token classification (utility vs security)
- DeFi protocol licensing requirements
- Stablecoin reserve and reporting rules
- NFT marketplace regulations
- Cross-border transaction rules

3. SMART CONTRACT COMPLIANCE:
- Required disclosure mechanisms
- Audit trail and transparency features
- User protection mechanisms
- Emergency pause functionality
- Upgrade and governance patterns

Analyze contracts for regulatory compliance gaps. Provide specific recommendations with regulatory references. Flag potential securities law violations clearly.""",
            "capabilities": ["SEC Compliance", "MiCA Analysis", "AML/KYC Check", "Token Classification"]
        },
        "gas_wizard": {
            "name": "⛽ Gas Wizard",
            "description": "Advanced gas optimization and cost reduction analysis. Saves thousands in transaction fees with smart recommendations.",
            "icon": "⛽",
            "color": "#22c55e",
            "system_prompt": """You are a gas optimization specialist and Ethereum/Move virtual machine expert. Your focus areas:

1. STORAGE OPTIMIZATION:
- Slot packing and variable ordering
- Mappings vs arrays trade-offs
- Transient storage (EIP-1153) usage
- Storage vs memory vs calldata

2. COMPUTATION OPTIMIZATION:
- Loop optimization and unrolling
- Short-circuiting conditions
- Unchecked arithmetic blocks
- Assembly optimization opportunities
- Precompile utilization

3. PATTERN OPTIMIZATION:
- Batch operations vs single calls
- Lazy evaluation strategies
- Off-chain computation opportunities
- Event-based state tracking
- Clone and proxy patterns

4. APTOS/MOVE SPECIFIC:
- Resource efficiency
- Module organization
- Vector operations optimization
- Parallel execution patterns

Provide specific gas savings estimates with before/after code examples. Prioritize optimizations by impact and implementation difficulty.""",
            "capabilities": ["Storage Optimization", "Computation Analysis", "Batch Operations", "Cost Estimation"]
        },
        "defi_guardian": {
            "name": "🏦 DeFi Guardian",
            "description": "Specialized DeFi protocol security analysis. Protects against flash loans, oracle manipulation, and liquidity attacks.",
            "icon": "🏦",
            "color": "#8b5cf6",
            "system_prompt": """You are a DeFi security guardian specializing in decentralized finance protocol analysis:

1. LIQUIDITY VULNERABILITIES:
- Pool manipulation and imbalance attacks
- Impermanent loss exploitation
- LP token security
- Liquidity bootstrapping vulnerabilities

2. LENDING/BORROWING SECURITY:
- Collateralization ratio manipulation
- Liquidation mechanism exploits
- Interest rate manipulation
- Bad debt accumulation risks

3. ORACLE SECURITY:
- Price feed manipulation
- TWAP vs spot price vulnerabilities
- Chainlink integration patterns
- Pyth/Switchboard security (Aptos)

4. ADVANCED DeFi ATTACKS:
- Flash loan attack vectors
- Composability risks
- Protocol interaction vulnerabilities
- Cross-protocol exploits

5. YIELD/STAKING SECURITY:
- Reward calculation vulnerabilities
- Staking mechanism exploits
- Vault security patterns
- Auto-compounding risks

Analyze DeFi contracts with focus on economic attacks and financial exploits. Provide exploit scenarios and mitigation strategies.""",
            "capabilities": ["Flash Loan Protection", "Oracle Security", "Liquidity Analysis", "Yield Safety"]
        },
        "audit_master": {
            "name": "📋 Audit Master",
            "description": "Professional-grade smart contract audit reports. Generates comprehensive findings with severity ratings and fixes.",
            "icon": "📋",
            "color": "#f59e0b",
            "system_prompt": """You are a senior smart contract auditor generating professional audit reports:

1. AUDIT METHODOLOGY:
- Static analysis findings
- Manual code review
- Test coverage assessment
- Formal verification recommendations

2. VULNERABILITY CLASSIFICATION:
- Critical: Funds at immediate risk
- High: Significant security impact
- Medium: Limited security impact
- Low: Best practice violations
- Informational: Code quality suggestions

3. REPORT STRUCTURE:
- Executive Summary
- Scope and Methodology
- Findings with:
  * Title and severity
  * Description and impact
  * Proof of concept
  * Recommended fix
  * Developer response section
- Code Quality Assessment
- Test Coverage Analysis
- Recommendations Summary

4. PROFESSIONAL STANDARDS:
- CWE/SWC classification
- OWASP references
- Industry best practices
- Similar historical exploits

Generate audit-ready reports that could be submitted to clients. Include specific code references and detailed remediation steps.""",
            "capabilities": ["Full Audit Reports", "Severity Classification", "PoC Generation", "Fix Recommendations"]
        },
        "move_sensei": {
            "name": "🥋 Move Sensei",
            "description": "Aptos Move language expert. Deep analysis of Move-specific patterns, resources, and capabilities.",
            "icon": "🥋",
            "color": "#ec4899",
            "system_prompt": """You are a Move language master and Aptos blockchain expert:

1. MOVE-SPECIFIC VULNERABILITIES:
- Resource safety violations
- Capability misuse
- Acquires annotation issues
- Module initialization vulnerabilities
- Type confusion attacks

2. APTOS-SPECIFIC SECURITY:
- Coin and FungibleAsset security
- Object model vulnerabilities
- Account abstraction issues
- Transaction script security
- Multisig implementation

3. MOVE BEST PRACTICES:
- Resource management patterns
- Abort code conventions
- Event emission standards
- Access control with capabilities
- Module upgrade patterns

4. MOVE PROVER INTEGRATION:
- Specification writing
- Invariant definition
- Formal verification setup
- Property-based testing

5. APTOS FRAMEWORK USAGE:
- Correct standard library usage
- Framework module interactions
- Coin registration patterns
- NFT (Digital Assets) standards

Provide Move-specific guidance with code examples. Reference Aptos framework standards and Move language specifications.""",
            "capabilities": ["Resource Analysis", "Capability Check", "Move Prover", "Aptos Standards"]
        }
    }
    
    def __init__(self):
        """Initialize the agent manager with settings."""
        self.settings = get_settings()
        self.api_key = self.settings.ondemand_api_key
        self._sessions: Dict[str, str] = {}  # user_id -> session_id
        self._user_id = str(uuid.uuid4())  # Default user ID
    
    async def create_session(
        self,
        agent_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        context_metadata: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        """
        Create a new chat session with On-Demand.io.
        
        Args:
            agent_ids: List of agent/plugin IDs to use
            user_id: External user identifier
            context_metadata: Additional context for the session
        
        Returns:
            Session ID if successful, None otherwise
        """
        url = f"{self.BASE_URL}/sessions"
        
        payload = {
            "externalUserId": user_id or self._user_id,
            "pluginIds": agent_ids or [],
        }
        
        if context_metadata:
            payload["contextMetadata"] = context_metadata
        
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 201:
                    data = response.json()
                    session_id = data["data"]["id"]
                    print(f"✅ Created On-Demand session: {session_id}")
                    return session_id
                else:
                    print(f"❌ Session creation failed: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:
                print(f"❌ Session creation error: {str(e)}")
                return None
    
    async def submit_query(
        self,
        session_id: str,
        query: str,
        agent_id: str,
        endpoint_id: str = "predefined-openai-gpt4o",
        response_mode: str = "sync",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit a query to the On-Demand.io chat API.
        
        Args:
            session_id: The chat session ID
            query: User's question/query
            agent_id: Which internal agent to use for prompt
            endpoint_id: AI model endpoint to use
            response_mode: 'sync' or 'stream'
            context: Additional context (code, vulnerabilities, etc.)
        
        Returns:
            Response dictionary with answer and metadata
        """
        url = f"{self.BASE_URL}/sessions/{session_id}/query"
        
        # Get agent system prompt
        agent_info = self.AGENTS.get(agent_id, self.AGENTS["threat_hunter"])
        system_prompt = agent_info["system_prompt"]
        
        # Build the full query with context
        full_query = self._build_query_with_context(query, context, agent_info)
        
        payload = {
            "endpointId": endpoint_id,
            "query": full_query,
            "pluginIds": [],
            "responseMode": response_mode,
            "modelConfigs": {
                "fulfillmentPrompt": system_prompt,
                "temperature": 0.7,
                "topP": 1,
                "maxTokens": 4096,
                "presencePenalty": 0,
                "frequencyPenalty": 0
            }
        }
        
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                if response_mode == "sync":
                    response = await client.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "success": True,
                            "answer": data["data"]["answer"],
                            "session_id": data["data"]["sessionId"],
                            "message_id": data["data"]["messageId"],
                            "status": data["data"]["status"]
                        }
                    else:
                        print(f"❌ Query failed: {response.status_code} - {response.text}")
                        return {
                            "success": False,
                            "error": f"API Error: {response.status_code}",
                            "answer": self._get_fallback_response(agent_id, query, context)
                        }
                else:
                    # Streaming response
                    return await self._handle_stream_response(client, url, payload, headers)
                    
            except Exception as e:
                print(f"❌ Query error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "answer": self._get_fallback_response(agent_id, query, context)
                }
    
    async def _handle_stream_response(
        self,
        client: httpx.AsyncClient,
        url: str,
        payload: Dict,
        headers: Dict
    ) -> Dict[str, Any]:
        """Handle streaming response from On-Demand API."""
        try:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                full_answer = ""
                session_id = ""
                message_id = ""
                
                async for line in response.aiter_lines():
                    if line and line.startswith("data:"):
                        data_str = line[5:].strip()
                        
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            event = json.loads(data_str)
                            
                            if event.get("eventType") == "fulfillment":
                                if "answer" in event:
                                    full_answer += event["answer"]
                                if "sessionId" in event:
                                    session_id = event["sessionId"]
                                if "messageId" in event:
                                    message_id = event["messageId"]
                                    
                        except json.JSONDecodeError:
                            continue
                
                return {
                    "success": True,
                    "answer": full_answer,
                    "session_id": session_id,
                    "message_id": message_id,
                    "status": "completed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "answer": ""
            }
    
    def _build_query_with_context(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        agent_info: Dict
    ) -> str:
        """Build the full query with context information."""
        parts = []
        
        if context:
            if "code" in context and context["code"]:
                code = context["code"][:8000]  # Limit code length
                language = context.get("language", "move")
                parts.append(f"## Smart Contract Code ({language.upper()}):\n```{language}\n{code}\n```\n")
            
            if "vulnerabilities" in context and context["vulnerabilities"]:
                vulns = context["vulnerabilities"]
                if isinstance(vulns, list):
                    vuln_text = "\n".join([f"- {v.get('type', 'Unknown')}: {v.get('description', 'No description')}" for v in vulns[:10]])
                else:
                    vuln_text = str(vulns)
                parts.append(f"## Detected Vulnerabilities:\n{vuln_text}\n")
            
            if "contract_address" in context:
                parts.append(f"## Contract Address: {context['contract_address']}\n")
            
            if "transaction_data" in context:
                parts.append(f"## Transaction Data:\n{context['transaction_data']}\n")
        
        parts.append(f"## User Question:\n{query}")
        
        return "\n".join(parts)
    
    async def chat_with_agent(
        self,
        agent_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        model: str = "gpt4o"
    ) -> Dict[str, Any]:
        """
        Main method to chat with a specific agent.
        
        Args:
            agent_id: ID of the agent (threat_hunter, compliance_auditor, etc.)
            message: User's message
            context: Optional context with code, vulnerabilities, etc.
            session_id: Existing session ID for conversation continuity
            model: AI model to use (gpt4o, claude, grok, gemini)
        
        Returns:
            Agent response with analysis
        """
        if agent_id not in self.AGENTS:
            return {
                "success": False,
                "error": f"Unknown agent: {agent_id}",
                "agent_id": agent_id
            }
        
        agent_info = self.AGENTS[agent_id]
        
        # Create session if needed
        if not session_id:
            session_id = await self.create_session(
                context_metadata=[
                    {"key": "agent", "value": agent_id},
                    {"key": "platform", "value": "aptos-comply-agent"}
                ]
            )
        
        if not session_id:
            # Fallback if session creation fails
            return {
                "success": True,
                "agent_id": agent_id,
                "agent_name": agent_info["name"],
                "message": self._get_fallback_response(agent_id, message, context),
                "session_id": "",
                "timestamp": datetime.now().isoformat(),
                "fallback": True,
                "capabilities": agent_info.get("capabilities", [])
            }
        
        # Get endpoint ID
        endpoint_id = self.ENDPOINTS.get(model, self.ENDPOINTS["gpt4o"])
        
        # Submit query
        result = await self.submit_query(
            session_id=session_id,
            query=message,
            agent_id=agent_id,
            endpoint_id=endpoint_id,
            response_mode="sync",
            context=context
        )
        
        return {
            "success": result.get("success", False),
            "agent_id": agent_id,
            "agent_name": agent_info["name"],
            "message": result.get("answer", ""),
            "session_id": result.get("session_id", session_id),
            "message_id": result.get("message_id", ""),
            "timestamp": datetime.now().isoformat(),
            "fallback": not result.get("success", False),
            "capabilities": agent_info.get("capabilities", []),
            "model_used": model
        }
    
    async def analyze_with_all_agents(
        self,
        code: str,
        language: str = "move",
        include_agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze code with multiple agents in parallel.
        
        Args:
            code: Smart contract source code
            language: Programming language
            include_agents: Specific agents to use (default: all)
        
        Returns:
            Combined analysis from all agents
        """
        agents_to_use = include_agents or list(self.AGENTS.keys())
        context = {"code": code, "language": language}
        
        agent_questions = {
            "threat_hunter": "Analyze this smart contract for security threats, attack vectors, and malicious patterns. Identify any rug pull indicators, backdoors, or exploitable vulnerabilities.",
            "compliance_auditor": "Review this contract for regulatory compliance. Check for SEC/MiCA requirements, required disclosures, and compliance gaps.",
            "gas_wizard": "Analyze gas efficiency and provide specific optimization recommendations with estimated savings.",
            "defi_guardian": "If this is a DeFi contract, analyze for flash loan vulnerabilities, oracle manipulation risks, and liquidity attack vectors.",
            "audit_master": "Generate a professional audit summary with severity-rated findings and recommended fixes.",
            "move_sensei": "Analyze Move-specific patterns, resource safety, and Aptos framework compliance."
        }
        
        results = {}
        session_id = await self.create_session()
        
        for agent_id in agents_to_use:
            if agent_id in agent_questions:
                try:
                    result = await self.chat_with_agent(
                        agent_id=agent_id,
                        message=agent_questions[agent_id],
                        context=context,
                        session_id=session_id
                    )
                    results[agent_id] = result
                except Exception as e:
                    results[agent_id] = {
                        "success": False,
                        "agent_id": agent_id,
                        "message": f"Error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
        
        return {
            "analysis_complete": True,
            "agents_consulted": len(results),
            "session_id": session_id,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_fallback_response(
        self,
        agent_id: str,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Generate intelligent fallback responses when API is unavailable."""
        fallback_responses = {
            "threat_hunter": """## 🎯 Threat Analysis (Fallback Mode)

Based on static analysis patterns, here are key security checks to perform:

### Critical Checks:
1. **Reentrancy Protection**: Look for state changes after external calls
2. **Access Control**: Verify all privileged functions have proper authorization
3. **Input Validation**: Check for unchecked user inputs
4. **Overflow Protection**: Ensure arithmetic operations are safe

### Recommended Actions:
- Run automated security scanners (Slither, Mythril)
- Perform manual code review focusing on external calls
- Test with edge case inputs
- Review historical exploits for similar patterns

*Note: For comprehensive threat analysis, please try again when the AI service is available.*""",

            "compliance_auditor": """## ⚖️ Compliance Review (Fallback Mode)

### Regulatory Checklist:

**SEC Considerations:**
- [ ] Token utility vs security classification
- [ ] Howey Test evaluation
- [ ] Disclosure requirements

**AML/KYC:**
- [ ] Transaction monitoring capabilities
- [ ] User verification mechanisms
- [ ] Suspicious activity reporting

**Best Practices:**
- [ ] Emergency pause mechanism
- [ ] Transparent governance
- [ ] Audit trail maintenance

*Note: For detailed regulatory analysis, please try again when the AI service is available.*""",

            "gas_wizard": """## ⛽ Gas Optimization (Fallback Mode)

### Quick Optimization Tips:

1. **Storage**
   - Pack variables into single slots
   - Use events instead of storage for historical data
   - Consider transient storage for temporary data

2. **Computation**
   - Use `unchecked` blocks for safe arithmetic
   - Cache storage reads in memory
   - Short-circuit boolean operations

3. **Patterns**
   - Batch operations when possible
   - Use clones for factory patterns
   - Consider off-chain computation with on-chain verification

*Note: For specific gas estimates, please try again when the AI service is available.*""",

            "defi_guardian": """## 🏦 DeFi Security (Fallback Mode)

### Security Checklist:

**Flash Loan Protection:**
- [ ] Same-block manipulation guards
- [ ] Price oracle protections
- [ ] Slippage controls

**Liquidity Safety:**
- [ ] Pool balance validations
- [ ] LP token security
- [ ] Withdrawal restrictions

**Oracle Security:**
- [ ] Multiple oracle sources
- [ ] TWAP vs spot price usage
- [ ] Staleness checks

*Note: For comprehensive DeFi analysis, please try again when the AI service is available.*""",

            "audit_master": f"""## 📋 Audit Summary (Fallback Mode)

**Contract Analysis Report**
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

### Scope
- Manual pattern matching analysis
- Static security checks

### Preliminary Findings

| Severity | Count | Status |
|----------|-------|--------|
| Critical | - | Pending |
| High | - | Pending |
| Medium | - | Pending |
| Low | - | Pending |

### Recommendations
1. Complete full automated analysis
2. Engage professional auditor review
3. Implement comprehensive test coverage
4. Consider formal verification

*Note: For professional audit report, please try again when the AI service is available.*""",

            "move_sensei": """## 🥋 Move Analysis (Fallback Mode)

### Move/Aptos Security Checklist:

**Resource Safety:**
- [ ] Proper resource creation/destruction
- [ ] No resource duplication
- [ ] Correct acquires annotations

**Capability Patterns:**
- [ ] Capability-based access control
- [ ] Signer verification
- [ ] Module initialization

**Framework Compliance:**
- [ ] Standard coin patterns
- [ ] Object model usage
- [ ] Event emission

### Best Practices:
- Use Move Prover for formal verification
- Follow Aptos framework conventions
- Implement proper abort codes

*Note: For detailed Move analysis, please try again when the AI service is available.*"""
        }
        
        return fallback_responses.get(agent_id, "I'm here to help with smart contract analysis. Please try again when the service is available.")
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get information about all available agents."""
        return [
            {
                "id": agent_id,
                "name": info["name"],
                "description": info["description"],
                "icon": info["icon"],
                "color": info["color"],
                "capabilities": info.get("capabilities", [])
            }
            for agent_id, info in self.AGENTS.items()
        ]
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent."""
        if agent_id in self.AGENTS:
            info = self.AGENTS[agent_id]
            return {
                "id": agent_id,
                "name": info["name"],
                "description": info["description"],
                "icon": info["icon"],
                "color": info["color"],
                "capabilities": info.get("capabilities", []),
                "system_prompt": info["system_prompt"]
            }
        return None


# Singleton instance
_agent_manager: Optional[OnDemandAgentManager] = None


def get_agent_manager() -> OnDemandAgentManager:
    """Get the agent manager singleton instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = OnDemandAgentManager()
    return _agent_manager
