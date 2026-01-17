"""
Demo Contract Analysis Routes

Endpoints for analyzing the demo vulnerable contracts locally.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.models.schemas import (
    VulnerabilityReportResponse,
    VulnerabilityResponse,
    RiskScoreResponse,
    SeverityEnum,
    RiskLevelEnum
)


router = APIRouter(prefix="/demo", tags=["Demo"])


# Simulated vulnerability data for each demo contract
DEMO_CONTRACTS = {
    "vulnerable_token": {
        "name": "vulnerable_token",
        "address": "demo",
        "description": "A token contract with critical security vulnerabilities including missing signer verification and dangerous capability abilities.",
        "vulnerabilities": [
            {
                "type": "MISSING_SIGNER",
                "severity": "critical",
                "title": "Entry Function Without Signer: mint_to_anyone",
                "description": "The mint_to_anyone function is an entry point that accepts an arbitrary recipient address and amount without requiring signer verification. Anyone can mint tokens to any address.",
                "location": "vulnerable_token::mint_to_anyone",
                "recommendation": "Add a signer parameter and verify authorization before minting tokens.",
                "confidence": 0.95
            },
            {
                "type": "MISSING_SIGNER",
                "severity": "critical",
                "title": "Entry Function Without Signer: burn_from_anyone",
                "description": "The burn_from_anyone function allows burning tokens from any address without owner consent. This is a funds-at-risk vulnerability.",
                "location": "vulnerable_token::burn_from_anyone",
                "recommendation": "Require signer verification to ensure only token owners can burn their tokens.",
                "confidence": 0.95
            },
            {
                "type": "MISSING_SIGNER",
                "severity": "high",
                "title": "Entry Function Without Signer: freeze_account",
                "description": "The freeze_account function can freeze any user's account without authorization, enabling denial of service attacks.",
                "location": "vulnerable_token::freeze_account",
                "recommendation": "Implement proper admin authorization checks.",
                "confidence": 0.90
            },
            {
                "type": "CAPABILITY_LEAK_COPY",
                "severity": "high",
                "title": "Capability With Copy Ability: AdminCapability",
                "description": "AdminCapability has the 'copy' ability, which allows it to be freely duplicated. This defeats the purpose of capability-based access control.",
                "location": "vulnerable_token::AdminCapability",
                "recommendation": "Remove 'copy' ability from capability structs to prevent unauthorized duplication.",
                "confidence": 0.98
            },
            {
                "type": "CAPABILITY_LEAK_STORE",
                "severity": "medium",
                "title": "Capability With Store Ability: MinterCapability",
                "description": "MinterCapability has the 'store' ability, allowing it to be saved to global storage locations that may be accessible by untrusted code.",
                "location": "vulnerable_token::MinterCapability",
                "recommendation": "Consider removing 'store' ability or implementing strict access controls.",
                "confidence": 0.85
            },
            {
                "type": "PUBLIC_FUNCTION_EXPOSURE",
                "severity": "low",
                "title": "Public Helper Function: get_raw_balance",
                "description": "Internal helper function get_raw_balance is marked public, potentially exposing implementation details.",
                "location": "vulnerable_token::get_raw_balance",
                "recommendation": "Mark as public(friend) or make private if not needed externally.",
                "confidence": 0.75
            }
        ]
    },
    "insecure_dex": {
        "name": "insecure_dex",
        "address": "demo",
        "description": "A DEX contract with severe access control flaws, excessive friend declarations, and functions that can drain user funds.",
        "vulnerabilities": [
            {
                "type": "MISSING_SIGNER",
                "severity": "critical",
                "title": "Entry Function Without Signer: swap_tokens_unprotected",
                "description": "The swap function executes trades on behalf of any user without authorization. Attackers can manipulate user positions.",
                "location": "insecure_dex::swap_tokens_unprotected",
                "recommendation": "Require signer verification to ensure only the user can initiate their own swaps.",
                "confidence": 0.95
            },
            {
                "type": "MISSING_SIGNER",
                "severity": "critical",
                "title": "Entry Function Without Signer: withdraw_liquidity_unsafe",
                "description": "Anyone can withdraw liquidity from any provider's position without ownership verification. Direct theft vector.",
                "location": "insecure_dex::withdraw_liquidity_unsafe",
                "recommendation": "Add signer parameter and verify LP token ownership before withdrawal.",
                "confidence": 0.95
            },
            {
                "type": "MISSING_SIGNER",
                "severity": "critical",
                "title": "Entry Function Without Signer: emergency_drain",
                "description": "CRITICAL: An 'emergency' function that can drain the entire pool to any address without any authorization checks.",
                "location": "insecure_dex::emergency_drain",
                "recommendation": "Implement multi-sig or time-locked emergency functions with proper admin verification.",
                "confidence": 0.99
            },
            {
                "type": "EXCESSIVE_FRIENDS",
                "severity": "medium",
                "title": "Excessive Friend Declarations (6 modules)",
                "description": "The module declares 6 friend modules, significantly expanding the trust boundary. Each friend can access internal functions.",
                "location": "insecure_dex module header",
                "recommendation": "Minimize friend declarations and use capability-based access instead.",
                "confidence": 0.90
            },
            {
                "type": "LOGIC_FLAW",
                "severity": "high",
                "title": "Slippage Protection Ignored",
                "description": "The swap function accepts min_amount_out parameter but never actually enforces the slippage check, exposing users to sandwich attacks.",
                "location": "insecure_dex::swap_tokens_unprotected",
                "recommendation": "Implement and enforce slippage protection: assert!(amount_out >= min_amount_out, ERROR_SLIPPAGE)",
                "confidence": 0.85
            }
        ]
    },
    "risky_nft": {
        "name": "risky_nft",
        "address": "demo",
        "description": "An NFT contract vulnerable to unauthorized transfers, burns, and metadata manipulation attacks.",
        "vulnerabilities": [
            {
                "type": "MISSING_SIGNER",
                "severity": "critical",
                "title": "Entry Function Without Signer: transfer_nft_unsafe",
                "description": "NFTs can be transferred by anyone without owner authorization. This enables direct theft of all NFTs in the collection.",
                "location": "risky_nft::transfer_nft_unsafe",
                "recommendation": "Require signer verification and validate ownership before transfer.",
                "confidence": 0.95
            },
            {
                "type": "MISSING_SIGNER",
                "severity": "critical",
                "title": "Entry Function Without Signer: burn_nft_unprotected",
                "description": "Any user can burn any NFT without the owner's consent, causing permanent loss of assets.",
                "location": "risky_nft::burn_nft_unprotected",
                "recommendation": "Add signer parameter and verify the caller is the NFT owner.",
                "confidence": 0.95
            },
            {
                "type": "MISSING_SIGNER",
                "severity": "high",
                "title": "Entry Function Without Signer: update_metadata_unsafe",
                "description": "NFT metadata (URI) can be modified without authorization. Attackers could replace legitimate artwork with malicious content.",
                "location": "risky_nft::update_metadata_unsafe",
                "recommendation": "Implement creator/owner verification for metadata updates.",
                "confidence": 0.90
            },
            {
                "type": "MISSING_SIGNER",
                "severity": "high",
                "title": "Entry Function Without Signer: free_mint_unlimited",
                "description": "Minting function requires no signer, no payment, and ignores max supply limits. Enables unlimited free minting.",
                "location": "risky_nft::free_mint_unlimited",
                "recommendation": "Require payment, enforce max supply, and add signer verification.",
                "confidence": 0.90
            }
        ]
    }
}


class DemoContractInfo(BaseModel):
    name: str
    address: str
    description: str
    vulnerability_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


class DemoContractsResponse(BaseModel):
    contracts: list[DemoContractInfo]
    total_vulnerabilities: int


@router.get("/contracts", response_model=DemoContractsResponse)
async def list_demo_contracts():
    """List all demo contracts available for analysis."""
    contracts = []
    total_vulns = 0
    
    for name, data in DEMO_CONTRACTS.items():
        vulns = data["vulnerabilities"]
        total_vulns += len(vulns)
        
        contracts.append(DemoContractInfo(
            name=data["name"],
            address=data["address"],
            description=data["description"],
            vulnerability_count=len(vulns),
            critical_count=sum(1 for v in vulns if v["severity"] == "critical"),
            high_count=sum(1 for v in vulns if v["severity"] == "high"),
            medium_count=sum(1 for v in vulns if v["severity"] == "medium"),
            low_count=sum(1 for v in vulns if v["severity"] == "low")
        ))
    
    return DemoContractsResponse(contracts=contracts, total_vulnerabilities=total_vulns)


class DemoAnalysisResponse(BaseModel):
    contract_name: str
    address: str
    description: str
    vulnerabilities: VulnerabilityReportResponse
    risk_score: RiskScoreResponse
    source_code: Optional[str] = None


@router.get("/contracts/{contract_name}/analyze", response_model=DemoAnalysisResponse)
async def analyze_demo_contract(contract_name: str, include_source: bool = True):
    """
    Analyze a specific demo contract.
    
    This demonstrates the compliance agent's detection capabilities
    using intentionally vulnerable contracts.
    """
    if contract_name not in DEMO_CONTRACTS:
        raise HTTPException(
            status_code=404,
            detail=f"Demo contract '{contract_name}' not found. Available: {list(DEMO_CONTRACTS.keys())}"
        )
    
    contract_data = DEMO_CONTRACTS[contract_name]
    vulns = contract_data["vulnerabilities"]
    
    # Build vulnerability report
    vuln_responses = [
        VulnerabilityResponse(
            type=v["type"],
            severity=SeverityEnum(v["severity"]),
            title=v["title"],
            description=v["description"],
            location=v["location"],
            recommendation=v["recommendation"],
            confidence=v["confidence"]
        )
        for v in vulns
    ]
    
    critical_count = sum(1 for v in vulns if v["severity"] == "critical")
    high_count = sum(1 for v in vulns if v["severity"] == "high")
    medium_count = sum(1 for v in vulns if v["severity"] == "medium")
    low_count = sum(1 for v in vulns if v["severity"] == "low")
    
    vuln_report = VulnerabilityReportResponse(
        module_address="demo",
        module_name=contract_name,
        vulnerabilities=vuln_responses,
        summary=f"Found {len(vulns)} vulnerabilities: {critical_count} critical, {high_count} high, {medium_count} medium, {low_count} low.",
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count
    )
    
    # Calculate risk score
    score = min(100, critical_count * 25 + high_count * 15 + medium_count * 8 + low_count * 3)
    
    if score >= 90:
        level = RiskLevelEnum.CRITICAL
    elif score >= 70:
        level = RiskLevelEnum.HIGH
    elif score >= 40:
        level = RiskLevelEnum.MEDIUM
    elif score >= 15:
        level = RiskLevelEnum.LOW
    else:
        level = RiskLevelEnum.SAFE
    
    # Build factors list, filtering out None values
    factors_list = [
        f"{critical_count} critical vulnerabilities detected" if critical_count > 0 else None,
        f"{high_count} high-severity issues found" if high_count > 0 else None,
        "Missing signer verification on entry functions" if any(v["type"] == "MISSING_SIGNER" for v in vulns) else None,
        "Capability structs with dangerous abilities" if any("CAPABILITY" in v["type"] for v in vulns) else None,
        "Excessive friend module declarations" if any("FRIEND" in v["type"] for v in vulns) else None,
    ]
    factors_list = [f for f in factors_list if f is not None]
    
    risk_score = RiskScoreResponse(
        score=score,
        level=level,
        breakdown={
            "critical_issues": critical_count * 25,
            "high_issues": high_count * 15,
            "medium_issues": medium_count * 8,
            "low_issues": low_count * 3
        },
        factors=factors_list,
        recommendations=[
            "Do NOT deploy this contract to mainnet",
            "Add signer verification to all entry functions",
            "Remove 'copy' ability from capability structs",
            "Implement proper access control mechanisms"
        ]
    )
    
    # Optionally include source code
    source_code = None
    if include_source:
        source_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "contracts", "sources", f"{contract_name}.move"
        )
        try:
            with open(source_path, 'r') as f:
                source_code = f.read()
        except FileNotFoundError:
            pass
    
    return DemoAnalysisResponse(
        contract_name=contract_name,
        address="demo",
        description=contract_data["description"],
        vulnerabilities=vuln_report,
        risk_score=risk_score,
        source_code=source_code
    )


@router.get("/contracts/{contract_name}/source")
async def get_demo_contract_source(contract_name: str):
    """Get the source code of a demo contract."""
    source_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "contracts", "sources", f"{contract_name}.move"
    )
    
    try:
        with open(source_path, 'r') as f:
            return {"contract_name": contract_name, "source_code": f.read()}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Source file not found for {contract_name}")
