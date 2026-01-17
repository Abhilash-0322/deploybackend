'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { Navbar } from '@/components/ui/Navbar';
import './scanner.css';

// When served from same origin, use relative URLs
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

interface DemoContract {
  id: string;
  name: string;
  code: string;
  description: string;
  language: string;
}

interface Vulnerability {
  type: string;
  severity: string;
  title: string;
  description: string;
  location: string;
  recommendation: string;
  confidence: number;
  code_snippet?: string;
}

interface AnalysisResult {
  analysis_id: string;
  timestamp: string;
  vulnerabilities: Vulnerability[];
  severity_counts: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  risk_score: {
    score: number;
    level: string;
    description: string;
  };
  summary: string;
}

export default function ScannerPage() {
  const [activeTab, setActiveTab] = useState<'manual' | 'demo' | 'upload'>('manual');
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState<'move' | 'solidity' | 'rust'>('move');
  const [demoContracts, setDemoContracts] = useState<DemoContract[]>([]);
  const [selectedDemo, setSelectedDemo] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [currentScanLine, setCurrentScanLine] = useState(0);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadedFileUrl, setUploadedFileUrl] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const codeEditorRef = useRef<HTMLTextAreaElement>(null);

  // Load demo contracts
  useEffect(() => {
    const loadDemoContracts = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/contracts/demo-contracts`);
        if (response.ok) {
          const data = await response.json();
          setDemoContracts(data.contracts || []);
        }
      } catch (error) {
        console.error('Failed to load demo contracts:', error);
      }
    };

    loadDemoContracts();
  }, []);

  // Handle demo contract selection
  const handleDemoSelect = (contractId: string) => {
    const contract = demoContracts.find(c => c.id === contractId);
    if (contract) {
      setSelectedDemo(contractId);
      setCode(contract.code);
      // Auto-set language based on demo contract
      setLanguage(contract.language as 'move' | 'solidity' | 'rust');
      setShowResults(false);
      setAnalysisResult(null);
    }
  };

  // Animate scanning progress with line-by-line effect
  const animateScan = () => {
    return new Promise<void>((resolve) => {
      const totalLines = code.split('\n').length;
      let progress = 0;
      let lineIndex = 0;

      const interval = setInterval(() => {
        // Update progress
        progress += Math.random() * 12;
        if (progress >= 100) {
          progress = 100;
          lineIndex = totalLines;
          clearInterval(interval);
          setTimeout(resolve, 500);
        }

        // Update current scanning line based on progress
        lineIndex = Math.floor((progress / 100) * totalLines);
        setCurrentScanLine(lineIndex);
        setScanProgress(Math.min(100, progress));
      }, 150);
    });
  };

  // Handle contract analysis
  const handleAnalyze = async () => {
    if (!code.trim()) {
      alert('Please enter or select contract code to analyze');
      return;
    }

    setIsScanning(true);
    setScanProgress(0);
    setShowResults(false);
    setAnalysisResult(null);

    try {
      // Animate the scanning process
      await animateScan();

      // Call analysis API
      const response = await fetch(`${API_BASE}/api/contracts/analyze-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: code,
          language: language,
          include_ai_analysis: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const result = await response.json();
      setAnalysisResult(result);
      setShowResults(true);
    } catch (error) {
      console.error('Analysis error:', error);
      alert('Failed to analyze contract. Please try again.');
    } finally {
      setIsScanning(false);
      setCurrentScanLine(0);
      setScanProgress(0);
    }
  };

  // Clear editor
  const handleClear = () => {
    setCode('');
    setSelectedDemo(null);
    setAnalysisResult(null);
    setShowResults(false);
    setUploadedFile(null);
    setUploadedFileUrl('');
    codeEditorRef.current?.focus();
  };

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadedFile(file);
    setIsUploading(true);
    setShowResults(false);
    setAnalysisResult(null);

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('file', file);
      formData.append('language', language);

      // Upload and analyze
      const response = await fetch(`${API_BASE}/api/contracts/upload-and-analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();

      // Set the code in the editor
      setCode(result.code);

      // Store on-demand.io file URL if available
      if (result.file_url) {
        setUploadedFileUrl(result.file_url);
        console.log('File saved on on-demand.io:', result.file_url);
      }

      // Set analysis results
      setAnalysisResult(result.analysis);
      setShowResults(true);
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload and analyze file. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="scanner-page">
      {/* Unified Navigation */}
      <Navbar />

      {/* Hero Section */}
      <section className="scanner-hero">
        <div className="scanner-hero-content">
          <h1 className="scanner-title">
            Smart Contract <span className="gradient-text">Security Scanner</span>
          </h1>
          <p className="scanner-subtitle">
            Analyze Move smart contracts for vulnerabilities with AI-powered detection
          </p>
        </div>
      </section>

      {/* Main Content */}
      <div className="scanner-container">
        {/* Tab Selection */}
        <div className="scanner-tabs">
          <button
            className={`tab-button ${activeTab === 'manual' ? 'active' : ''}`}
            onClick={() => setActiveTab('manual')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            Manual Input
          </button>
          <button
            className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            Upload File
          </button>
          <button
            className={`tab-button ${activeTab === 'demo' ? 'active' : ''}`}
            onClick={() => setActiveTab('demo')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </svg>
            Demo Contracts
          </button>
        </div>

        <div className="scanner-content">
          {/* Left Panel - Code Editor/Demo Selection */}
          <div className="scanner-panel editor-panel">
            {activeTab === 'manual' ? (
              <>
                <div className="panel-header">
                  <div>
                    <h2>Paste Contract Code</h2>
                    <div className="language-selector">
                      <label htmlFor="language">Language:</label>
                      <select
                        id="language"
                        value={language}
                        onChange={(e) => setLanguage(e.target.value as 'move' | 'solidity' | 'rust')}
                        className="language-select"
                      >
                        <option value="move">Move</option>
                        <option value="solidity">Solidity (ETH)</option>
                        <option value="rust">Rust (Solana)</option>
                      </select>
                    </div>
                  </div>
                  <div className="panel-actions">
                    <button className="action-btn" onClick={handleClear} title="Clear">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 6h18" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
                        <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                  </div>
                </div>
                <div className="code-editor-container">
                  <textarea
                    ref={codeEditorRef}
                    className="code-editor"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder={
                      language === 'move'
                        ? "// Paste your Move smart contract code here...\n\nmodule example::contract {\n    // Your code\n}"
                        : language === 'solidity'
                          ? "// Paste your Solidity smart contract code here...\n\npragma solidity ^0.8.0;\n\ncontract Example {\n    // Your code\n}"
                          : "// Paste your Rust/Solana program code here...\n\nuse anchor_lang::prelude::*;\n\n#[program]\npub mod example {\n    // Your code\n}"
                    }
                    spellCheck={false}
                  />
                  <div className="editor-info">
                    <span className="info-item">
                      <span className="info-label">Lines:</span> {code.split('\n').length}
                    </span>
                    <span className="info-item">
                      <span className="info-label">Characters:</span> {code.length}
                    </span>
                  </div>
                </div>
              </>
            ) : activeTab === 'upload' ? (
              <>
                <div className="panel-header">
                  <div>
                    <h2>Upload Contract File</h2>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                      Powered by <strong style={{ color: 'var(--primary)' }}>on-demand.io Media API</strong>
                    </p>
                    <div className="language-selector">
                      <label htmlFor="upload-language">Language:</label>
                      <select
                        id="upload-language"
                        value={language}
                        onChange={(e) => setLanguage(e.target.value as 'move' | 'solidity' | 'rust')}
                        className="language-select"
                      >
                        <option value="move">Move (.move)</option>
                        <option value="solidity">Solidity (.sol)</option>
                        <option value="rust">Rust (.rs)</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div className="upload-area">
                  <div className="upload-dropzone">
                    <input
                      type="file"
                      id="file-upload"
                      accept=".move,.sol,.rs,.txt"
                      onChange={handleFileUpload}
                      style={{ display: 'none' }}
                    />
                    <label htmlFor="file-upload" className="upload-label">
                      {isUploading ? (
                        <>
                          <span className="scanning-spinner"></span>
                          <h3>Processing...</h3>
                          <p>Extracting and analyzing contract</p>
                        </>
                      ) : uploadedFile ? (
                        <>
                          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                            <polyline points="22 4 12 14.01 9 11.01" />
                          </svg>
                          <h3>File Uploaded Successfully</h3>
                          <p className="uploaded-filename">{uploadedFile.name}</p>
                          {uploadedFileUrl && (
                            <p className="file-url-info">
                              📁 Stored on on-demand.io
                            </p>
                          )}
                          <button
                            type="button"
                            className="upload-another-btn"
                            onClick={() => {
                              setUploadedFile(null);
                              setUploadedFileUrl('');
                              setCode('');
                              setShowResults(false);
                            }}
                          >
                            Upload Another File
                          </button>
                        </>
                      ) : (
                        <>
                          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="17 8 12 3 7 8" />
                            <line x1="12" y1="3" x2="12" y2="15" />
                          </svg>
                          <h3>Drop your contract file here</h3>
                          <p>or click to browse</p>
                          <span className="supported-formats">
                            Supports: .move, .sol, .rs files
                          </span>
                          <span className="api-badge">
                            🚀 Processed via on-demand.io Media API
                          </span>
                        </>
                      )}
                    </label>
                  </div>
                  {code && (
                    <div className="uploaded-code-preview">
                      <h4>Extracted Contract Code:</h4>
                      <div className="code-preview-box">
                        <pre>{code.slice(0, 500)}{code.length > 500 ? '...' : ''}</pre>
                      </div>
                      <div className="editor-info">
                        <span className="info-item">
                          <span className="info-label">Lines:</span> {code.split('\n').length}
                        </span>
                        <span className="info-item">
                          <span className="info-label">Characters:</span> {code.length}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className="panel-header">
                  <h2>Select Demo Contract</h2>
                </div>
                <div className="demo-contracts-list">
                  {demoContracts.map((contract) => (
                    <div
                      key={contract.id}
                      className={`demo-contract-card ${selectedDemo === contract.id ? 'selected' : ''}`}
                      data-language={contract.language}
                      onClick={() => handleDemoSelect(contract.id)}
                    >
                      <div className="demo-contract-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                          <line x1="16" y1="13" x2="8" y2="13" />
                          <line x1="16" y1="17" x2="8" y2="17" />
                          <polyline points="10 9 9 9 8 9" />
                        </svg>
                      </div>
                      <div className="demo-contract-info">
                        <h3>{contract.name}</h3>
                        <p>{contract.description}</p>
                        <span className="demo-contract-language" data-language={contract.language}>
                          {contract.language === 'move' ? 'Move' : contract.language === 'solidity' ? 'Solidity' : 'Rust'}
                        </span>
                      </div>
                      {selectedDemo === contract.id && (
                        <div className="selected-checkmark">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Analyze Button */}
            <div className="panel-footer">
              <button
                className="analyze-button"
                onClick={handleAnalyze}
                disabled={isScanning || !code.trim()}
              >
                {isScanning ? (
                  <>
                    <span className="scanning-spinner"></span>
                    Analyzing... {Math.round(scanProgress)}%
                  </>
                ) : (
                  <>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                      <polyline points="22 4 12 14.01 9 11.01" />
                    </svg>
                    Analyze Contract
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right Panel - Results */}
          <div className="scanner-panel results-panel">
            {isScanning ? (
              <div className="scanning-animation">
                <div className="scan-visualization">
                  <div className="code-preview-scan">
                    <div className="scan-lines">
                      {code.split('\n').map((line, idx) => (
                        <div
                          key={idx}
                          className={`scan-line-item ${idx === currentScanLine ? 'scanning' :
                              idx < currentScanLine ? 'scanned' : ''
                            }`}
                        >
                          <span className="line-number">{idx + 1}</span>
                          <span className="line-code">{line || ' '}</span>
                        </div>
                      ))}
                    </div>
                    <div className="scan-beam"></div>
                  </div>
                  <div className="scan-status">
                    <div className="status-dots">
                      <span className="dot"></span>
                      <span className="dot"></span>
                      <span className="dot"></span>
                    </div>
                    <p>Analyzing contract for vulnerabilities...</p>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${scanProgress}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>
            ) : showResults && analysisResult ? (
              <div className="analysis-results">
                <div className="results-header">
                  <div>
                    <h2>
                      Analysis Results
                      <span className={`language-badge ${language}`}>
                        {language === 'move' ? 'Move' : language === 'solidity' ? 'Solidity' : 'Rust'}
                      </span>
                    </h2>
                  </div>
                  <span className="results-timestamp">
                    {new Date(analysisResult.timestamp).toLocaleString()}
                  </span>
                </div>

                {/* Risk Score */}
                <div className={`risk-score-card ${analysisResult.risk_score.level.toLowerCase()}`}>
                  <div className="risk-score-value">{analysisResult.risk_score.score}</div>
                  <div className="risk-score-info">
                    <h3>{analysisResult.risk_score.level} RISK</h3>
                    <p>{analysisResult.summary}</p>
                  </div>
                </div>

                {/* Severity Summary */}
                <div className="severity-summary">
                  <div className="severity-badge critical">
                    {analysisResult.severity_counts.critical} Critical
                  </div>
                  <div className="severity-badge high">
                    {analysisResult.severity_counts.high} High
                  </div>
                  <div className="severity-badge medium">
                    {analysisResult.severity_counts.medium} Medium
                  </div>
                  <div className="severity-badge low">
                    {analysisResult.severity_counts.low} Low
                  </div>
                </div>

                {/* Vulnerabilities List */}
                {analysisResult.vulnerabilities.length > 0 && (
                  <div className="vulnerabilities-section">
                    <h3>Detected Vulnerabilities</h3>
                    <div className="vulnerabilities-list">
                      {analysisResult.vulnerabilities.map((vuln, idx) => (
                        <div key={idx} className={`vulnerability-item ${vuln.severity.toLowerCase()}`}>
                          <div className="vuln-header">
                            <span className={`vuln-severity-badge ${vuln.severity.toLowerCase()}`}>
                              {vuln.severity}
                            </span>
                            <h4>{vuln.title}</h4>
                          </div>
                          <p className="vuln-description">{vuln.description}</p>
                          {vuln.location && (
                            <p className="vuln-location">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                                <circle cx="12" cy="10" r="3" />
                              </svg>
                              {vuln.location}
                            </p>
                          )}
                          {vuln.code_snippet && (
                            <div className="vuln-code-snippet">
                              <code>{vuln.code_snippet}</code>
                            </div>
                          )}
                          <div className="vuln-recommendation">
                            <strong>Recommendation:</strong> {vuln.recommendation}
                          </div>
                          <div className="vuln-confidence">
                            Confidence: {Math.round(vuln.confidence * 100)}%
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {analysisResult.vulnerabilities.length === 0 && (
                  <div className="no-vulnerabilities">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                      <polyline points="22 4 12 14.01 9 11.01" />
                    </svg>
                    <h3>No Vulnerabilities Detected</h3>
                    <p>The contract appears to follow security best practices.</p>
                  </div>
                )}

                {/* Ask AI Agents Button */}
                <div className="ai-agents-cta">
                  <Link href="/agents" className="ai-agents-button">
                    <span className="ai-icon">🤖</span>
                    <div className="ai-button-content">
                      <span className="ai-button-title">Ask AI Agents</span>
                      <span className="ai-button-subtitle">Get detailed insights from 6 specialized AI agents</span>
                    </div>
                    <span className="ai-button-arrow">→</span>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="no-results">
                <div className="no-results-icon">
                  <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.35-4.35" />
                    <path d="M11 8v6" />
                    <path d="M8 11h6" />
                  </svg>
                </div>
                <h3>Ready to Analyze</h3>
                <p>Paste your contract code or select a demo contract, then click "Analyze Contract" to begin security analysis.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
