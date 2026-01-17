"""
Transaction API Routes

Endpoints for analyzing and monitoring transactions.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.models.schemas import (
    TransactionAnalyzeRequest,
    TransactionAnalysisResponse,
    TransactionResponse,
    ComplianceResultResponse,
    PolicyViolationResponse,
    AnomalyReportResponse,
    AnomalyFindingResponse,
    RiskScoreResponse,
    MonitorStatusResponse,
    MonitorAddressRequest,
    SeverityEnum,
    RiskLevelEnum
)
from app.core.aptos_client import get_aptos_client
from app.core.transaction_monitor import get_transaction_monitor, TransactionEvent
from app.ai.policy_engine import get_policy_engine
from app.ai.anomaly import get_anomaly_detector, get_simple_anomaly_detector
from app.ai.risk_scorer import get_risk_scorer
from app.config import get_settings


router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/{address}", response_model=list[TransactionResponse])
async def get_account_transactions(address: str, limit: int = 25):
    """Get recent transactions for an account."""
    client = await get_aptos_client()
    
    try:
        transactions = await client.get_account_transactions(address, limit=limit)
        
        return [
            TransactionResponse(
                hash=tx.get("hash", ""),
                version=int(tx.get("version", 0)),
                sender=tx.get("sender", ""),
                type=tx.get("type", "unknown"),
                success=tx.get("success", False),
                gas_used=int(tx.get("gas_used", 0)),
                timestamp=_parse_timestamp(tx.get("timestamp"))
            )
            for tx in transactions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=TransactionAnalysisResponse)
async def analyze_transaction(request: TransactionAnalyzeRequest):
    """
    Analyze a specific transaction.
    
    Performs:
    - Compliance policy check
    - AI-powered anomaly detection (optional)
    - Risk score calculation
    """
    client = await get_aptos_client()
    policy_engine = get_policy_engine()
    risk_scorer = get_risk_scorer()
    settings = get_settings()
    
    try:
        # Fetch transaction
        tx_data = await client.get_transaction_by_hash(request.hash)
        
        # Parse transaction
        tx_event = TransactionEvent(
            hash=tx_data.get("hash", ""),
            version=int(tx_data.get("version", 0)),
            sender=tx_data.get("sender", ""),
            type=tx_data.get("type", "unknown"),
            timestamp=_parse_timestamp(tx_data.get("timestamp")) or datetime.now(),
            success=tx_data.get("success", False),
            gas_used=int(tx_data.get("gas_used", 0)),
            payload=tx_data.get("payload", {}),
            changes=tx_data.get("changes", []),
            raw=tx_data
        )
        
        # Run compliance check
        compliance_result = policy_engine.check_transaction(
            sender=tx_event.sender,
            gas_used=tx_event.gas_used,
            payload=tx_event.payload
        )
        
        compliance_response = ComplianceResultResponse(
            passed=compliance_result.passed,
            violations=[
                PolicyViolationResponse(
                    policy_name=v.policy_name,
                    policy_type=v.policy_type.value,
                    severity=SeverityEnum(v.severity.value),
                    message=v.message,
                    details=v.details
                )
                for v in compliance_result.violations
            ],
            policies_checked=compliance_result.policies_checked
        )
        
        # Run anomaly detection
        anomaly_response = None
        anomaly_report = None
        
        if request.include_ai_analysis and settings.groq_api_key:
            try:
                anomaly_detector = get_anomaly_detector()
                anomaly_report = await anomaly_detector.analyze_transaction(tx_event)
                
                anomaly_response = AnomalyReportResponse(
                    analysis_type=anomaly_report.analysis_type,
                    target=anomaly_report.target,
                    findings=[
                        AnomalyFindingResponse(
                            category=f.category,
                            severity=f.severity,
                            title=f.title,
                            description=f.description,
                            confidence=f.confidence,
                            evidence=f.evidence,
                            recommendations=f.recommendations
                        )
                        for f in anomaly_report.findings
                    ],
                    summary=anomaly_report.summary,
                    risk_assessment=anomaly_report.risk_assessment
                )
            except Exception as e:
                # Fallback to simple detector
                simple_detector = get_simple_anomaly_detector()
                anomaly_report = simple_detector.analyze_transaction(tx_event)
        
        # Calculate risk score
        risk_score = risk_scorer.calculate_risk_score(
            compliance_result=compliance_result,
            anomaly_report=anomaly_report
        )
        
        risk_response = RiskScoreResponse(
            score=risk_score.score,
            level=RiskLevelEnum(risk_score.level.value),
            breakdown=risk_score.breakdown,
            factors=risk_score.factors,
            recommendations=risk_score.recommendations
        )
        
        # Build transaction response
        tx_response = TransactionResponse(
            hash=tx_event.hash,
            version=tx_event.version,
            sender=tx_event.sender,
            type=tx_event.type,
            success=tx_event.success,
            gas_used=tx_event.gas_used,
            timestamp=tx_event.timestamp
        )
        
        return TransactionAnalysisResponse(
            transaction=tx_response,
            compliance=compliance_response,
            anomalies=anomaly_response,
            risk_score=risk_response,
            analyzed_at=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/status", response_model=MonitorStatusResponse)
async def get_monitor_status():
    """Get the current status of the transaction monitor."""
    monitor = get_transaction_monitor()
    
    return MonitorStatusResponse(
        is_running=monitor.is_running,
        monitored_addresses=list(monitor._monitored_addresses),
        recent_transaction_count=len(monitor.recent_transactions),
        last_version=monitor._last_version
    )


@router.post("/monitor/start")
async def start_monitor():
    """Start the transaction monitor."""
    monitor = get_transaction_monitor()
    
    if monitor.is_running:
        return {"status": "already_running"}
    
    await monitor.start()
    return {"status": "started"}


@router.post("/monitor/stop")
async def stop_monitor():
    """Stop the transaction monitor."""
    monitor = get_transaction_monitor()
    
    if not monitor.is_running:
        return {"status": "not_running"}
    
    await monitor.stop()
    return {"status": "stopped"}


@router.post("/monitor/address")
async def add_monitored_address(request: MonitorAddressRequest):
    """Add an address to the monitoring list."""
    monitor = get_transaction_monitor()
    monitor.add_monitored_address(request.address)
    
    return {
        "status": "added",
        "address": request.address,
        "total_monitored": len(monitor._monitored_addresses)
    }


@router.delete("/monitor/address/{address}")
async def remove_monitored_address(address: str):
    """Remove an address from the monitoring list."""
    monitor = get_transaction_monitor()
    monitor.remove_monitored_address(address)
    
    return {
        "status": "removed",
        "address": address,
        "total_monitored": len(monitor._monitored_addresses)
    }


def _parse_timestamp(timestamp_str) -> datetime | None:
    """Parse Aptos timestamp to datetime."""
    if not timestamp_str:
        return None
    try:
        return datetime.fromtimestamp(int(timestamp_str) / 1_000_000)
    except (ValueError, TypeError):
        return None
