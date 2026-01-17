'use client';

import Link from 'next/link';
import { CodePreview } from './CodePreview';

const statsData = [
    { value: '15', label: 'Vulnerability Types' },
    { value: '3', label: 'Demo Contracts' },
    { value: '100', label: 'Risk Score Range' },
];

export function Hero() {
    return (
        <section id="hero" className="hero">
            <div className="hero-content">
                {/* Badge */}
                <div className="hero-badge">
                    <span className="status-dot"></span>
                    <svg className="sparkle-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 3v18M3 12h18M6.3 6.3l11.4 11.4M6.3 17.7L17.7 6.3" />
                    </svg>
                    Powered by Groq AI
                </div>

                {/* Title */}
                <h1 className="hero-title">
                    <span>Protect Your </span>
                    <span className="gradient-text">Smart Contracts </span>
                    <span>in Real-time</span>
                </h1>

                {/* Description */}
                <p className="hero-description">
                    AI-powered compliance agent that scans, validates, and monitors
                    your Aptos dApps for vulnerabilities and policy violations.
                </p>

                {/* CTAs */}
                <div className="hero-ctas">
                    <Link href="/dashboard" className="btn btn-primary">
                        <span>Open Dashboard</span>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                    </Link>
                    <Link href="#demo" className="btn btn-secondary">
                        <span>See Demo</span>
                    </Link>
                </div>

                {/* Stats */}
                <div className="hero-stats">
                    {statsData.map((stat, i) => (
                        <div key={i} className="stat-item">
                            <div className="stat-value">{stat.value}</div>
                            <div className="stat-label">{stat.label}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Right - Code Preview */}
            <div className="hero-code">
                <CodePreview />
            </div>

            {/* Scroll indicator */}
            <div className="scroll-indicator">
                <div className="scroll-dot"></div>
            </div>
        </section>
    );
}
