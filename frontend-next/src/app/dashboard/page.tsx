'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { Navbar } from '@/components/ui/Navbar';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './dashboard.css';

// When served from same origin, use relative URLs
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';
const WS_URL = typeof window !== 'undefined'
  ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`
  : '';

interface Stats {
  safe: number;
  warnings: number;
  alerts: number;
  total: number;
}

interface Alert {
  risk_level: string;
  risk_score: number;
  violations: Array<{ message: string }>;
  transaction_hash: string;
  timestamp: string;
  sender: string;
}

interface Transaction {
  transaction_hash: string;
  timestamp: string;
  success: boolean;
}

interface Policy {
  name: string;
  policy_type: string;
  severity: string;
  enabled: boolean;
}

type ChainType = 'aptos' | 'ethereum' | 'solana';

interface ChainConfig {
  id: ChainType;
  name: string;
  network: string;
  icon: string;
  explorerUrl: (hash: string) => string;
  color: string;
}

const CHAIN_CONFIGS: Record<ChainType, ChainConfig> = {
  aptos: {
    id: 'aptos',
    name: 'Aptos',
    network: 'Testnet',
    icon: '⬥',
    explorerUrl: (hash) => `https://explorer.aptoslabs.com/txn/${hash}?network=testnet`,
    color: '#00D4AA'
  },
  ethereum: {
    id: 'ethereum',
    name: 'Ethereum',
    network: 'Sepolia',
    icon: '◆',
    explorerUrl: (hash) => `https://sepolia.etherscan.io/tx/${hash}`,
    color: '#627EEA'
  },
  solana: {
    id: 'solana',
    name: 'Solana',
    network: 'Devnet',
    icon: '◉',
    explorerUrl: (hash) => `https://explorer.solana.com/tx/${hash}?cluster=devnet`,
    color: '#14F195'
  }
};

