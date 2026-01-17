"""
AI-Powered Anomaly Detection

Uses LLM (Groq with Llama 3.3) to analyze transactions and contracts for
unusual patterns, potential exploits, and suspicious behavior.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import json

from groq import AsyncGroq

from app.config import get_settings
from app.core.contract_parser import ModuleInfo
from app.core.transaction_monitor import TransactionEvent


@dataclass
class AnomalyFinding:
    """Represents an anomaly detected by AI analysis."""
    category: str
    severity: str  # low, medium, high, critical
    title: str
    description: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class AnomalyReport:
    """Complete anomaly analysis report."""
    analysis_type: str  # transaction, contract, pattern
    target: str  # address, hash, or module name
    findings: list[AnomalyFinding] = field(default_factory=list)
    summary: str = ""
    risk_assessment: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def has_critical(self) -> bool:
        return any(f.severity == "critical" for f in self.findings)
    
    @property
    def has_high(self) -> bool:
        return any(f.severity == "high" for f in self.findings)


class AnomalyDetector:
    """
    AI-powered anomaly detector using Groq (Llama 3.3 70B).
    
    Analyzes transactions and contracts for:
    - Unusual transaction patterns
    - Potential exploit attempts
    - Suspicious contract behavior
    - Deviations from normal activity
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[AsyncGroq] = None
    
    def _get_client(self) -> AsyncGroq:
        """Get or create Groq client."""
        if self._client is None:
            if not self.settings.groq_api_key:
                raise ValueError("Groq API key not configured")
            self._client = AsyncGroq(api_key=self.settings.groq_api_key)
        return self._client
    
    async def analyze_transaction(
        self,
        transaction: TransactionEvent
    ) -> AnomalyReport:
        """
        Analyze a transaction for anomalies using AI.
        
        Args:
            transaction: Transaction event to analyze
            
        Returns:
            AnomalyReport with findings
        """
        prompt = self._build_transaction_prompt(transaction)
        
        try:
            response = await self._query_llm(prompt)
            findings = self._parse_llm_response(response)
            
            return AnomalyReport(
                analysis_type="transaction",
                target=transaction.hash,
                findings=findings,
                summary=response.get("summary", ""),
                risk_assessment=response.get("risk_assessment", "Low risk")
            )
        except Exception as e:
            # Return empty report on error
            return AnomalyReport(
                analysis_type="transaction",
                target=transaction.hash,
                summary=f"Analysis failed: {str(e)}"
            )
    
    async def analyze_contract(
        self,
        module: ModuleInfo,
        additional_context: Optional[str] = None
    ) -> AnomalyReport:
        """
        Analyze a smart contract for anomalies using AI.
        
        Args:
            module: Parsed module information
            additional_context: Optional additional context
            
        Returns:
            AnomalyReport with findings
        """
        prompt = self._build_contract_prompt(module, additional_context)
        
        try:
            response = await self._query_llm(prompt)
            findings = self._parse_llm_response(response)
            
            return AnomalyReport(
                analysis_type="contract",
                target=f"{module.address}::{module.name}",
                findings=findings,
                summary=response.get("summary", ""),
                risk_assessment=response.get("risk_assessment", "Low risk")
            )
        except Exception as e:
            return AnomalyReport(
                analysis_type="contract",
                target=f"{module.address}::{module.name}",
                summary=f"Analysis failed: {str(e)}"
            )
    
    async def analyze_transaction_pattern(
        self,
        transactions: list[TransactionEvent],
        address: str
    ) -> AnomalyReport:
        """
        Analyze a pattern of transactions for anomalies.
        
        Args:
            transactions: List of recent transactions
            address: Address being analyzed
            
        Returns:
            AnomalyReport with pattern-based findings
        """
        prompt = self._build_pattern_prompt(transactions, address)
        
        try:
            response = await self._query_llm(prompt)
            findings = self._parse_llm_response(response)
            
            return AnomalyReport(
                analysis_type="pattern",
                target=address,
                findings=findings,
                summary=response.get("summary", ""),
                risk_assessment=response.get("risk_assessment", "Low risk")
            )
        except Exception as e:
            return AnomalyReport(
                analysis_type="pattern",
                target=address,
                summary=f"Analysis failed: {str(e)}"
            )
    
    def _build_transaction_prompt(self, tx: TransactionEvent) -> str:
        """Build prompt for transaction analysis."""
        tx_info = {
            "hash": tx.hash,
            "sender": tx.sender,
            "type": tx.type,
            "success": tx.success,
            "gas_used": tx.gas_used,
            "payload": tx.payload,
            "timestamp": tx.timestamp.isoformat() if tx.timestamp else None
        }
        
        return f"""Analyze this Aptos blockchain transaction for potential security concerns, anomalies, or suspicious patterns.

Transaction Data:
{json.dumps(tx_info, indent=2, default=str)}

Analyze for:
1. Suspicious function calls
2. Unusual parameter values
3. Potential exploit patterns
4. High-risk operations
5. Compliance concerns

Respond with a JSON object containing:
{{
    "findings": [
        {{
            "category": "category name",
            "severity": "low|medium|high|critical",
            "title": "short title",
            "description": "detailed description",
            "confidence": 0.0-1.0,
            "evidence": ["evidence1", "evidence2"],
            "recommendations": ["recommendation1"]
        }}
    ],
    "summary": "brief summary",
    "risk_assessment": "overall risk level and reasoning"
}}

If no issues found, return empty findings array with appropriate summary. Respond ONLY with valid JSON."""
    
    def _build_contract_prompt(
        self,
        module: ModuleInfo,
        context: Optional[str]
    ) -> str:
        """Build prompt for contract analysis."""
        module_info = {
            "address": module.address,
            "name": module.name,
            "friends": module.friends,
            "functions": [
                {
                    "name": f.name,
                    "visibility": f.visibility.value,
                    "is_entry": f.is_entry,
                    "params": f.params,
                    "returns": f.return_types
                }
                for f in module.functions
            ],
            "structs": [
                {
                    "name": s.name,
                    "abilities": s.abilities,
                    "fields": s.fields
                }
                for s in module.structs
            ]
        }
        
        context_section = f"\n\nAdditional Context:\n{context}" if context else ""
        
        return f"""Analyze this Aptos Move smart contract module for security vulnerabilities, design issues, and potential risks.

Module Data:
{json.dumps(module_info, indent=2, default=str)}{context_section}

Analyze for:
1. Access control vulnerabilities
2. Unsafe capability/resource handling
3. Logic flaws in function design
4. Potential reentrancy or DoS vectors
5. Missing input validation
6. Privilege escalation risks

Respond with a JSON object containing:
{{
    "findings": [
        {{
            "category": "category name",
            "severity": "low|medium|high|critical",
            "title": "short title",
            "description": "detailed description",
            "confidence": 0.0-1.0,
            "evidence": ["evidence1"],
            "recommendations": ["recommendation1"]
        }}
    ],
    "summary": "brief summary",
    "risk_assessment": "overall risk level and reasoning"
}}

Focus on Move-specific and Aptos-specific security considerations. Respond ONLY with valid JSON."""
    
    def _build_pattern_prompt(
        self,
        transactions: list[TransactionEvent],
        address: str
    ) -> str:
        """Build prompt for transaction pattern analysis."""
        tx_list = [
            {
                "hash": tx.hash[:16] + "...",
                "type": tx.type,
                "success": tx.success,
                "gas_used": tx.gas_used,
                "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                "payload_function": tx.payload.get("function", "") if tx.payload else ""
            }
            for tx in transactions[:20]  # Limit to 20 transactions
        ]
        
        return f"""Analyze this pattern of Aptos blockchain transactions for the address {address}.

Recent Transactions:
{json.dumps(tx_list, indent=2, default=str)}

Look for:
1. Unusual transaction frequency
2. Repeated failed transactions (potential attack attempts)
3. Suspicious function call patterns
4. Abnormal gas usage patterns
5. Signs of automated bot activity
6. Flash loan or sandwich attack patterns

Respond with a JSON object containing:
{{
    "findings": [
        {{
            "category": "category name",
            "severity": "low|medium|high|critical",
            "title": "short title",
            "description": "detailed description",
            "confidence": 0.0-1.0,
            "evidence": ["evidence1"],
            "recommendations": ["recommendation1"]
        }}
    ],
    "summary": "brief pattern analysis summary",
    "risk_assessment": "overall risk level and reasoning"
}}

Respond ONLY with valid JSON."""
    
    async def _query_llm(self, prompt: str) -> dict[str, Any]:
        """Query the LLM and parse response."""
        client = self._get_client()
        
        response = await client.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a blockchain security expert specializing in Aptos and Move smart contracts. Analyze the provided data and respond with structured JSON findings. Be thorough but avoid false positives. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content) if content else {}
    
    def _parse_llm_response(self, response: dict) -> list[AnomalyFinding]:
        """Parse LLM response into AnomalyFinding objects."""
        findings = []
        
        for finding_data in response.get("findings", []):
            findings.append(AnomalyFinding(
                category=finding_data.get("category", "Unknown"),
                severity=finding_data.get("severity", "low"),
                title=finding_data.get("title", "Untitled Finding"),
                description=finding_data.get("description", ""),
                confidence=float(finding_data.get("confidence", 0.5)),
                evidence=finding_data.get("evidence", []),
                recommendations=finding_data.get("recommendations", [])
            ))
        
        return findings


