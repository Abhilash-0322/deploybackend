'use client';

const features = [
    {
        icon: 'search',
        title: 'Vulnerability Detection',
        description: 'Pattern-based analysis detecting missing signers, capability leaks, and access control flaws',
        tags: ['CRITICAL', 'HIGH', 'MEDIUM'],
    },
    {
        icon: 'brain',
        title: 'AI-Powered Analysis',
        description: "LLM-based anomaly detection using Groq's Llama 3.3 70B for deep contract analysis",
        tags: ['GROQ', 'LLAMA 3.3'],
    },
    {
        icon: 'activity',
        title: 'Real-time Monitoring',
        description: 'WebSocket-powered transaction monitoring with instant alerts for suspicious activity',
        tags: ['LIVE', 'WEBSOCKET'],
    },
    {
        icon: 'shield',
        title: 'Compliance Engine',
        description: 'Configurable policy rules with blocked addresses, value limits, and custom thresholds',
        tags: ['POLICIES', 'RULES'],
    },
];

const getIcon = (type: string) => {
    switch(type) {
        case 'search': return <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>;
        case 'brain': return <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>;
        case 'activity': return <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>;
        case 'shield': return <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>;
        default: return null;
    }
};

export function Features() {
    return (
        <section id="features" className="section">
            <div className="section-container">
                {/* Header */}
                <div className="section-header">
                    <span className="section-badge">Features</span>
                    <h2 className="section-title">Complete Security Suite</h2>
                    <p className="section-subtitle">
                        Everything you need to secure your Aptos smart contracts
                    </p>
                </div>

                {/* Grid */}
                <div className="features-grid">
                    {features.map((feature, i) => (
                        <div key={i} className="feature-card">
                            <div className="feature-icon">
                                {getIcon(feature.icon)}
                            </div>

                            <h3 className="feature-title">
                                {feature.title}
                            </h3>
                            <p className="feature-description">
                                {feature.description}
                            </p>

                            {/* Tags */}
                            <div className="feature-tags">
                                {feature.tags.map((tag, j) => (
                                    <span key={j} className="feature-tag">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
