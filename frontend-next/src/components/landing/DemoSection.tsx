'use client';

import { useState } from 'react';
import Link from 'next/link';
import { analyzeDemoContract, type DemoContractAnalysis } from '@/lib/api';

const demoContracts = [
    { name: 'vulnerable_token', displayName: 'vulnerable_token.move', description: 'Token with critical flaws', score: 91, level: 'critical' },
    { name: 'insecure_dex', displayName: 'insecure_dex.move', description: 'DEX with drain vulnerability', score: 98, level: 'critical' },
    { name: 'risky_nft', displayName: 'risky_nft.move', description: 'NFT theft vulnerability', score: 80, level: 'high' },
];

const getIcon = (name: string) => {
    if (name === 'vulnerable_token') return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6m0-6l6 6"/></svg>;
    if (name === 'insecure_dex') return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>;
    if (name === 'risky_nft') return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>;
    return null;
};

export function DemoSection() {
    const [selected, setSelected] = useState<string | null>(null);
    const [analysis, setAnalysis] = useState<DemoContractAnalysis | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSelect = async (name: string) => {
        setSelected(name); setLoading(true); setError(null);
        try { setAnalysis(await analyzeDemoContract(name)); } 
        catch (e) { setError('Failed to analyze. Make sure the backend is running on port 8000.'); } 
        finally { setLoading(false); }
    };

    const getLevelColor = (level: string) => ({critical: '#ef4444', high: '#f97316', medium: '#f59e0b'}[level] || '#10b981');

    return (
        <section id="demo" className="section demo-section">
            <div className="section-container">
                <div className="section-header">
                    <span className="section-badge">Live Demo</span>
                    <h2 className="section-title">See It In Action</h2>
                    <p className="section-subtitle">Click any vulnerable contract to see the agent detect security flaws</p>
                </div>
                <div className="demo-grid">
                    <div className="demo-contracts">
                        {demoContracts.map((contract) => (
                            <button key={contract.name} onClick={() => handleSelect(contract.name)} className={`contract-card ${selected === contract.name ? 'selected' : ''} ${contract.level}`}>
                                <div className="contract-info">
                                    <div className={`contract-icon ${contract.level}`}>{getIcon(contract.name)}</div>
                                    <div><div className="contract-name">{contract.displayName}</div><div className="contract-desc">{contract.description}</div></div>
                                </div>
                                <div className="contract-score"><div className={`score-value ${contract.level}`}>{contract.score}</div><div className={`score-label ${contract.level}`}>{contract.level}</div></div>
                            </button>
                        ))}
                    </div>
                    <div className="demo-results">
                        {loading ? (<div className="demo-loading"><div className="spinner"></div><p>Analyzing contract...</p></div>) 
                        : error ? (<div className="demo-error"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6m0-6l6 6"/></svg><p>{error}</p></div>) 
                        : analysis ? (<div className="demo-analysis"><div className="analysis-header"><div className="risk-display"><div className="risk-score" style={{ color: getLevelColor(analysis.risk_score.level) }}>{analysis.risk_score.score}</div><div className="risk-info"><div className="risk-level" style={{ color: getLevelColor(analysis.risk_score.level) }}>{analysis.risk_score.level} Risk</div><div className="contract-title">{analysis.contract_name}.move</div></div></div></div><div className="vuln-badges"><span className="badge critical">{analysis.vulnerabilities.critical_count} Critical</span><span className="badge high">{analysis.vulnerabilities.high_count} High</span><span className="badge medium">{analysis.vulnerabilities.medium_count} Medium</span></div><div className="vuln-list">{analysis.vulnerabilities.vulnerabilities.slice(0, 4).map((vuln, i) => (<div key={i} className={`vuln-item ${vuln.severity}`}><div className="vuln-title">{vuln.title}</div><div className="vuln-desc">{vuln.description}</div></div>))}</div><div className="analysis-footer"><Link href="/dashboard" className="btn btn-primary">Open Full Dashboard<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg></Link></div></div>) 
                        : (<div className="demo-empty"><svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" opacity="0.3"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><p>Select a contract to analyze</p></div>)}
                    </div>
                </div>
            </div>
        </section>
    );
}
