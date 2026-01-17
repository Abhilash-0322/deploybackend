"""
Pydantic Schemas

Request/response models for the API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime
from enum import Enum


# ============= Enums =============

class RiskLevelEnum(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SeverityEnum(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============= Request Models =============

class ContractAnalyzeRequest(BaseModel):
    """Request to analyze a smart contract."""
    address: str = Field(..., description="Account address with deployed contract")
    module_name: Optional[str] = Field(None, description="Specific module name (optional)")
    include_ai_analysis: bool = Field(True, description="Include AI-powered analysis")


class TransactionAnalyzeRequest(BaseModel):
    """Request to analyze a transaction."""
    hash: str = Field(..., description="Transaction hash")
    include_ai_analysis: bool = Field(True, description="Include AI-powered analysis")


class ComplianceCheckRequest(BaseModel):
    """Request to check compliance for a transaction."""
    sender: str = Field(..., description="Sender address")
    receiver: Optional[str] = Field(None, description="Receiver address")
    value: int = Field(0, description="Transaction value in octas")
    gas_used: int = Field(0, description="Gas used")
    payload: Optional[dict[str, Any]] = Field(None, description="Transaction payload")


class PolicyCreateRequest(BaseModel):
    """Request to create a new policy."""
    name: str = Field(..., description="Policy name")
    policy_type: str = Field(..., description="Policy type")
    severity: SeverityEnum = Field(..., description="Violation severity")
    description: str = Field(..., description="Policy description")
    enabled: bool = Field(True, description="Is policy enabled")
    config: dict[str, Any] = Field(default_factory=dict, description="Policy configuration")


class MonitorAddressRequest(BaseModel):
    """Request to add an address to monitoring."""
    address: str = Field(..., description="Address to monitor")


# ============= Response Models =============

class VulnerabilityResponse(BaseModel):
    """Vulnerability finding response."""
    type: str
    severity: SeverityEnum
    title: str
    description: str
    location: Optional[str] = None
    recommendation: str = ""
    confidence: float


class VulnerabilityReportResponse(BaseModel):
    """Complete vulnerability report response."""
    module_address: str
    module_name: str
    vulnerabilities: list[VulnerabilityResponse]
    summary: str
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


class AnomalyFindingResponse(BaseModel):
    """Anomaly finding response."""
    category: str
    severity: str
    title: str
    description: str
    confidence: float
    evidence: list[str] = []
    recommendations: list[str] = []


class AnomalyReportResponse(BaseModel):
    """Complete anomaly report response."""
    analysis_type: str
    target: str
    findings: list[AnomalyFindingResponse]
    summary: str
    risk_assessment: str


class RiskScoreResponse(BaseModel):
    """Risk score response."""
    score: int = Field(..., ge=0, le=100)
    level: RiskLevelEnum
    breakdown: dict[str, int]
    factors: list[str]
    recommendations: list[str]


class PolicyViolationResponse(BaseModel):
    """Policy violation response."""
    policy_name: str
    policy_type: str
    severity: SeverityEnum
    message: str
    details: dict[str, Any] = {}


class ComplianceResultResponse(BaseModel):
    """Compliance check result response."""
    passed: bool
    violations: list[PolicyViolationResponse]
    policies_checked: int


class PolicyResponse(BaseModel):
    """Policy information response."""
    name: str
    policy_type: str
    severity: SeverityEnum
    description: str
    enabled: bool
    config: dict[str, Any]


class ModuleInfoResponse(BaseModel):
    """Module information response."""
    address: str
    name: str
    friends: list[str]
    function_count: int
    struct_count: int
    exposed_functions: list[str]


class TransactionResponse(BaseModel):
    """Transaction information response."""
    hash: str
    version: int
    sender: str
    type: str
    success: bool
    gas_used: int
    timestamp: Optional[datetime] = None


class ContractAnalysisResponse(BaseModel):
    """Complete contract analysis response."""
    module: ModuleInfoResponse
    vulnerabilities: Optional[VulnerabilityReportResponse] = None
    anomalies: Optional[AnomalyReportResponse] = None
    risk_score: RiskScoreResponse
    analyzed_at: datetime = Field(default_factory=datetime.now)


class TransactionAnalysisResponse(BaseModel):
    """Complete transaction analysis response."""
    transaction: TransactionResponse
    compliance: ComplianceResultResponse
    anomalies: Optional[AnomalyReportResponse] = None
    risk_score: RiskScoreResponse
    analyzed_at: datetime = Field(default_factory=datetime.now)


class MonitorStatusResponse(BaseModel):
    """Transaction monitor status response."""
    is_running: bool
    monitored_addresses: list[str]
    recent_transaction_count: int
    last_version: Optional[int] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    aptos_network: str
    ai_enabled: bool


# ============= WebSocket Messages =============

class AlertMessage(BaseModel):
    """WebSocket alert message."""
    type: str = "alert"
    timestamp: datetime = Field(default_factory=datetime.now)
    severity: SeverityEnum
    title: str
    message: str
    details: dict[str, Any] = {}


class TransactionAlertMessage(BaseModel):
    """WebSocket transaction alert."""
    type: str = "transaction_alert"
    timestamp: datetime = Field(default_factory=datetime.now)
    transaction_hash: str
    sender: str
    risk_level: RiskLevelEnum
    risk_score: int
    violations: list[str] = []