# Simple anomaly detection without LLM (fallback)
class SimpleAnomalyDetector:
    """
    Simple rule-based anomaly detector (no LLM required).
    
    Provides basic anomaly detection using heuristics.
    """
    
    def analyze_transaction(self, tx: TransactionEvent) -> AnomalyReport:
        """Simple transaction analysis without AI."""
        findings = []
        
        # Check for failed transactions
        if not tx.success:
            findings.append(AnomalyFinding(
                category="Transaction Failure",
                severity="low",
                title="Failed Transaction",
                description="Transaction failed to execute successfully.",
                confidence=1.0,
                evidence=[f"Transaction hash: {tx.hash}"]
            ))
        
        # Check for high gas usage
        if tx.gas_used > 50000:
            findings.append(AnomalyFinding(
                category="Resource Usage",
                severity="low" if tx.gas_used < 100000 else "medium",
                title="High Gas Usage",
                description=f"Transaction used {tx.gas_used} gas units.",
                confidence=0.8,
                evidence=[f"Gas used: {tx.gas_used}"]
            ))
        
        return AnomalyReport(
            analysis_type="transaction",
            target=tx.hash,
            findings=findings,
            summary="Basic rule-based analysis completed."
        )


# Singleton instances
_detector: Optional[AnomalyDetector] = None
_simple_detector: Optional[SimpleAnomalyDetector] = None


def get_anomaly_detector() -> AnomalyDetector:
    """Get or create the AI anomaly detector instance."""
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
    return _detector


def get_simple_anomaly_detector() -> SimpleAnomalyDetector:
    """Get or create the simple anomaly detector instance."""
    global _simple_detector
    if _simple_detector is None:
        _simple_detector = SimpleAnomalyDetector()
    return _simple_detector
