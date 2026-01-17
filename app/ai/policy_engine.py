"""
Compliance Policy Engine

Defines and evaluates configurable compliance policies for
transaction validation and smart contract checks.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
from datetime import datetime


class PolicySeverity(str, Enum):
    """Severity levels for policy violations."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyType(str, Enum):
    """Types of compliance policies."""
    TRANSACTION_VALUE = "transaction_value"
    BLOCKED_ADDRESS = "blocked_address"
    GAS_LIMIT = "gas_limit"
    FUNCTION_CALL = "function_call"
    CONTRACT_INTERACTION = "contract_interaction"
    CUSTOM = "custom"


@dataclass
class PolicyViolation:
    """Represents a policy violation."""
    policy_name: str
    policy_type: PolicyType
    severity: PolicySeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CompliancePolicy:
    """Defines a compliance policy."""
    name: str
    policy_type: PolicyType
    severity: PolicySeverity
    description: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    passed: bool
    violations: list[PolicyViolation] = field(default_factory=list)
    policies_checked: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class PolicyEngine:
    """
    Compliance policy engine for evaluating transactions and contracts.
    
    Provides built-in policies and supports custom policy definitions.
    """
    
    def __init__(self):
        self._policies: dict[str, CompliancePolicy] = {}
        self._blocked_addresses: set[str] = set()
        self._load_default_policies()
    
    def _load_default_policies(self):
        """Load built-in default policies."""
        # Maximum transaction value policy
        self.add_policy(CompliancePolicy(
            name="max_transaction_value",
            policy_type=PolicyType.TRANSACTION_VALUE,
            severity=PolicySeverity.HIGH,
            description="Flag transactions exceeding maximum allowed value",
            config={"max_value": 1000000000000}  # 10,000 APT in octas
        ))
        
        # Gas limit policy
        self.add_policy(CompliancePolicy(
            name="high_gas_warning",
            policy_type=PolicyType.GAS_LIMIT,
            severity=PolicySeverity.MEDIUM,
            description="Flag transactions with unusually high gas usage",
            config={"max_gas": 100000}
        ))
        
        # Blocked addresses policy (OFAC-style sanctions)
        self.add_policy(CompliancePolicy(
            name="blocked_addresses",
            policy_type=PolicyType.BLOCKED_ADDRESS,
            severity=PolicySeverity.CRITICAL,
            description="Block transactions involving sanctioned addresses",
            config={"addresses": []}
        ))
        
        # Suspicious contract interactions
        self.add_policy(CompliancePolicy(
            name="suspicious_contracts",
            policy_type=PolicyType.CONTRACT_INTERACTION,
            severity=PolicySeverity.HIGH,
            description="Flag interactions with known malicious contracts",
            config={"contracts": []}
        ))
    
    def add_policy(self, policy: CompliancePolicy):
        """Add or update a policy."""
        self._policies[policy.name] = policy
        
        # Update blocked addresses cache
        if policy.policy_type == PolicyType.BLOCKED_ADDRESS:
            addresses = policy.config.get("addresses", [])
            self._blocked_addresses.update(addr.lower() for addr in addresses)
    
    def remove_policy(self, policy_name: str):
        """Remove a policy."""
        if policy_name in self._policies:
            del self._policies[policy_name]
    
    def get_policy(self, policy_name: str) -> Optional[CompliancePolicy]:
        """Get a policy by name."""
        return self._policies.get(policy_name)
    
    def list_policies(self) -> list[CompliancePolicy]:
        """List all policies."""
        return list(self._policies.values())
    
    def add_blocked_address(self, address: str):
        """Add an address to the blocked list."""
        self._blocked_addresses.add(address.lower())
        
        # Update policy config
        policy = self._policies.get("blocked_addresses")
        if policy:
            addresses = policy.config.get("addresses", [])
            if address not in addresses:
                addresses.append(address)
                policy.config["addresses"] = addresses
    
    def remove_blocked_address(self, address: str):
        """Remove an address from the blocked list."""
        self._blocked_addresses.discard(address.lower())
    
    def check_transaction(
        self,
        sender: str,
        receiver: Optional[str] = None,
        value: int = 0,
        gas_used: int = 0,
        payload: Optional[dict] = None
    ) -> ComplianceResult:
        """
        Check a transaction against all active policies.
        
        Args:
            sender: Transaction sender address
            receiver: Optional receiver address
            value: Transaction value in octas
            gas_used: Gas used by transaction
            payload: Transaction payload
            
        Returns:
            ComplianceResult with violations if any
        """
        violations = []
        policies_checked = 0
        
        for policy in self._policies.values():
            if not policy.enabled:
                continue
            
            policies_checked += 1
            violation = self._check_policy(
                policy, sender, receiver, value, gas_used, payload
            )
            if violation:
                violations.append(violation)
        
        return ComplianceResult(
            passed=len(violations) == 0,
            violations=violations,
            policies_checked=policies_checked
        )
    
    def _check_policy(
        self,
        policy: CompliancePolicy,
        sender: str,
        receiver: Optional[str],
        value: int,
        gas_used: int,
        payload: Optional[dict]
    ) -> Optional[PolicyViolation]:
        """Check a single policy."""
        
        if policy.policy_type == PolicyType.TRANSACTION_VALUE:
            max_value = policy.config.get("max_value", float("inf"))
            if value > max_value:
                return PolicyViolation(
                    policy_name=policy.name,
                    policy_type=policy.policy_type,
                    severity=policy.severity,
                    message=f"Transaction value {value} exceeds maximum {max_value}",
                    details={"value": value, "max_value": max_value}
                )
        
        elif policy.policy_type == PolicyType.BLOCKED_ADDRESS:
            sender_lower = sender.lower() if sender else ""
            receiver_lower = receiver.lower() if receiver else ""
            
            if sender_lower in self._blocked_addresses:
                return PolicyViolation(
                    policy_name=policy.name,
                    policy_type=policy.policy_type,
                    severity=policy.severity,
                    message=f"Sender {sender} is blocked",
                    details={"blocked_address": sender, "role": "sender"}
                )
            
            if receiver_lower in self._blocked_addresses:
                return PolicyViolation(
                    policy_name=policy.name,
                    policy_type=policy.policy_type,
                    severity=policy.severity,
                    message=f"Receiver {receiver} is blocked",
                    details={"blocked_address": receiver, "role": "receiver"}
                )
        
        elif policy.policy_type == PolicyType.GAS_LIMIT:
            max_gas = policy.config.get("max_gas", float("inf"))
            if gas_used > max_gas:
                return PolicyViolation(
                    policy_name=policy.name,
                    policy_type=policy.policy_type,
                    severity=policy.severity,
                    message=f"Gas usage {gas_used} exceeds threshold {max_gas}",
                    details={"gas_used": gas_used, "max_gas": max_gas}
                )
        
        elif policy.policy_type == PolicyType.CONTRACT_INTERACTION:
            if payload:
                # Check function calls
                func = payload.get("function", "")
                blocked_contracts = policy.config.get("contracts", [])
                for contract in blocked_contracts:
                    if contract.lower() in func.lower():
                        return PolicyViolation(
                            policy_name=policy.name,
                            policy_type=policy.policy_type,
                            severity=policy.severity,
                            message=f"Interaction with suspicious contract: {contract}",
                            details={"contract": contract, "function": func}
                        )
        
        return None
    
    def get_policy_stats(self) -> dict[str, Any]:
        """Get statistics about loaded policies."""
        return {
            "total_policies": len(self._policies),
            "enabled_policies": sum(1 for p in self._policies.values() if p.enabled),
            "blocked_addresses": len(self._blocked_addresses),
            "by_severity": {
                sev.value: sum(1 for p in self._policies.values() if p.severity == sev)
                for sev in PolicySeverity
            },
            "by_type": {
                pt.value: sum(1 for p in self._policies.values() if p.policy_type == pt)
                for pt in PolicyType
            }
        }


# Singleton instance
_engine: Optional[PolicyEngine] = None


def get_policy_engine() -> PolicyEngine:
    """Get or create the policy engine instance."""
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
    return _engine
