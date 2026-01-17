'use client';

import Link from 'next/link';

export function CTA() {
    return (
        <section className="section cta-section">
            <div className="cta-content">
                <h2 className="section-title">Ready to Secure Your dApp?</h2>
                <p className="section-subtitle">Start analyzing your smart contracts in seconds</p>
                <div style={{display: 'flex', gap: '20px', justifyContent: 'center', marginTop: '40px'}}>
                    <Link href="/scanner" className="btn btn-primary btn-large">
                        <span>Try Scanner</span>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="11" cy="11" r="8"/>
                            <path d="m21 21-4.35-4.35"/>
                        </svg>
                    </Link>
                    <Link href="/dashboard" className="btn btn-secondary btn-large">
                        <span>Launch Dashboard</span>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                    </Link>
                </div>
            </div>
        </section>
    );
}

export function Footer() {
    return (
        <footer className="footer">
            <p>Aptos Shield — Built for Hackathon 2026</p>
        </footer>
    );
}
