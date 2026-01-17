'use client';

import { useState } from 'react';
import Navbar from '@/components/ui/Navbar';
import './workflows.css';

// When served from same origin, use relative URLs
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

// Workflow definitions - Built in On-Demand.io platform
const WORKFLOWS = [
  {
    id: '696abab2c28c63108ddb7dbe',
    key: 'solana_trading_bot',
    name: '🤖 Solana Trading Bot',
    tagline: 'Automated token analysis & swapping',
    description: 'AI-powered Solana trading bot that analyzes tokens using DEX data, performs RSI/MACD technical analysis, and executes swaps on Raydium. Workflow is pre-configured in the On-Demand.io platform.',
    icon: '🤖',
    gradient: 'linear-gradient(135deg, #14F195 0%, #9945FF 50%, #14F195 100%)',
    accentColor: '#14F195',
    steps: [
      { agent: 'Solscan Wallet Checker', task: 'Check wallet for existing tokens', icon: '👛' },
      { agent: 'Token Filter', task: 'Filter by liquidity, FDV, volume', icon: '🔍' },
      { agent: 'Technical Analyzer', task: 'Calculate RSI & MACD signals', icon: '📊' },
      { agent: 'Token Selector', task: 'Select top 2 tokens', icon: '🎯' },
      { agent: 'Raydium Swapper', task: 'Execute multi-token swaps', icon: '⚡' }
    ]
  }
];

interface WorkflowResult {
  success: boolean;
  workflow_id: string;
  execution_id?: string;
  status?: string;
  message?: string;
  execution_time: string;
  error?: string;
}

