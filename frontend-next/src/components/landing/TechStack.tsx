'use client';

const techStack = [
    { icon: '🔷', name: 'Aptos' },
    { icon: '⚡', name: 'FastAPI' },
    { icon: '🤖', name: 'Groq AI' },
    { icon: '🔌', name: 'WebSockets' },
    { icon: '📜', name: 'Move' },
];

export function TechStack() {
    return (
        <section id="tech" className="section">
            <div className="section-container">
                <div className="section-header">
                    <span className="section-badge">Technology</span>
                    <h2 className="section-title">Built With Modern Stack</h2>
                </div>
                <div className="tech-grid">
                    {techStack.map((tech, i) => (
                        <div key={i} className="tech-item">
                            <div className="tech-icon">{tech.icon}</div>
                            <span className="tech-name">{tech.name}</span>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
