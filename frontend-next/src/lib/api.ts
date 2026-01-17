const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export interface Vulnerability {
    type: string;
    severity: string;
    title: string;
    description: string;
    location: string;
    recommendation: string;
    confidence: number;
}

export interface VulnerabilityReport {
    module_address: string;
    module_name: string;
    vulnerabilities: Vulnerability[];
    summary: string;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
}

export interface RiskScore {
    score: number;
    level: string;
    breakdown: Record<string, number>;
    factors: string[];
    recommendations: string[];
}

export interface DemoContractAnalysis {
    contract_name: string;
    address: string;
    description: string;
    vulnerabilities: VulnerabilityReport;
    risk_score: RiskScore;
    source_code?: string;
}

export interface DemoContract {
    name: string;
    address: string;
    description: string;
    vulnerability_count: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
}

export async function getDemoContracts(): Promise<{ contracts: DemoContract[]; total_vulnerabilities: number }> {
    const res = await fetch(`${API_BASE}/api/demo/contracts`);
    if (!res.ok) throw new Error('Failed to fetch demo contracts');
    return res.json();
}

export async function analyzeDemoContract(contractName: string): Promise<DemoContractAnalysis> {
    const res = await fetch(`${API_BASE}/api/demo/contracts/${contractName}/analyze`);
    if (!res.ok) throw new Error('Failed to analyze contract');
    return res.json();
}

export async function analyzeContract(
    address: string,
    moduleName?: string,
    includeAI: boolean = false
): Promise<any> {
    const res = await fetch(`${API_BASE}/api/contracts/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            address,
            module_name: moduleName || null,
            include_ai_analysis: includeAI
        })
    });
    if (!res.ok) throw new Error('Failed to analyze contract');
    return res.json();
}

export async function getHealth(): Promise<{
    status: string;
    version: string;
    aptos_network: string;
    ai_enabled: boolean;
}> {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
}