export default function DashboardPage() {
  const [connected, setConnected] = useState(false);
  const [selectedChain, setSelectedChain] = useState<ChainType>('aptos');
  const [stats, setStats] = useState<Stats>({ safe: 0, warnings: 0, alerts: 0, total: 0 });
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [networkName, setNetworkName] = useState('testnet');
  const [transactionHash, setTransactionHash] = useState('');
  const [includeAI, setIncludeAI] = useState(true);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [demoModal, setDemoModal] = useState<{ open: boolean, data: any }>({ open: false, data: null });
  const [viewModal, setViewModal] = useState<{ open: boolean, type: 'transaction' | 'alert' | null, data: any }>({ open: false, type: null, data: null });
  const [activityData, setActivityData] = useState<Array<{ time: string, transactions: number }>>([]);
  const [currentIntervalCount, setCurrentIntervalCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const activityIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Copy to clipboard helper
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      // Could add a toast notification here
    }).catch(err => console.error('Copy failed:', err));
  };

  // Get explorer URL based on selected chain
  const getExplorerUrl = (hash: string) => {
    return CHAIN_CONFIGS[selectedChain].explorerUrl(hash);
  };

  // Handle chain change
  const handleChainChange = (chain: ChainType) => {
    setSelectedChain(chain);
    // Reset stats and data when changing chains
    setStats({ safe: 0, warnings: 0, alerts: 0, total: 0 });
    setAlerts([]);
    setTransactions([]);
    setAnalysisResult(null);
    setActivityData([]);
    setCurrentIntervalCount(0);
  };

  // Transaction activity tracking - tick every 2 seconds
  useEffect(() => {
    activityIntervalRef.current = setInterval(() => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

      setCurrentIntervalCount(count => {
        console.log(`[Chart Tick] Time: ${timeStr}, Transactions: ${count}`);

        // Add data point with current count
        setActivityData(prev => {
          const newData = [...prev, { time: timeStr, transactions: count }];
          return newData.slice(-60); // Keep last 60 points (2 minutes)
        });

        // Reset counter for next interval
        return 0;
      });
    }, 2000);

    return () => {
      if (activityIntervalRef.current) {
        clearInterval(activityIntervalRef.current);
      }
    };
  }, []);

  // WebSocket connection
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const connectWS = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
      };

      ws.onclose = () => {
        setConnected(false);
        setTimeout(connectWS, 3000);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };
    };

    connectWS();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'transaction_alert':
        if (message.risk_level === 'critical' || message.risk_level === 'high') {
          setStats(prev => ({ ...prev, alerts: prev.alerts + 1 }));
        } else {
          setStats(prev => ({ ...prev, warnings: prev.warnings + 1 }));
        }
        setAlerts(prev => [message, ...prev].slice(0, 50));
        break;
      case 'new_transaction':
        setStats(prev => ({
          ...prev,
          total: prev.total + 1,
          safe: message.success ? prev.safe + 1 : prev.safe
        }));
        setTransactions(prev => [message, ...prev].slice(0, 20));
        setCurrentIntervalCount(prev => {
          const newCount = prev + 1;
          console.log(`[Transaction Received] Counter: ${newCount}, Hash: ${message.hash?.substring(0, 10)}...`);
          return newCount;
        });
        break;
      case 'ping':
        if (wsRef.current) wsRef.current.send(JSON.stringify({ type: 'pong' }));
        break;
    }
  };

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        const [policiesRes, healthRes] = await Promise.all([
          fetch(`${API_BASE}/api/compliance/policies`),
          fetch(`${API_BASE}/api/health`)
        ]);

        if (policiesRes.ok) {
          setPolicies(await policiesRes.json());
        }
        if (healthRes.ok) {
          const health = await healthRes.json();
          setNetworkName(health.aptos_network);
        }
      } catch (e) {
        console.error('Failed to load data:', e);
      }
    };

    loadData();
  }, []);

  const analyzeTransaction = async () => {
    setLoading(true);
    setAnalysisResult(null);

    try {
      const response = await fetch(`${API_BASE}/api/transactions/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hash: transactionHash,
          include_ai_analysis: includeAI
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Analysis failed' }));
        throw new Error(errorData.detail || 'Analysis failed');
      }
      const results = await response.json();
      setAnalysisResult(results);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Analysis failed. Make sure the backend is running and provide a valid transaction hash.';
      console.error('Analysis error:', error);
      setAnalysisResult({
        error: true,
        message: errorMsg
      });
    } finally {
      setLoading(false);
    }
  };

  const analyzeDemo = async (contractName: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/demo/contracts/${contractName}/analyze`);
      if (!response.ok) throw new Error('Failed');
      const results = await response.json();
      setDemoModal({ open: true, data: results });
    } catch (error) {
      alert('Failed to analyze demo contract');
    }
  };

  const togglePolicy = async (name: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/compliance/policies/${name}/toggle`, { method: 'PUT' });
      if (response.ok) {
        const result = await response.json();
        setPolicies(prev => prev.map(p => p.name === name ? { ...p, enabled: result.enabled } : p));
      }
    } catch (e) {
      console.error('Failed to toggle policy:', e);
    }
  };

  return (
    <div className="app-container">
      {/* Unified Navigation */}
      <Navbar />

      {/* Connection Status Bar with Chain Selector */}
      <div className="connection-bar">
        <div className="chain-selector-wrapper">
          <span className="selector-label">Monitoring:</span>
          <div className="chain-selector">
            {(Object.keys(CHAIN_CONFIGS) as ChainType[]).map((chain) => {
              const config = CHAIN_CONFIGS[chain];
              return (
                <button
                  key={chain}
                  className={`chain-btn ${selectedChain === chain ? 'active' : ''}`}
                  onClick={() => handleChainChange(chain)}
                  style={{ '--chain-color': config.color } as React.CSSProperties}
                >
                  <span className="chain-icon">{config.icon}</span>
                  <span className="chain-info">
                    <span className="chain-name">{config.name}</span>
                    <span className="chain-network">{config.network}</span>
                  </span>
                </button>
              );
            })}
          </div>
        </div>
        <div className="connection-status">
          <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`}></span>
          <span className="status-text">
            {connected ? `Connected to ${CHAIN_CONFIGS[selectedChain].name} ${CHAIN_CONFIGS[selectedChain].network}` : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Main Content */}
      <main className="main-content">
        {/* Stats Row */}
        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-icon safe">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <div className="stat-info">
              <span className="stat-value">{stats.safe}</span>
              <span className="stat-label">Safe Transactions</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon warning">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <div className="stat-info">
              <span className="stat-value">{stats.warnings}</span>
              <span className="stat-label">Warnings</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon danger">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
            </div>
            <div className="stat-info">
              <span className="stat-value">{stats.alerts}</span>
              <span className="stat-label">Alerts</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon info">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <div className="stat-info">
              <span className="stat-value">{stats.total}</span>
              <span className="stat-label">Total Monitored</span>
            </div>
          </div>
        </div>

        {/* Transaction Activity Chart */}
        <section className="activity-chart-panel">
          <div className="panel-header">
            <div>
              <h2>Transaction Activity</h2>
              <span className="activity-subtitle">Real-time transactions per 2 seconds • Last 2 minutes</span>
            </div>
            <div className="activity-stats">
              <span className="activity-stat">
                <span className="stat-label-small">Current Chain:</span>
                <span className="stat-value-small" style={{ color: CHAIN_CONFIGS[selectedChain].color }}>
                  {CHAIN_CONFIGS[selectedChain].name}
                </span>
              </span>
            </div>
          </div>
          <div className="chart-container">
            {activityData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={activityData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99, 102, 241, 0.1)" />
                  <XAxis
                    dataKey="time"
                    stroke="rgba(255, 255, 255, 0.5)"
                    tick={{ fill: 'rgba(255, 255, 255, 0.6)', fontSize: 11 }}
                  />
                  <YAxis
                    stroke="rgba(255, 255, 255, 0.5)"
                    tick={{ fill: 'rgba(255, 255, 255, 0.6)', fontSize: 11 }}
                    allowDecimals={false}
                    domain={[0, 'auto']}
                  />
                  <Tooltip
                    contentStyle={{
                      background: 'rgba(20, 20, 35, 0.95)',
                      border: '1px solid rgba(99, 102, 241, 0.3)',
                      borderRadius: '8px',
                      color: 'white'
                    }}
                    labelStyle={{ color: 'rgba(255, 255, 255, 0.8)' }}
                    cursor={{ fill: 'rgba(99, 102, 241, 0.1)' }}
                  />
                  <Bar
                    dataKey="transactions"
                    fill={CHAIN_CONFIGS[selectedChain].color}
                    radius={[4, 4, 0, 0]}
                    opacity={0.8}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '200px',
                color: 'rgba(255, 255, 255, 0.5)',
                fontSize: '14px'
              }}>
                Waiting for transactions...
              </div>
            )}
          </div>
        </section>

        {/* Main Grid */}
        <div className="main-grid">
          {/* Transaction Analysis Panel */}
          <section className="panel contract-panel">
            <div className="panel-header">
              <h2>Transaction Analysis</h2>
              <span className="panel-badge">AI-Powered</span>
            </div>
            <div className="panel-content">
              <form className="analyze-form" onSubmit={(e) => { e.preventDefault(); analyzeTransaction(); }}>
                <div className="form-group">
                  <label htmlFor="transactionHash">Transaction Hash</label>
                  <input
                    type="text"
                    id="transactionHash"
                    placeholder="Enter transaction hash (0x...)..."
                    value={transactionHash}
                    onChange={(e) => setTransactionHash(e.target.value)}
                  />
                  <small className="form-help">
                    Paste a transaction hash from the explorer or recent transactions below
                  </small>
                </div>
                <div className="form-check">
                  <input
                    type="checkbox"
                    id="includeAI"
                    checked={includeAI}
                    onChange={(e) => setIncludeAI(e.target.checked)}
                  />
                  <label htmlFor="includeAI">Include AI Analysis</label>
                </div>
                <button type="submit" className={`btn btn-primary ${loading ? 'loading' : ''}`} disabled={loading || !transactionHash.trim()}>
                  <span className="btn-text">Analyze Transaction</span>
                  <span className="btn-loader"></span>
                </button>
              </form>

              {/* Analysis Results */}
              {analysisResult && (
                <div className="analysis-results">
                  {analysisResult.error ? (
                    <div className="error-message">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                      </svg>
                      <div>
                        <strong>Error:</strong> {analysisResult.message}
                      </div>
                    </div>
                  ) : (
                    <>
                      {/* Transaction Info Header */}
                      <div className="module-info">
                        <div className="module-address">
                          <strong>Transaction Hash:</strong> <code>{analysisResult.transaction?.hash}</code>
                        </div>
                        <div className="module-name">
                          <strong>Sender:</strong> <code>{analysisResult.transaction?.sender}</code>
                        </div>
                        <div className="module-name">
                          <strong>Status:</strong> <span className={analysisResult.transaction?.success ? 'text-green-400' : 'text-red-400'}>{analysisResult.transaction?.success ? '✓ Success' : '✗ Failed'}</span>
                          {' | '}
                          <strong>Gas:</strong> {analysisResult.transaction?.gas_used}
                          {' | '}
                          <strong>Type:</strong> {analysisResult.transaction?.type}
                        </div>
                      </div>

                      <div className="risk-score-display">
                        <div className="risk-circle">
                          <svg viewBox="0 0 100 100">
                            <circle className="risk-bg" cx="50" cy="50" r="45" />
                            <circle
                              className={`risk-progress ${analysisResult.risk_score.level}`}
                              cx="50"
                              cy="50"
                              r="45"
                              style={{
                                strokeDashoffset: 283 - (analysisResult.risk_score.score / 100) * 283
                              }}
                            />
                          </svg>
                          <div className="risk-value">
                            <span>{analysisResult.risk_score.score}</span>
                            <span className="risk-label">Risk Score</span>
                          </div>
                        </div>
                        <div className={`risk-level ${analysisResult.risk_score.level}`}>
                          {analysisResult.risk_score.level.toUpperCase()}
                        </div>
                      </div>

                      {/* Compliance Results */}
                      {analysisResult.compliance && (
                        <>
                          <div className="vuln-summary">
                            <span className={`vuln-badge ${analysisResult.compliance.passed ? 'low' : 'critical'}`}>
                              {analysisResult.compliance.passed ? '✓ Compliant' : '✗ Non-Compliant'}
                            </span>
                            <span className="vuln-badge info">
                              {analysisResult.compliance.policies_checked} Policies Checked
                            </span>
                          </div>

                          {analysisResult.compliance.violations && analysisResult.compliance.violations.length > 0 && (
                            <div className="vuln-list">
                              <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>Policy Violations</h4>
                              {analysisResult.compliance.violations.map((v: any, i: number) => (
                                <div key={i} className={`vuln-item ${v.severity.toLowerCase()}`}>
                                  <div className="vuln-item-header">
                                    <div className="vuln-item-title">{v.policy_name.replace(/_/g, ' ')}</div>
                                    <span className={`vuln-severity-badge ${v.severity.toLowerCase()}`}>{v.severity}</span>
                                  </div>
                                  <div className="vuln-item-desc">{v.message}</div>
                                  <div className="vuln-item-location">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                      <polyline points="14 2 14 8 20 8" />
                                    </svg>
                                    Policy Type: {v.policy_type}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          {analysisResult.compliance.passed && (
                            <div className="empty-state">
                              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                                <polyline points="22 4 12 14.01 9 11.01" />
                              </svg>
                              <p>All Policies Passed</p>
                              <span>This transaction complies with all active policies</span>
                            </div>
                          )}
                        </>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          </section>

          {/* Real-time Alerts Panel */}
          <section className="panel alerts-panel">
            <div className="panel-header">
              <h2>Real-time Alerts</h2>
              <button className="btn btn-small" onClick={() => setAlerts([])}>Clear</button>
            </div>
            <div className="panel-content">
              <div className="alerts-list">
                {alerts.length === 0 ? (
                  <div className="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                    </svg>
                    <p>No alerts yet</p>
                    <span>Monitoring for suspicious activity...</span>
                  </div>
                ) : (
                  alerts.map((alert, i) => (
                    <div key={i} className={`alert-item ${alert.risk_level}`}>
                      <div className="alert-header">
                        <div className="alert-title-group">
                          <span className={`alert-badge ${alert.risk_level}`}>{alert.risk_level.toUpperCase()}</span>
                          <span className="alert-score">Risk: {alert.risk_score}</span>
                        </div>
                        <span className="alert-time">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="alert-message">
                        {alert.violations.length > 0
                          ? alert.violations.map(v => v.message).join(', ')
                          : `Transaction from ${alert.sender.slice(0, 8)}...`}
                      </div>
                      <div className="alert-tx-row">
                        <div className="tx-hash-display">
                          <span className="tx-label">Transaction Hash:</span>
                          <a
                            href={getExplorerUrl(alert.transaction_hash)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="tx-hash-link"
                          >
                            {alert.transaction_hash.slice(0, 8)}...{alert.transaction_hash.slice(-8)}
                          </a>
                          <button
                            className="copy-btn"
                            onClick={() => copyToClipboard(alert.transaction_hash)}
                            title="Copy transaction hash"
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                            </svg>
                          </button>
                        </div>
                        <div className="sender-address">
                          <span className="sender-label">From:</span>
                          <code className="address-code">{alert.sender.slice(0, 6)}...{alert.sender.slice(-4)}</code>
                        </div>
                      </div>
                      <button
                        className="view-details-btn"
                        onClick={() => setViewModal({ open: true, type: 'alert', data: alert })}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                          <circle cx="12" cy="12" r="3" />
                        </svg>
                        View Details
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </section>

          {/* Transaction Monitor Panel */}
          <section className="panel monitor-panel">
            <div className="panel-header">
              <h2>Transaction Monitor</h2>
            </div>
            <div className="panel-content">
              <div className="monitored-addresses">
                <span className="label">Monitored:</span>
                <span className="address-tag">All Transactions</span>
              </div>
              <div className="transactions-list">
                {transactions.length === 0 ? (
                  <div className="empty-state small">
                    <p>Waiting for transactions...</p>
                  </div>
                ) : (
                  transactions.map((tx, i) => (
                    <div key={i} className="tx-item">
                      <div className="tx-status-icon">
                        <div className={`tx-status-badge ${tx.success ? 'success' : 'failed'}`}>
                          {tx.success ? (
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                          ) : (
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                              <line x1="18" y1="6" x2="6" y2="18" />
                              <line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                          )}
                        </div>
                      </div>
                      <div className="tx-details">
                        <div className="tx-hash-row">
                          <span className="tx-label">Txn Hash:</span>
                          <a
                            href={getExplorerUrl(tx.transaction_hash)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="tx-hash-link"
                          >
                            {tx.transaction_hash.slice(0, 10)}...{tx.transaction_hash.slice(-8)}
                          </a>
                          <button
                            className="copy-btn-small"
                            onClick={() => copyToClipboard(tx.transaction_hash)}
                            title="Copy transaction hash"
                          >
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                            </svg>
                          </button>
                        </div>
                        <div className="tx-meta">
                          <span className="tx-time">
                            {new Date(tx.timestamp).toLocaleTimeString()}
                          </span>
                          <span className={`tx-status-text ${tx.success ? 'success' : 'failed'}`}>
                            {tx.success ? 'Success' : 'Failed'}
                          </span>
                          <button
                            className="view-details-btn-inline"
                            onClick={() => {
                              setTransactionHash(tx.transaction_hash);
                              window.scrollTo({ top: 0, behavior: 'smooth' });
                            }}
                            title="Analyze this transaction"
                          >
                            Analyze
                          </button>
                          <button
                            className="view-details-btn-inline"
                            onClick={() => setViewModal({ open: true, type: 'transaction', data: tx })}
                          >
                            View
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </section>

          {/* Compliance Policies Panel */}
          <section className="panel policies-panel">
            <div className="panel-header">
              <h2>Active Policies</h2>
              <span className="panel-badge">
                {policies.filter(p => p.enabled).length} active
              </span>
            </div>
            <div className="panel-content">
              <div className="policies-list">
                {policies.map((policy, i) => (
                  <div key={i} className="policy-item">
                    <div className="policy-info">
                      <span className="policy-name">
                        {policy.name.replace(/_/g, ' ')}
                      </span>
                      <span className="policy-type">
                        {policy.policy_type} | {policy.severity}
                      </span>
                    </div>
                    <div
                      className={`policy-toggle ${policy.enabled ? 'active' : ''}`}
                      onClick={() => togglePolicy(policy.name)}
                    ></div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>

        {/* Demo Contracts Showcase */}
        <section className="demo-showcase">
          <div className="demo-header">
            <h2>🎯 Demo: Vulnerable Smart Contracts</h2>
            <p>Click on any contract below to see the compliance agent detect intentional vulnerabilities</p>
          </div>
          <div className="demo-cards">
            <div className="demo-card" onClick={() => analyzeDemo('vulnerable_token')}>
              <div className="demo-card-icon danger">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M16 8l-8 8M8 8l8 8" />
                </svg>
              </div>
              <h3>Vulnerable Token</h3>
              <p>Token with missing signer verification and copy capability leaks</p>
              <div className="demo-stats">
                <span className="demo-badge critical">3 Critical</span>
                <span className="demo-badge high">2 High</span>
              </div>
            </div>
            <div className="demo-card" onClick={() => analyzeDemo('insecure_dex')}>
              <div className="demo-card-icon warning">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
              </div>
              <h3>Insecure DEX</h3>
              <p>DEX with excessive friends and unprotected swap/drain functions</p>
              <div className="demo-stats">
                <span className="demo-badge critical">3 Critical</span>
                <span className="demo-badge medium">1 Medium</span>
              </div>
            </div>
            <div className="demo-card" onClick={() => analyzeDemo('risky_nft')}>
              <div className="demo-card-icon danger">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <polyline points="21 15 16 10 5 21" />
                </svg>
              </div>
              <h3>Risky NFT</h3>
              <p>NFT contract with unauthorized transfers and metadata manipulation</p>
              <div className="demo-stats">
                <span className="demo-badge critical">2 Critical</span>
                <span className="demo-badge high">2 High</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>Aptos Compliance Agent v0.1.0 | Connected to <span>{networkName}</span></p>
      </footer>

      {/* View Details Modal */}
      {viewModal.open && viewModal.data && (
        <div className="modal open" onClick={() => setViewModal({ open: false, type: null, data: null })}>
          <div className="modal-content view-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{viewModal.type === 'transaction' ? 'Transaction Details' : 'Alert Details'}</h2>
              <button className="modal-close" onClick={() => setViewModal({ open: false, type: null, data: null })}>
                &times;
              </button>
            </div>
            <div className="modal-body">
              {viewModal.type === 'transaction' && (
                <div className="detail-view">
                  <div className="detail-row">
                    <span className="detail-label">Transaction Hash:</span>
                    <div className="detail-value-group">
                      <code className="detail-hash">{viewModal.data.transaction_hash || viewModal.data.hash}</code>
                      <button className="copy-btn-small" onClick={() => copyToClipboard(viewModal.data.transaction_hash || viewModal.data.hash)}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                        </svg>
                      </button>
                      <a
                        href={getExplorerUrl(viewModal.data.transaction_hash || viewModal.data.hash)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="explorer-link-btn"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                          <polyline points="15 3 21 3 21 9" />
                          <line x1="10" y1="14" x2="21" y2="3" />
                        </svg>
                        View in Explorer
                      </a>
                    </div>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Status:</span>
                    <span className={`detail-status ${viewModal.data.success ? 'success' : 'failed'}`}>
                      {viewModal.data.success ? '✓ Success' : '✗ Failed'}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Timestamp:</span>
                    <span className="detail-value">{new Date(viewModal.data.timestamp).toLocaleString()}</span>
                  </div>
                  {viewModal.data.sender && (
                    <div className="detail-row">
                      <span className="detail-label">Sender:</span>
                      <div className="detail-value-group">
                        <code className="detail-address">{viewModal.data.sender}</code>
                        <button className="copy-btn-small" onClick={() => copyToClipboard(viewModal.data.sender)}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  )}
                  {viewModal.data.type && (
                    <div className="detail-row">
                      <span className="detail-label">Type:</span>
                      <span className="detail-value">{viewModal.data.type}</span>
                    </div>
                  )}
                  {viewModal.data.riskScore !== undefined && (
                    <div className="detail-row">
                      <span className="detail-label">Risk Score:</span>
                      <span className={`detail-risk-score ${viewModal.data.riskScore >= 70 ? 'high' : viewModal.data.riskScore >= 40 ? 'medium' : 'low'}`}>
                        {viewModal.data.riskScore}
                      </span>
                    </div>
                  )}
                </div>
              )}
              {viewModal.type === 'alert' && (
                <div className="detail-view">
                  <div className="detail-row">
                    <span className="detail-label">Alert Type:</span>
                    <span className={`alert-badge ${viewModal.data.severity.toLowerCase()}`}>
                      {viewModal.data.severity}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Risk Score:</span>
                    <span className={`detail-risk-score ${viewModal.data.risk_score >= 70 ? 'high' : viewModal.data.risk_score >= 40 ? 'medium' : 'low'}`}>
                      {viewModal.data.risk_score}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Description:</span>
                    <span className="detail-value">{viewModal.data.message}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Transaction Hash:</span>
                    <div className="detail-value-group">
                      <code className="detail-hash">{viewModal.data.transaction_hash}</code>
                      <button className="copy-btn-small" onClick={() => copyToClipboard(viewModal.data.transaction_hash)}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                        </svg>
                      </button>
                      <a
                        href={getExplorerUrl(viewModal.data.transaction_hash)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="explorer-link-btn"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                          <polyline points="15 3 21 3 21 9" />
                          <line x1="10" y1="14" x2="21" y2="3" />
                        </svg>
                        View in Explorer
                      </a>
                    </div>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Sender Address:</span>
                    <div className="detail-value-group">
                      <code className="detail-address">{viewModal.data.sender}</code>
                      <button className="copy-btn-small" onClick={() => copyToClipboard(viewModal.data.sender)}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Timestamp:</span>
                    <span className="detail-value">{new Date(viewModal.data.timestamp).toLocaleString()}</span>
                  </div>
                  {viewModal.data.details && (
                    <div className="detail-row">
                      <span className="detail-label">Additional Details:</span>
                      <pre className="detail-json">{JSON.stringify(viewModal.data.details, null, 2)}</pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Demo Modal */}
      {demoModal.open && demoModal.data && (
        <div className="modal open" onClick={() => setDemoModal({ open: false, data: null })}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Analysis: {demoModal.data.contract_name.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}</h2>
              <button className="modal-close" onClick={() => setDemoModal({ open: false, data: null })}>
                &times;
              </button>
            </div>
            <div className="modal-body">
              <div className="modal-risk-display">
                <div className={`modal-risk-score ${demoModal.data.risk_score.level}`}>
                  {demoModal.data.risk_score.score}
                </div>
                <div className="modal-risk-info">
                  <h3>{demoModal.data.risk_score.level.toUpperCase()} RISK</h3>
                  <p className="modal-risk-level">{demoModal.data.description}</p>
                </div>
              </div>

              <div className="vuln-summary" style={{ marginBottom: '1rem' }}>
                <span className="vuln-badge critical">
                  {demoModal.data.vulnerabilities.critical_count} Critical
                </span>
                <span className="vuln-badge high">
                  {demoModal.data.vulnerabilities.high_count} High
                </span>
                <span className="vuln-badge medium">
                  {demoModal.data.vulnerabilities.medium_count} Medium
                </span>
                <span className="vuln-badge low">
                  {demoModal.data.vulnerabilities.low_count} Low
                </span>
              </div>

              <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>Vulnerabilities Detected</h3>
              <div className="modal-vuln-list">
                {demoModal.data.vulnerabilities.vulnerabilities.map((v: any, i: number) => (
                  <div key={i} className={`modal-vuln-item ${v.severity}`}>
                    <div className="modal-vuln-header">
                      <span className="modal-vuln-title">{v.title}</span>
                      <span className={`modal-vuln-severity ${v.severity}`}>{v.severity}</span>
                    </div>
                    <div className="modal-vuln-desc">{v.description}</div>
                    <span className="modal-vuln-location">📍 {v.location}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
