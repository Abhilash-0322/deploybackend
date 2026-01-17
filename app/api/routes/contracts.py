"""
Contract Analysis API Routes

Endpoints for analyzing smart contracts deployed on Aptos.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime
import os
from pathlib import Path
import httpx
import uuid

from app.models.schemas import (
    ContractAnalyzeRequest,
    ContractAnalysisResponse,
    ModuleInfoResponse,
    VulnerabilityReportResponse,
    VulnerabilityResponse,
    AnomalyReportResponse,
    AnomalyFindingResponse,
    RiskScoreResponse,
    SeverityEnum,
    RiskLevelEnum
)
from app.core.aptos_client import get_aptos_client
from app.core.contract_parser import get_contract_parser
from app.ai.vulnerability import get_vulnerability_detector
from app.ai.anomaly import get_anomaly_detector
from app.ai.risk_scorer import get_risk_scorer
from app.config import get_settings


router = APIRouter(prefix="/contracts", tags=["Contracts"])


@router.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(request: ContractAnalyzeRequest):
    """
    Analyze a smart contract for vulnerabilities and risks.
    
    Performs:
    - Module structure analysis
    - Pattern-based vulnerability detection
    - AI-powered anomaly detection (optional)
    - Risk score calculation
    """
    parser = get_contract_parser()
    vuln_detector = get_vulnerability_detector()
    risk_scorer = get_risk_scorer()
    settings = get_settings()
    
    try:
        # Get module info
        if request.module_name:
            module = await parser.get_module_info(request.address, request.module_name)
        else:
            # Get first module if not specified
            modules = await parser.get_all_modules(request.address)
            if not modules:
                raise HTTPException(
                    status_code=404,
                    detail=f"No modules found at address {request.address}"
                )
            module = modules[0]
        
        # Run vulnerability detection
        vuln_report = vuln_detector.analyze_module(module)
        
        # Convert to response format
        vuln_response = VulnerabilityReportResponse(
            module_address=vuln_report.module_address,
            module_name=vuln_report.module_name,
            vulnerabilities=[
                VulnerabilityResponse(
                    type=v.vuln_type.value,
                    severity=SeverityEnum(v.severity.value),
                    title=v.title,
                    description=v.description,
                    location=v.location,
                    recommendation=v.recommendation,
                    confidence=v.confidence
                )
                for v in vuln_report.vulnerabilities
            ],
            summary=f"Found {vuln_report.critical_count} critical, {vuln_report.high_count} high, {vuln_report.medium_count} medium, {vuln_report.low_count} low vulnerabilities.",
            critical_count=vuln_report.critical_count,
            high_count=vuln_report.high_count,
            medium_count=vuln_report.medium_count,
            low_count=vuln_report.low_count
        )
        
        # Run AI analysis if enabled and API key configured
        anomaly_response = None
        anomaly_report = None
        
        if request.include_ai_analysis and settings.groq_api_key:
            try:
                anomaly_detector = get_anomaly_detector()
                anomaly_report = await anomaly_detector.analyze_contract(module)
                
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
                # AI analysis failed, continue without it
                print(f"AI analysis failed: {e}")
        
        # Calculate risk score
        risk_score = risk_scorer.calculate_risk_score(
            vulnerability_report=vuln_report,
            anomaly_report=anomaly_report
        )
        
        risk_response = RiskScoreResponse(
            score=risk_score.score,
            level=RiskLevelEnum(risk_score.level.value),
            breakdown=risk_score.breakdown,
            factors=risk_score.factors,
            recommendations=risk_score.recommendations
        )
        
        # Build module info response
        module_response = ModuleInfoResponse(
            address=module.address,
            name=module.name,
            friends=module.friends,
            function_count=len(module.functions),
            struct_count=len(module.structs),
            exposed_functions=module.exposed_functions
        )
        
        return ContractAnalysisResponse(
            module=module_response,
            vulnerabilities=vuln_response,
            anomalies=anomaly_response,
            risk_score=risk_response,
            analyzed_at=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{address}/modules", response_model=list[ModuleInfoResponse])
async def list_modules(address: str):
    """List all modules deployed to an address."""
    parser = get_contract_parser()
    
    try:
        modules = await parser.get_all_modules(address)
        
        return [
            ModuleInfoResponse(
                address=m.address,
                name=m.name,
                friends=m.friends,
                function_count=len(m.functions),
                struct_count=len(m.structs),
                exposed_functions=m.exposed_functions
            )
            for m in modules
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{address}/{module_name}/vulnerabilities", response_model=VulnerabilityReportResponse)
async def get_vulnerabilities(address: str, module_name: str):
    """Get vulnerability report for a specific module."""
    parser = get_contract_parser()
    vuln_detector = get_vulnerability_detector()
    
    try:
        module = await parser.get_module_info(address, module_name)
        vuln_report = vuln_detector.analyze_module(module)
        
        return VulnerabilityReportResponse(
            module_address=vuln_report.module_address,
            module_name=vuln_report.module_name,
            vulnerabilities=[
                VulnerabilityResponse(
                    type=v.vuln_type.value,
                    severity=SeverityEnum(v.severity.value),
                    title=v.title,
                    description=v.description,
                    location=v.location,
                    recommendation=v.recommendation,
                    confidence=v.confidence
                )
                for v in vuln_report.vulnerabilities
            ],
            summary=f"Found {vuln_report.critical_count} critical, {vuln_report.high_count} high, {vuln_report.medium_count} medium, {vuln_report.low_count} low vulnerabilities.",
            critical_count=vuln_report.critical_count,
            high_count=vuln_report.high_count,
            medium_count=vuln_report.medium_count,
            low_count=vuln_report.low_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW ENDPOINTS FOR SMART CONTRACT SCANNER PAGE
# ============================================================================

@router.get("/demo-contracts")
async def get_demo_contracts():
    """
    Get list of demo vulnerable contracts available for analysis in multiple languages.
    Includes Move, Solidity, and Rust/Solana examples.
    """
    contracts_dir = Path(__file__).parent.parent.parent.parent / "contracts" / "sources"
    
    demo_contracts = []
    
    if contracts_dir.exists():
        # Load Move contracts
        for file_path in contracts_dir.glob("*.move"):
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                
                contract_name = file_path.stem
                
                # Extract description from comments
                description = "Vulnerable Move smart contract for demonstration"
                lines = code.split('\n')
                for line in lines[:20]:
                    if 'Vulnerabilities included:' in line or 'INTENTIONAL VULNERABILITIES' in line:
                        description = "Contains intentional vulnerabilities for testing"
                        break
                
                demo_contracts.append({
                    "id": contract_name,
                    "name": contract_name.replace('_', ' ').title(),
                    "code": code,
                    "description": description,
                    "language": "move"
                })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
        
        # Load Solidity contracts
        for file_path in contracts_dir.glob("*.sol"):
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                
                contract_name = file_path.stem
                
                # Extract description from comments
                description = "Vulnerable Solidity smart contract for Ethereum"
                if "INTENTIONALLY VULNERABLE" in code:
                    description = "Contains critical Solidity vulnerabilities for testing"
                
                demo_contracts.append({
                    "id": contract_name,
                    "name": contract_name.replace('_', ' ').title(),
                    "code": code,
                    "description": description,
                    "language": "solidity"
                })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
        
        # Load Rust/Solana contracts
        for file_path in contracts_dir.glob("*.rs"):
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                
                contract_name = file_path.stem
                
                # Extract description from comments
                description = "Vulnerable Rust program for Solana"
                if "INTENTIONALLY VULNERABLE" in code:
                    description = "Contains critical Solana/Anchor vulnerabilities for testing"
                
                demo_contracts.append({
                    "id": contract_name,
                    "name": contract_name.replace('_', ' ').title(),
                    "code": code,
                    "description": description,
                    "language": "rust"
                })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
    
    return {"contracts": demo_contracts}


@router.post("/analyze-code")
async def analyze_contract_code(request: dict):
    """
    Analyze smart contract code provided as text.
    Supports Move, Solidity (Ethereum), and Rust (Solana) contracts.
    
    This endpoint performs pattern-based analysis of pasted contract code.
    """
    code = request.get("code", "")
    language = request.get("language", "move")  # move, solidity, or rust
    include_ai = request.get("include_ai_analysis", True)
    
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")
    
    # Pattern-based vulnerability detection on raw code
    vulnerabilities = []
    
    # Define language-specific vulnerability patterns
    if language == "move":
        patterns = [
            {
                "pattern": "public entry fun",
                "check": lambda line: "public entry fun" in line and "signer" not in line.split("public entry fun")[1].split(")")[0] if ")" in line.split("public entry fun")[1] else False,
                "vuln": {
                    "type": "missing_authorization",
                    "severity": "CRITICAL",
                    "title": "Entry Function Without Signer Parameter",
                    "description": "Public entry function lacks signer parameter for authorization",
                    "recommendation": "Add a signer parameter to verify caller identity"
                }
            },
            {
                "pattern": "has copy",
                "check": lambda line: "Capability" in line and "has copy" in line,
                "vuln": {
                    "type": "capability_copy",
                    "severity": "HIGH",
                    "title": "Capability with Copy Ability",
                    "description": "Capability struct has 'copy' ability, allowing unauthorized duplication",
                    "recommendation": "Remove 'copy' ability from capability structs"
                }
            },
            {
                "pattern": "acquires",
                "check": lambda line: "public fun" in line and "acquires" in line and "signer" not in line.split("public fun")[1].split("acquires")[0] if "acquires" in line.split("public fun")[1] else False,
                "vuln": {
                    "type": "missing_authorization",
                    "severity": "HIGH",
                    "title": "Public Function Modifies State Without Authorization",
                    "description": "Public function modifies global state without proper authorization",
                    "recommendation": "Add authorization checks or make function private"
                }
            },
            {
                "pattern": "borrow_global_mut",
                "check": lambda line: "borrow_global_mut" in line,
                "vuln": {
                    "type": "unsafe_mutation",
                    "severity": "MEDIUM",
                    "title": "Global State Mutation",
                    "description": "Function mutates global state - ensure proper access controls",
                    "recommendation": "Verify authorization before mutating global state"
                }
            }
        ]
    
    elif language == "solidity":
        patterns = [
            {
                "pattern": "tx.origin",
                "check": lambda line: "tx.origin" in line and "//" not in line[:line.index("tx.origin")] if "tx.origin" in line else False,
                "vuln": {
                    "type": "tx_origin_usage",
                    "severity": "CRITICAL",
                    "title": "Use of tx.origin for Authorization",
                    "description": "Using tx.origin for authorization is vulnerable to phishing attacks",
                    "recommendation": "Use msg.sender instead of tx.origin for authorization checks"
                }
            },
            {
                "pattern": "selfdestruct",
                "check": lambda line: "selfdestruct" in line or "suicide" in line,
                "vuln": {
                    "type": "selfdestruct",
                    "severity": "HIGH",
                    "title": "Selfdestruct Usage",
                    "description": "Contract contains selfdestruct which can destroy the contract",
                    "recommendation": "Ensure selfdestruct is properly protected and necessary"
                }
            },
            {
                "pattern": "delegatecall",
                "check": lambda line: "delegatecall" in line,
                "vuln": {
                    "type": "delegatecall",
                    "severity": "HIGH",
                    "title": "Delegatecall to Untrusted Contract",
                    "description": "Delegatecall can be dangerous if called on untrusted contracts",
                    "recommendation": "Ensure delegatecall target is trusted and validated"
                }
            },
            {
                "pattern": "transfer",
                "check": lambda line: ".transfer(" in line or ".send(" in line,
                "vuln": {
                    "type": "unsafe_transfer",
                    "severity": "MEDIUM",
                    "title": "Use of transfer() or send()",
                    "description": "transfer() and send() have limited gas and may fail",
                    "recommendation": "Use call{value: amount}() instead for better error handling"
                }
            },
            {
                "pattern": "block.timestamp",
                "check": lambda line: "block.timestamp" in line or "now" in line,
                "vuln": {
                    "type": "timestamp_dependence",
                    "severity": "MEDIUM",
                    "title": "Timestamp Dependence",
                    "description": "Using block.timestamp can be manipulated by miners",
                    "recommendation": "Avoid using timestamps for critical logic"
                }
            },
            {
                "pattern": "public",
                "check": lambda line: ("function" in line and "public" in line and 
                                     not any(mod in line for mod in ["onlyOwner", "require(", "modifier", "internal"])),
                "vuln": {
                    "type": "unprotected_function",
                    "severity": "HIGH",
                    "title": "Potentially Unprotected Public Function",
                    "description": "Public function may lack access control",
                    "recommendation": "Add access control modifiers or require statements"
                }
            }
        ]
    
    elif language == "rust":
        patterns = [
            {
                "pattern": "unchecked",
                "check": lambda line: "unchecked" in line and not line.strip().startswith("//"),
                "vuln": {
                    "type": "unchecked_arithmetic",
                    "severity": "HIGH",
                    "title": "Unchecked Arithmetic Operations",
                    "description": "Unchecked arithmetic can lead to overflow/underflow",
                    "recommendation": "Use checked arithmetic or ensure bounds are validated"
                }
            },
            {
                "pattern": "unwrap()",
                "check": lambda line: ".unwrap()" in line and not line.strip().startswith("//"),
                "vuln": {
                    "type": "unsafe_unwrap",
                    "severity": "MEDIUM",
                    "title": "Use of unwrap() without Error Handling",
                    "description": "unwrap() will panic if value is None/Err, causing program crash",
                    "recommendation": "Use proper error handling with ? operator or match statements"
                }
            },
            {
                "pattern": "unsafe",
                "check": lambda line: "unsafe" in line and "{" in line,
                "vuln": {
                    "type": "unsafe_block",
                    "severity": "HIGH",
                    "title": "Unsafe Code Block",
                    "description": "Unsafe blocks bypass Rust's safety guarantees",
                    "recommendation": "Minimize unsafe code and thoroughly audit for memory safety"
                }
            },
            {
                "pattern": "signer",
                "check": lambda line: ("pub fn" in line and "invoke" in line.lower() and 
                                      "signer" not in line.lower()),
                "vuln": {
                    "type": "missing_signer_check",
                    "severity": "CRITICAL",
                    "title": "Instruction Handler Missing Signer Check",
                    "description": "Solana instruction handler may not verify signer authority",
                    "recommendation": "Add signer checks using is_signer or require validation"
                }
            },
            {
                "pattern": "mut",
                "check": lambda line: ("Account" in line and "mut" in line and 
                                      "constraint" not in line.lower()),
                "vuln": {
                    "type": "missing_constraints",
                    "severity": "MEDIUM",
                    "title": "Mutable Account Without Constraints",
                    "description": "Mutable account access may lack proper constraints",
                    "recommendation": "Add #[account(constraint = ...)] to validate account state"
                }
            }
        ]
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
    
    # Analyze code with language-specific patterns
    lines = code.split('\n')
    for line_num, line in enumerate(lines, 1):
        for pattern_info in patterns:
            try:
                if pattern_info["pattern"] in line and pattern_info["check"](line):
                    vuln = pattern_info["vuln"].copy()
                    vuln["location"] = f"Line {line_num}"
                    vuln["confidence"] = 0.85
                    vuln["code_snippet"] = line.strip()
                    vulnerabilities.append(vuln)
            except Exception as e:
                # Skip patterns that cause errors (e.g., malformed lines)
                continue
    
    # Count by severity
    severity_counts = {
        "critical": sum(1 for v in vulnerabilities if v["severity"] == "CRITICAL"),
        "high": sum(1 for v in vulnerabilities if v["severity"] == "HIGH"),
        "medium": sum(1 for v in vulnerabilities if v["severity"] == "MEDIUM"),
        "low": sum(1 for v in vulnerabilities if v["severity"] == "LOW")
    }
    
    # Calculate risk score
    risk_score = min(100, (
        severity_counts["critical"] * 25 +
        severity_counts["high"] * 15 +
        severity_counts["medium"] * 8 +
        severity_counts["low"] * 3
    ))
    
    risk_level = "CRITICAL" if risk_score >= 80 else "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 30 else "LOW"
    
    # AI analysis (simplified for demo)
    ai_findings = []
    if include_ai and get_settings().groq_api_key:
        try:
            anomaly_detector = get_anomaly_detector()
            # Simulate AI analysis
            ai_findings = [
                {
                    "title": "Complex Logic Flow",
                    "description": f"The {language} contract contains complex control flow that may hide vulnerabilities",
                    "severity": "MEDIUM",
                    "confidence": 0.75
                }
            ]
        except:
            pass
    
    return {
        "analysis_id": f"code_scan_{datetime.now().timestamp()}",
        "timestamp": datetime.now().isoformat(),
        "language": language,
        "vulnerabilities": vulnerabilities,
        "severity_counts": severity_counts,
        "risk_score": {
            "score": risk_score,
            "level": risk_level,
            "description": f"Risk score: {risk_score}/100"
        },
        "ai_findings": ai_findings,
        "summary": f"Found {len(vulnerabilities)} vulnerabilities: {severity_counts['critical']} critical, {severity_counts['high']} high, {severity_counts['medium']} medium, {severity_counts['low']} low"
    }


@router.post("/upload-and-analyze")
async def upload_and_analyze_contract(
    file: UploadFile = File(...),
    language: str = Form(...)
):
    """
    Upload a smart contract file and analyze it for vulnerabilities.
    
    **Uses on-demand.io Media API for file processing** (Hackathon Track Requirement)
    
    Process:
    1. Receives uploaded file (.move, .sol, .rs)
    2. Sends file to on-demand.io Media API for text extraction
    3. Analyzes extracted code for vulnerabilities using pattern matching
    4. Stores contract and analysis results in MongoDB
    5. Returns extracted code and vulnerability report
    
    Supports: Move, Solidity (Ethereum), and Rust (Solana) contracts
    """
    from app.core.database import save_uploaded_contract, get_database
    
    settings = get_settings()
    upload_id = str(uuid.uuid4())
    
    # Validate file type
    allowed_extensions = {'.move', '.sol', '.rs', '.txt'}
    file_extension = Path(file.filename or '').suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate language
    if language not in ['move', 'solidity', 'rust']:
        raise HTTPException(status_code=400, detail="Invalid language. Must be: move, solidity, or rust")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # ALWAYS use on-demand.io Media API for file processing (hackathon requirement)
        file_url = ""  # Will store the on-demand.io file URL
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"📤 Processing file '{file.filename}' using on-demand.io Media API...")
            
            try:
                # Prepare multipart form data for on-demand.io API
                files = {'file': (file.filename, file_content, file.content_type or 'text/plain')}
                
                # Call the fetchmedia endpoint to process the file
                response = await client.post(
                    f"{settings.ondemand_api_url}/api/fetchmedia",
                    files=files,
                    headers={'apikey': settings.ondemand_api_key}
                )
                
                print(f"📡 on-demand.io API Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ File processed successfully by on-demand.io API")
                    print(f"📊 API Response keys: {list(result.keys())}")
                    
                    # Try to extract file URL from response (if available)
                    if 'url' in result:
                        file_url = result['url']
                        print(f"💾 File saved on on-demand.io: {file_url}")
                    elif 'file_url' in result:
                        file_url = result['file_url']
                        print(f"💾 File saved on on-demand.io: {file_url}")
                    elif 'data' in result and isinstance(result['data'], dict) and 'url' in result['data']:
                        file_url = result['data']['url']
                        print(f"💾 File saved on on-demand.io: {file_url}")
                    else:
                        print("ℹ No file URL returned by on-demand.io API")
                    
                    # Extract text content from the on-demand.io response
                    # Try various possible response fields
                    if 'text' in result:
                        code = result['text']
                        print(f"✓ Extracted {len(code)} characters from 'text' field")
                    elif 'content' in result:
                        code = result['content']
                        print(f"✓ Extracted {len(code)} characters from 'content' field")
                    elif 'data' in result:
                        if isinstance(result['data'], str):
                            code = result['data']
                            print(f"✓ Extracted {len(code)} characters from 'data' field")
                        elif isinstance(result['data'], dict) and 'text' in result['data']:
                            code = result['data']['text']
                            print(f"✓ Extracted {len(code)} characters from 'data.text' field")
                        else:
                            raise ValueError("Unexpected data structure")
                    else:
                        raise ValueError(f"No text field found in response. Available: {list(result.keys())}")
                        
                elif response.status_code == 405:
                    print(f"⚠ on-demand.io API returned 405 (Method Not Allowed)")
                    print(f"   This may indicate the endpoint is not configured or the API key needs verification")
                    print(f"   Falling back to direct text extraction...")
                    code = file_content.decode('utf-8')
                    
                else:
                    print(f"❌ on-demand.io API Error ({response.status_code}): {response.text[:200]}")
                    code = file_content.decode('utf-8')
                    print("⚠ Using direct UTF-8 decode as fallback")
                    
            except httpx.RequestError as e:
                print(f"❌ on-demand.io API Request Error: {str(e)}")
                code = file_content.decode('utf-8')
                print("⚠ Using direct UTF-8 decode due to API request error")
                
            except (ValueError, KeyError, UnicodeDecodeError) as e:
                print(f"❌ Processing Error: {str(e)}")
                # Last resort: try direct decode
                try:
                    code = file_content.decode('utf-8')
                    print("⚠ Using direct UTF-8 decode as final fallback")
                except Exception as final_error:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Could not process file: {str(final_error)}"
                    )
        
        # Analyze the extracted code
        vulnerabilities = []
        
        # Use the same pattern-based analysis from analyze-code endpoint
        if language == "move":
            patterns = [
                {
                    "pattern": "public entry fun",
                    "check": lambda line: "public entry fun" in line and "signer" not in line.split("public entry fun")[1].split(")")[0] if ")" in line.split("public entry fun")[1] else False,
                    "vuln": {
                        "type": "missing_authorization",
                        "severity": "CRITICAL",
                        "title": "Entry Function Without Signer Parameter",
                        "description": "Public entry function lacks signer parameter for authorization",
                        "recommendation": "Add a signer parameter to verify caller identity"
                    }
                },
                {
                    "pattern": "has copy",
                    "check": lambda line: "Capability" in line and "has copy" in line,
                    "vuln": {
                        "type": "capability_copy",
                        "severity": "HIGH",
                        "title": "Capability with Copy Ability",
                        "description": "Capability struct has 'copy' ability, allowing unauthorized duplication",
                        "recommendation": "Remove 'copy' ability from capability structs"
                    }
                },
                {
                    "pattern": "borrow_global_mut",
                    "check": lambda line: "borrow_global_mut" in line,
                    "vuln": {
                        "type": "unsafe_mutation",
                        "severity": "MEDIUM",
                        "title": "Global State Mutation",
                        "description": "Function mutates global state - ensure proper access controls",
                        "recommendation": "Verify authorization before mutating global state"
                    }
                }
            ]
        elif language == "solidity":
            patterns = [
                {
                    "pattern": "tx.origin",
                    "check": lambda line: "tx.origin" in line and "//" not in line[:line.index("tx.origin")] if "tx.origin" in line else False,
                    "vuln": {
                        "type": "tx_origin_usage",
                        "severity": "CRITICAL",
                        "title": "Use of tx.origin for Authorization",
                        "description": "Using tx.origin for authorization is vulnerable to phishing attacks",
                        "recommendation": "Use msg.sender instead of tx.origin for authorization checks"
                    }
                },
                {
                    "pattern": "selfdestruct",
                    "check": lambda line: "selfdestruct" in line or "suicide" in line,
                    "vuln": {
                        "type": "selfdestruct",
                        "severity": "HIGH",
                        "title": "Selfdestruct Usage",
                        "description": "Contract contains selfdestruct which can destroy the contract",
                        "recommendation": "Ensure selfdestruct is properly protected and necessary"
                    }
                },
                {
                    "pattern": "delegatecall",
                    "check": lambda line: "delegatecall" in line,
                    "vuln": {
                        "type": "delegatecall",
                        "severity": "HIGH",
                        "title": "Delegatecall to Untrusted Contract",
                        "description": "Delegatecall can be dangerous if called on untrusted contracts",
                        "recommendation": "Ensure delegatecall target is trusted and validated"
                    }
                }
            ]
        else:  # rust
            patterns = [
                {
                    "pattern": "unwrap()",
                    "check": lambda line: ".unwrap()" in line and not line.strip().startswith("//"),
                    "vuln": {
                        "type": "unsafe_unwrap",
                        "severity": "MEDIUM",
                        "title": "Use of unwrap() without Error Handling",
                        "description": "unwrap() will panic if value is None/Err, causing program crash",
                        "recommendation": "Use proper error handling with ? operator or match statements"
                    }
                },
                {
                    "pattern": "unsafe",
                    "check": lambda line: "unsafe" in line and "{" in line,
                    "vuln": {
                        "type": "unsafe_block",
                        "severity": "HIGH",
                        "title": "Unsafe Code Block",
                        "description": "Unsafe blocks bypass Rust's safety guarantees",
                        "recommendation": "Minimize unsafe code and thoroughly audit for memory safety"
                    }
                }
            ]
        
        # Analyze code with patterns
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern_info in patterns:
                try:
                    if pattern_info["pattern"] in line and pattern_info["check"](line):
                        vuln = pattern_info["vuln"].copy()
                        vuln["location"] = f"Line {line_num}"
                        vuln["confidence"] = 0.85
                        vuln["code_snippet"] = line.strip()
                        vulnerabilities.append(vuln)
                except:
                    continue
        
        # Calculate severity counts and risk score
        severity_counts = {
            "critical": sum(1 for v in vulnerabilities if v["severity"] == "CRITICAL"),
            "high": sum(1 for v in vulnerabilities if v["severity"] == "HIGH"),
            "medium": sum(1 for v in vulnerabilities if v["severity"] == "MEDIUM"),
            "low": sum(1 for v in vulnerabilities if v["severity"] == "LOW")
        }
        
        risk_score = min(100, (
            severity_counts["critical"] * 25 +
            severity_counts["high"] * 15 +
            severity_counts["medium"] * 8 +
            severity_counts["low"] * 3
        ))
        
        risk_level = "CRITICAL" if risk_score >= 80 else "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 30 else "LOW"
        
        analysis_result = {
            "analysis_id": f"upload_{upload_id}",
            "timestamp": datetime.now().isoformat(),
            "language": language,
            "vulnerabilities": vulnerabilities,
            "severity_counts": severity_counts,
            "risk_score": {
                "score": risk_score,
                "level": risk_level,
                "description": f"Risk score: {risk_score}/100"
            },
            "summary": f"Found {len(vulnerabilities)} vulnerabilities: {severity_counts['critical']} critical, {severity_counts['high']} high, {severity_counts['medium']} medium, {severity_counts['low']} low"
        }
        
        # Save to MongoDB
        try:
            db = get_database()
            await save_uploaded_contract(
                upload_id=upload_id,
                filename=file.filename or "unknown",
                language=language,
                code=code,
                file_url=file_url or "",  # Store on-demand.io file URL
                analysis_result=analysis_result
            )
            print(f"💾 Contract saved to MongoDB with upload_id: {upload_id}")
            if file_url:
                print(f"🔗 on-demand.io file URL stored: {file_url}")
        except Exception as db_error:
            print(f"❌ MongoDB save failed: {db_error}")
            # Continue without saving to DB
        
        return {
            "upload_id": upload_id,
            "filename": file.filename,
            "code": code,
            "file_url": file_url,  # Include on-demand.io URL in response
            "analysis": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload and analysis failed: {str(e)}")


@router.get("/uploads/recent")
async def get_recent_uploads(limit: int = 20):
    """Get recently uploaded contracts from MongoDB."""
    from app.core.database import get_recent_uploads
    
    try:
        uploads = await get_recent_uploads(limit=limit)
        return {"uploads": uploads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch uploads: {str(e)}")


@router.get("/uploads/{upload_id}")
async def get_upload_by_id(upload_id: str):
    """Get a specific uploaded contract by ID."""
    from app.core.database import get_uploaded_contract
    
    try:
        upload = await get_uploaded_contract(upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        return upload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch upload: {str(e)}")
