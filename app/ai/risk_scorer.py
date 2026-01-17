"""
Risk Scorer

Aggregates findings from policy checks, vulnerability detection,
and anomaly analysis into a unified risk score.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
from datetime import datetime

from app.ai.policy_engine import ComplianceResult, PolicySeverity
from app.ai.vulnerability import VulnerabilityReport, VulnerabilitySeverity
from app.ai.anomaly import AnomalyReport


class RiskLevel(str, Enum):
    """Overall risk level classification."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskScore:
    """Aggregated risk score."""
    score: int  # 0-100
    level: RiskLevel
    breakdown: dict[str, int] = field(default_factory=dict)
    factors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ComprehensiveRiskReport:
    """Complete risk assessment report."""
    target: str  # Address, module, or transaction hash
    target_type: str  # "contract", "transaction", "address"
    risk_score: RiskScore
    compliance_result: Optional[ComplianceResult] = None
    vulnerability_report: Optional[VulnerabilityReport] = None
    anomaly_report: Optional[AnomalyReport] = None
    timestamp: datetime = field(default_factory=datetime.now)


class RiskScorer:
    """
    Aggregates multiple analysis results into a unified risk score.
    
    Combines:
    - Compliance policy violations
    - Vulnerability findings
    - Anomaly detections
    
    Into a weighted risk score (0-100).
    """
    
    # Weights for different analysis types
    WEIGHTS = {
        "compliance": 0.35,
        "vulnerability": 0.40,
        "anomaly": 0.25
    }
    
    # Severity scores
    SEVERITY_SCORES = {
        "info": 5,
        "low": 15,
        "medium": 35,
        "high": 65,
        "critical": 95
    }
    
    def calculate_risk_score(
        self,
        compliance_result: Optional[ComplianceResult] = None,
        vulnerability_report: Optional[VulnerabilityReport] = None,
        anomaly_report: Optional[AnomalyReport] = None
    ) -> RiskScore:
        """
        Calculate aggregated risk score from all analyses.
        
        Args:
            compliance_result: Policy compliance check result
            vulnerability_report: Vulnerability scan report
            anomaly_report: AI anomaly analysis report
            
        Returns:
            RiskScore with aggregated score and breakdown
        """
        breakdown = {}
        factors = []
        recommendations = []
        
        # Calculate compliance score
        compliance_score = 0
        if compliance_result:
            compliance_score = self._score_compliance(compliance_result)
            breakdown["compliance"] = compliance_score
            
            if compliance_result.violations:
                for v in compliance_result.violations:
                    factors.append(f"Policy violation: {v.message}")
                recommendations.append("Review and address policy violations")
        
        # Calculate vulnerability score
        vuln_score = 0
        if vulnerability_report:
            vuln_score = self._score_vulnerabilities(vulnerability_report)
            breakdown["vulnerability"] = vuln_score
            
            if vulnerability_report.vulnerabilities:
                for v in vulnerability_report.vulnerabilities:
                    factors.append(f"{v.severity.value.upper()}: {v.title}")
                if vulnerability_report.critical_count > 0:
                    recommendations.append("Address critical vulnerabilities immediately")
                if vulnerability_report.high_count > 0:
                    recommendations.append("Review and fix high-severity issues")
        
        # Calculate anomaly score
        anomaly_score = 0
        if anomaly_report:
            anomaly_score = self._score_anomalies(anomaly_report)
            breakdown["anomaly"] = anomaly_score
            
            for f in anomaly_report.findings:
                factors.append(f"{f.severity.upper()}: {f.title}")
                recommendations.extend(f.recommendations)
        
        # Calculate weighted total
        total_score = 0
        total_weight = 0
        
        if compliance_result:
            total_score += compliance_score * self.WEIGHTS["compliance"]
            total_weight += self.WEIGHTS["compliance"]
        
        if vulnerability_report:
            total_score += vuln_score * self.WEIGHTS["vulnerability"]
            total_weight += self.WEIGHTS["vulnerability"]
        
        if anomaly_report:
            total_score += anomaly_score * self.WEIGHTS["anomaly"]
            total_weight += self.WEIGHTS["anomaly"]
        
        # Normalize if not all analyses present
        final_score = int(total_score / total_weight) if total_weight > 0 else 0
        final_score = max(0, min(100, final_score))  # Clamp to 0-100
        
        # Determine risk level
        risk_level = self._score_to_level(final_score)
        
        # Remove duplicate recommendations
        recommendations = list(dict.fromkeys(recommendations))[:5]
        
        return RiskScore(
            score=final_score,
            level=risk_level,
            breakdown=breakdown,
            factors=factors[:10],  # Limit to top 10 factors
            recommendations=recommendations
        )
    
    def _score_compliance(self, result: ComplianceResult) -> int:
        """Calculate score from compliance result."""
        if not result.violations:
            return 0
        
        max_severity = 0
        for violation in result.violations:
            severity_score = self.SEVERITY_SCORES.get(
                violation.severity.value, 0
            )
            max_severity = max(max_severity, severity_score)
        
        # Add increment for multiple violations
        violation_count_bonus = min(len(result.violations) * 5, 25)
        
        return min(100, max_severity + violation_count_bonus)
    
    def _score_vulnerabilities(self, report: VulnerabilityReport) -> int:
        """Calculate score from vulnerability report."""
        if not report.vulnerabilities:
            return 0
        
        # Base score on highest severity
        max_severity = 0
        for vuln in report.vulnerabilities:
            severity_score = self.SEVERITY_SCORES.get(
                vuln.severity.value, 0
            )
            max_severity = max(max_severity, severity_score)
        
        # Add weighted count bonus
        count_bonus = (
            report.critical_count * 15 +
            report.high_count * 10 +
            report.medium_count * 5 +
            report.low_count * 2
        )
        
        return min(100, max_severity + min(count_bonus, 30))
    
    def _score_anomalies(self, report: AnomalyReport) -> int:
        """Calculate score from anomaly report."""
        if not report.findings:
            return 0
        
        max_severity = 0
        for finding in report.findings:
            severity_score = self.SEVERITY_SCORES.get(finding.severity, 0)
            # Weight by confidence
            weighted_score = int(severity_score * finding.confidence)
            max_severity = max(max_severity, weighted_score)
        
        # Add count bonus
        count_bonus = min(len(report.findings) * 5, 20)
        
        return min(100, max_severity + count_bonus)
    
    def _score_to_level(self, score: int) -> RiskLevel:
        """Convert numeric score to risk level."""
        if score < 10:
            return RiskLevel.SAFE
        elif score < 30:
            return RiskLevel.LOW
        elif score < 55:
            return RiskLevel.MEDIUM
        elif score < 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def create_comprehensive_report(
        self,
        target: str,
        target_type: str,
        compliance_result: Optional[ComplianceResult] = None,
        vulnerability_report: Optional[VulnerabilityReport] = None,
        anomaly_report: Optional[AnomalyReport] = None
    ) -> ComprehensiveRiskReport:
        """
        Create a comprehensive risk report combining all analyses.
        
        Args:
            target: Target identifier (address, hash, module)
            target_type: Type of target
            compliance_result: Optional compliance check result
            vulnerability_report: Optional vulnerability report
            anomaly_report: Optional anomaly report
            
        Returns:
            ComprehensiveRiskReport with all findings
        """
        risk_score = self.calculate_risk_score(
            compliance_result,
            vulnerability_report,
            anomaly_report
        )
        
        return ComprehensiveRiskReport(
            target=target,
            target_type=target_type,
            risk_score=risk_score,
            compliance_result=compliance_result,
            vulnerability_report=vulnerability_report,
            anomaly_report=anomaly_report
        )


# Singleton instance
_scorer: Optional[RiskScorer] = None


def get_risk_scorer() -> RiskScorer:
    """Get or create the risk scorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
    return _scorer
