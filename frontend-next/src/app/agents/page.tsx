'use client';

import { useState, useEffect, useRef } from 'react';
import { Navbar } from '@/components/ui/Navbar';
import Link from 'next/link';
import './agents.css';

// When served from same origin, use relative URLs
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  capabilities: string[];
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  agent?: Agent;
  isTyping?: boolean;
}

interface ChatSession {
  agent: Agent;
  messages: Message[];
  sessionId?: string;
  isActive: boolean;
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeAgent, setActiveAgent] = useState<Agent | null>(null);
  const [chatSession, setChatSession] = useState<ChatSession | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [selectedModel, setSelectedModel] = useState('gpt4o');
  const [codeContext, setCodeContext] = useState('');
  const [showCodeInput, setShowCodeInput] = useState(false);
  const [multiAnalysisMode, setMultiAnalysisMode] = useState(false);
  const [multiAnalysisResults, setMultiAnalysisResults] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const models = [
    { id: 'gpt4o', name: 'GPT-4o', badge: '✨ Best', color: '#10b981' },
    { id: 'claude', name: 'Claude', badge: '🧠 Smart', color: '#8b5cf6' },
    { id: 'grok', name: 'Grok', badge: '⚡ Fast', color: '#f59e0b' },
    { id: 'gemini', name: 'Gemini', badge: '🚀 Quick', color: '#3b82f6' },
  ];

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [chatSession?.messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadAgents = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/agents/list`);
      const data = await response.json();
      setAgents(data.agents || []);
    } catch (error) {
      console.error('Error loading agents:', error);
      // Fallback agents for demo
      setAgents([
        { id: 'threat_hunter', name: '🎯 Threat Hunter', description: 'Real-time blockchain threat detection', icon: '🎯', color: '#ef4444', capabilities: ['Attack Detection', 'Rug Pull Analysis'] },
        { id: 'compliance_auditor', name: '⚖️ Compliance Auditor', description: 'Regulatory compliance verification', icon: '⚖️', color: '#3b82f6', capabilities: ['SEC Compliance', 'AML Check'] },
        { id: 'gas_wizard', name: '⛽ Gas Wizard', description: 'Gas optimization analysis', icon: '⛽', color: '#22c55e', capabilities: ['Cost Reduction', 'Optimization'] },
        { id: 'defi_guardian', name: '🏦 DeFi Guardian', description: 'DeFi protocol security', icon: '🏦', color: '#8b5cf6', capabilities: ['Flash Loan Protection', 'Oracle Security'] },
        { id: 'audit_master', name: '📋 Audit Master', description: 'Professional audit reports', icon: '📋', color: '#f59e0b', capabilities: ['Full Audits', 'Severity Rating'] },
        { id: 'move_sensei', name: '🥋 Move Sensei', description: 'Aptos Move language expert', icon: '🥋', color: '#ec4899', capabilities: ['Resource Analysis', 'Move Prover'] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startChat = (agent: Agent) => {
    setActiveAgent(agent);
    setChatSession({
      agent,
      messages: [{
        id: Date.now().toString(),
        role: 'system',
        content: `Welcome! I'm the ${agent.name}. ${agent.description}. How can I help you analyze your smart contract today?`,
        timestamp: new Date().toISOString()
      }],
      isActive: true
    });
    setMultiAnalysisMode(false);
    setMultiAnalysisResults(null);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !activeAgent || !chatSession || isSending) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    // Add user message
    setChatSession(prev => prev ? {
      ...prev,
      messages: [...prev.messages, userMessage]
    } : null);

    const messageToSend = inputMessage;
    setInputMessage('');
    setIsSending(true);

    // Add typing indicator
    const typingMessage: Message = {
      id: 'typing',
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      agent: activeAgent,
      isTyping: true
    };

    setChatSession(prev => prev ? {
      ...prev,
      messages: [...prev.messages, typingMessage]
    } : null);

    try {
      const response = await fetch(`${API_BASE}/api/agents/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: activeAgent.id,
          message: messageToSend,
          session_id: chatSession.sessionId,
          model: selectedModel,
          context: codeContext ? { code: codeContext, language: 'move' } : undefined
        })
      });

      const data = await response.json();

      // Remove typing indicator and add response
      setChatSession(prev => {
        if (!prev) return null;
        const messagesWithoutTyping = prev.messages.filter(m => m.id !== 'typing');
        return {
          ...prev,
          sessionId: data.session_id,
          messages: [...messagesWithoutTyping, {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.message || data.answer || 'I apologize, I could not process your request.',
            timestamp: data.timestamp || new Date().toISOString(),
            agent: activeAgent
          }]
        };
      });
    } catch (error) {
      console.error('Error sending message:', error);
      setChatSession(prev => {
        if (!prev) return null;
        const messagesWithoutTyping = prev.messages.filter(m => m.id !== 'typing');
        return {
          ...prev,
          messages: [...messagesWithoutTyping, {
            id: Date.now().toString(),
            role: 'assistant',
            content: '❌ Connection error. Please check your backend is running and try again.',
            timestamp: new Date().toISOString(),
            agent: activeAgent
          }]
        };
      });
    } finally {
      setIsSending(false);
    }
  };

  const runMultiAgentAnalysis = async () => {
    if (!codeContext.trim()) {
      alert('Please enter smart contract code first!');
      return;
    }

    setIsAnalyzing(true);
    setMultiAnalysisResults(null);

    try {
      const response = await fetch(`${API_BASE}/api/agents/analyze/multi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: codeContext,
          language: 'move'
        })
      });

      const data = await response.json();
      setMultiAnalysisResults(data);
    } catch (error) {
      console.error('Multi-agent analysis failed:', error);
      setMultiAnalysisResults({
        error: 'Analysis failed. Please ensure the backend is running.'
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const closeChat = () => {
    setActiveAgent(null);
    setChatSession(null);
    setCodeContext('');
    setShowCodeInput(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (content: string) => {
    // Simple markdown-like formatting
    return content
      .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
      .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/^### (.+)$/gm, '<h3 class="msg-h3">$1</h3>')
      .replace(/^## (.+)$/gm, '<h2 class="msg-h2">$1</h2>')
      .replace(/^# (.+)$/gm, '<h1 class="msg-h1">$1</h1>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/\n/g, '<br/>');
  };

  return (
    <div className="agents-page">
      <Navbar />

      {/* Animated background */}
      <div className="agents-bg">
        <div className="agents-bg-gradient"></div>
        <div className="agents-bg-grid"></div>
        <div className="floating-orbs">
          {[...Array(6)].map((_, i) => (
            <div key={i} className={`orb orb-${i + 1}`}></div>
          ))}
        </div>
      </div>

      <main className="agents-main">
        {/* Header Section */}
        <header className="agents-header">
          <div className="header-badge">
            <span className="badge-icon">⚡</span>
            <span>Powered by On-Demand.io</span>
          </div>
          <h1 className="agents-title">
            <span className="title-gradient">AI Security Agents</span>
          </h1>
          <p className="agents-subtitle">
            6 specialized AI agents for comprehensive smart contract security analysis,
            compliance verification, and optimization recommendations.
          </p>

          {/* Model Selector */}
          <div className="model-selector">
            <span className="model-label">AI Model:</span>
            <div className="model-options">
              {models.map(model => (
                <button
                  key={model.id}
                  className={`model-btn ${selectedModel === model.id ? 'active' : ''}`}
                  onClick={() => setSelectedModel(model.id)}
                  style={{ '--model-color': model.color } as React.CSSProperties}
                >
                  <span className="model-badge">{model.badge}</span>
                  <span className="model-name">{model.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="quick-actions">
            <button
              className={`action-btn ${multiAnalysisMode ? 'active' : ''}`}
              onClick={() => {
                setMultiAnalysisMode(!multiAnalysisMode);
                if (!multiAnalysisMode) {
                  setActiveAgent(null);
                  setChatSession(null);
                }
              }}
            >
              <span className="action-icon">🔬</span>
              <span>Multi-Agent Analysis</span>
            </button>
            <button
              className="action-btn"
              onClick={() => setShowCodeInput(!showCodeInput)}
            >
              <span className="action-icon">📝</span>
              <span>{showCodeInput ? 'Hide Code Input' : 'Add Contract Code'}</span>
            </button>
          </div>
        </header>

        {/* Code Input Section */}
        {showCodeInput && (
          <div className="code-input-section">
            <div className="code-input-header">
              <h3>📝 Smart Contract Code</h3>
              <p>Paste your contract code for context-aware analysis</p>
            </div>
            <textarea
              className="code-textarea"
              value={codeContext}
              onChange={(e) => setCodeContext(e.target.value)}
              placeholder="// Paste your Move, Solidity, or Rust smart contract code here...

module example::token {
    use aptos_framework::coin;
    
    struct MyToken has key {
        value: u64,
    }
    
    public fun transfer(from: &signer, to: address, amount: u64) {
        // Your code here
    }
}"
              rows={12}
            />
            {codeContext && (
              <div className="code-stats">
                <span>📊 {codeContext.split('\n').length} lines</span>
                <span>📏 {codeContext.length} characters</span>
              </div>
            )}
          </div>
        )}

        {/* Multi-Agent Analysis Mode */}
        {multiAnalysisMode && (
          <div className="multi-analysis-section">
            <div className="multi-analysis-header">
              <h2>🔬 Multi-Agent Comprehensive Analysis</h2>
              <p>Analyze your contract with all 6 specialized AI agents simultaneously</p>
            </div>

            {!codeContext && (
              <div className="no-code-warning">
                <span className="warning-icon">⚠️</span>
                <span>Please add your smart contract code above first</span>
              </div>
            )}

            <button
              className="run-analysis-btn"
              onClick={runMultiAgentAnalysis}
              disabled={!codeContext || isAnalyzing}
            >
              {isAnalyzing ? (
                <>
                  <span className="spinner"></span>
                  <span>Analyzing with 6 Agents...</span>
                </>
              ) : (
                <>
                  <span>🚀</span>
                  <span>Run Multi-Agent Analysis</span>
                </>
              )}
            </button>

            {/* Analysis Results */}
            {multiAnalysisResults && (
              <div className="multi-results">
                {multiAnalysisResults.error ? (
                  <div className="analysis-error">
                    <span>❌</span>
                    <span>{multiAnalysisResults.error}</span>
                  </div>
                ) : (
                  <div className="results-grid">
                    {Object.entries(multiAnalysisResults.results || {}).map(([agentId, result]: [string, any]) => {
                      const agent = agents.find(a => a.id === agentId);
                      return (
                        <div
                          key={agentId}
                          className="result-card"
                          style={{ '--agent-color': agent?.color || '#3b82f6' } as React.CSSProperties}
                        >
                          <div className="result-header">
                            <span className="result-icon">{agent?.icon}</span>
                            <span className="result-agent">{agent?.name || agentId}</span>
                            {result.success && <span className="success-badge">✓</span>}
                          </div>
                          <div
                            className="result-content"
                            dangerouslySetInnerHTML={{ __html: formatMessage(result.message || 'No response') }}
                          />
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Agent Grid or Chat Interface */}
        {!multiAnalysisMode && (
          <>
            {!activeAgent ? (
              /* Agent Selection Grid */
              <div className="agents-grid">
                {loading ? (
                  <div className="loading-state">
                    <div className="loading-spinner"></div>
                    <p>Loading AI Agents...</p>
                  </div>
                ) : (
                  agents.map((agent, index) => (
                    <div
                      key={agent.id}
                      className="agent-card"
                      style={{
                        '--agent-color': agent.color,
                        '--animation-delay': `${index * 0.1}s`
                      } as React.CSSProperties}
                      onClick={() => startChat(agent)}
                    >
                      <div className="agent-glow"></div>
                      <div className="agent-content">
                        <div className="agent-icon-wrapper">
                          <span className="agent-icon">{agent.icon}</span>
                          <div className="agent-pulse"></div>
                        </div>
                        <h3 className="agent-name">{agent.name}</h3>
                        <p className="agent-description">{agent.description}</p>
                        <div className="agent-capabilities">
                          {agent.capabilities?.slice(0, 3).map((cap, i) => (
                            <span key={i} className="capability-tag">{cap}</span>
                          ))}
                        </div>
                        <button className="chat-btn">
                          <span>💬</span>
                          <span>Start Chat</span>
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            ) : (
              /* Chat Interface */
              <div className="chat-interface">
                <div className="chat-header">
                  <button className="back-btn" onClick={closeChat}>
                    ← Back to Agents
                  </button>
                  <div className="chat-agent-info">
                    <span className="chat-agent-icon">{activeAgent.icon}</span>
                    <div>
                      <h3>{activeAgent.name}</h3>
                      <p>{activeAgent.description}</p>
                    </div>
                  </div>
                  <div className="chat-model-badge" style={{ background: models.find(m => m.id === selectedModel)?.color }}>
                    {models.find(m => m.id === selectedModel)?.name}
                  </div>
                </div>

                <div className="chat-messages" ref={chatContainerRef}>
                  {chatSession?.messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`message ${msg.role} ${msg.isTyping ? 'typing' : ''}`}
                    >
                      {msg.role === 'assistant' && (
                        <div className="message-avatar" style={{ background: activeAgent.color }}>
                          {activeAgent.icon}
                        </div>
                      )}
                      <div className="message-content">
                        {msg.isTyping ? (
                          <div className="typing-indicator">
                            <span></span><span></span><span></span>
                          </div>
                        ) : (
                          <div dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }} />
                        )}
                        {!msg.isTyping && (
                          <span className="message-time">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>

                <div className="chat-input-container">
                  {codeContext && (
                    <div className="context-indicator">
                      <span>📎 Contract code attached ({codeContext.split('\n').length} lines)</span>
                      <button onClick={() => setCodeContext('')}>✕</button>
                    </div>
                  )}
                  <div className="chat-input-wrapper">
                    <textarea
                      className="chat-input"
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={`Ask ${activeAgent.name} about your smart contract...`}
                      rows={1}
                      disabled={isSending}
                    />
                    <button
                      className="send-btn"
                      onClick={sendMessage}
                      disabled={!inputMessage.trim() || isSending}
                    >
                      {isSending ? (
                        <span className="send-spinner"></span>
                      ) : (
                        <span>➤</span>
                      )}
                    </button>
                  </div>
                  <div className="input-hints">
                    <span>Press Enter to send • Shift+Enter for new line</span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Footer */}
        <footer className="agents-footer">
          <div className="footer-content">
            <div className="footer-brand">
              <span className="footer-logo">🛡️</span>
              <span>AptosComply AI Agents</span>
            </div>
            <div className="footer-links">
              <Link href="/scanner">Contract Scanner</Link>
              <Link href="/dashboard">Dashboard</Link>
              <Link href="/">Home</Link>
            </div>
            <div className="footer-powered">
              <span>Powered by</span>
              <span className="ondemand-badge">On-Demand.io</span>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}