export default function WorkflowsPage() {
  const [selectedWorkflow, setSelectedWorkflow] = useState(WORKFLOWS[0]);
  const [loading, setLoading] = useState(false);
  const [actionType, setActionType] = useState<'activate' | 'execute' | null>(null);
  const [currentStep, setCurrentStep] = useState(-1);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const activateWorkflow = async () => {
    setLoading(true);
    setActionType('activate');
    setError(null);
    setResult(null);
    setCurrentStep(0);

    // Simulate step progression for visual feedback
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < selectedWorkflow.steps.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 2000);

    try {
      // Activate workflow - prepares it to run
      const response = await fetch(`${API_BASE}/api/workflows/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: selectedWorkflow.id
        })
      });

      clearInterval(stepInterval);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Workflow activation failed');
      }

      const data = await response.json();
      setResult(data);
      setCurrentStep(selectedWorkflow.steps.length);
    } catch (err: any) {
      setError(err.message || 'Failed to activate workflow');
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  };

  const executeWorkflow = async () => {
    setLoading(true);
    setActionType('execute');
    setError(null);
    setResult(null);
    setCurrentStep(0);

    // Simulate step progression for visual feedback
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < selectedWorkflow.steps.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 2000);

    try {
      // Execute workflow - runs it immediately
      const response = await fetch(`${API_BASE}/api/workflows/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: selectedWorkflow.id
        })
      });

      clearInterval(stepInterval);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Workflow execution failed');
      }

      const data = await response.json();
      setResult(data);
      setCurrentStep(selectedWorkflow.steps.length);
    } catch (err: any) {
      setError(err.message || 'Failed to execute workflow');
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  };

  return (
    <div className="workflows-page">
      <Navbar />

      {/* Background Effects */}
      <div className="workflows-bg">
        <div className="gradient-orb orb-1" style={{ background: selectedWorkflow.gradient }}></div>
        <div className="gradient-orb orb-2" style={{ background: selectedWorkflow.gradient }}></div>
        <div className="gradient-orb orb-3"></div>
        <div className="grid-pattern"></div>
      </div>

      <main className="workflows-main">
        {/* Header */}
        <header className="workflows-header">
          <div className="header-badge">
            <span className="badge-icon">⚡</span>
            <span>On-Demand.io Workflows</span>
          </div>
          <h1>AI-Powered Security Workflows</h1>
          <p className="header-subtitle">
            Multi-agent orchestrated analysis pipelines for comprehensive smart contract security
          </p>
        </header>

        {/* Workflow Selector */}
        <section className="workflow-selector">
          {WORKFLOWS.map((workflow) => (
            <button
              key={workflow.id}
              className={`workflow-card ${selectedWorkflow.id === workflow.id ? 'active' : ''}`}
              onClick={() => {
                setSelectedWorkflow(workflow);
                setResult(null);
                setError(null);
                setCurrentStep(-1);
              }}
              style={{ '--accent-color': workflow.accentColor } as React.CSSProperties}
            >
              <div className="workflow-card-gradient" style={{ background: workflow.gradient }}></div>
              <div className="workflow-card-content">
                <span className="workflow-icon">{workflow.icon}</span>
                <h3>{workflow.name.replace(workflow.icon, '').trim()}</h3>
                <p className="workflow-tagline">{workflow.tagline}</p>
              </div>
              {selectedWorkflow.id === workflow.id && (
                <div className="workflow-selected-indicator"></div>
              )}
            </button>
          ))}
        </section>

        {/* Selected Workflow Details */}
        <section className="workflow-details">
          <div className="workflow-info-panel">
            <div className="workflow-info-header">
              <span className="workflow-large-icon">{selectedWorkflow.icon}</span>
              <div>
                <h2>{selectedWorkflow.name}</h2>
                <p className="workflow-description">{selectedWorkflow.description}</p>
              </div>
            </div>

            {/* Workflow Steps */}
            <div className="workflow-steps">
              <h3>Workflow Pipeline</h3>
              <div className="steps-container">
                {selectedWorkflow.steps.map((step, index) => (
                  <div
                    key={index}
                    className={`workflow-step ${currentStep === index ? 'active' : ''} ${currentStep > index ? 'completed' : ''}`}
                  >
                    <div className="step-indicator">
                      {currentStep > index ? (
                        <span className="step-check">✓</span>
                      ) : currentStep === index ? (
                        <span className="step-spinner"></span>
                      ) : (
                        <span className="step-number">{index + 1}</span>
                      )}
                    </div>
                    <div className="step-content">
                      <span className="step-icon">{step.icon}</span>
                      <div className="step-text">
                        <span className="step-agent">{step.agent}</span>
                        <span className="step-task">{step.task}</span>
                      </div>
                    </div>
                    {index < selectedWorkflow.steps.length - 1 && (
                      <div className={`step-connector ${currentStep > index ? 'active' : ''}`}></div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Action Buttons Section */}
        <section className="workflow-input-section">
          <div className="input-header">
            <h3>🚀 Workflow Actions</h3>
            <span className="input-subtitle">Choose to activate or execute the pre-configured workflow</span>
          </div>

          <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            <button
              className="execute-btn"
              onClick={activateWorkflow}
              disabled={loading}
              style={{
                flex: 1,
                minWidth: '200px',
                background: loading && actionType === 'activate' ? undefined : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
              }}
            >
              {loading && actionType === 'activate' ? (
                <>
                  <span className="execute-spinner"></span>
                  <span>Activating...</span>
                </>
              ) : (
                <>
                  <span className="execute-icon">🔔</span>
                  <span>Activate Workflow</span>
                </>
              )}
            </button>

            <button
              className="execute-btn"
              onClick={executeWorkflow}
              disabled={loading}
              style={{
                flex: 1,
                minWidth: '200px',
                background: loading && actionType === 'execute' ? undefined : selectedWorkflow.gradient
              }}
            >
              {loading && actionType === 'execute' ? (
                <>
                  <span className="execute-spinner"></span>
                  <span>Executing...</span>
                </>
              ) : (
                <>
                  <span className="execute-icon">▶</span>
                  <span>Execute Workflow</span>
                </>
              )}
            </button>
          </div>

          <div className="workflow-info-box">
            <span className="info-icon">ℹ️</span>
            <div className="info-text">
              <strong>Built in On-Demand.io Platform</strong>
              <p><strong>Activate:</strong> Prepares the workflow to run (POST /workflow/{'{id}'}/activate)</p>
              <p><strong>Execute:</strong> Runs the workflow immediately (POST /workflow/{'{id}'}/execute)</p>
            </div>
          </div>
        </section>

        {/* Error Display */}
        {error && (
          <div className="workflow-error">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Results Section */}
        {result && (
          <section className="workflow-results">
            <div className="results-header">
              <div className="results-title">
                <span className="results-icon">{selectedWorkflow.icon}</span>
                <div>
                  <h2>Workflow {result.success ? (actionType === 'activate' ? 'Activated' : 'Executed') : 'Failed'}</h2>
                  <p>
                    <span className="result-meta">
                      {new Date(result.execution_time).toLocaleString()}
                    </span>
                    {result.execution_id && (
                      <span className="result-meta">
                        • Execution ID: {result.execution_id.substring(0, 12)}...
                      </span>
                    )}
                  </p>
                </div>
              </div>
              <div className="results-badge" style={{ background: result.success ? selectedWorkflow.gradient : '#ff4757' }}>
                {result.success ? `✓ ${actionType === 'activate' ? 'Activated' : 'Executed'}` : '✗ Failed'}
              </div>
            </div>

            <div className="result-content">
              <div className="result-panel">
                <h4>Status: {result.status}</h4>
                {result.message && <p>{result.message}</p>}
                {result.error && (
                  <div style={{ color: '#ff4757', marginTop: '10px' }}>
                    <strong>Error:</strong> {result.error}
                  </div>
                )}
                <details style={{ marginTop: '15px' }}>
                  <summary style={{ cursor: 'pointer', color: '#667eea' }}>View Raw Response</summary>
                  <pre className="result-json">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </details>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
