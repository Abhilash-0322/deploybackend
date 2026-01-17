'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const codeLines = [
    { text: 'module vulnerable_token {', type: 'keyword' },
    { text: '', type: 'empty' },
    { text: '    // ⚠️ CRITICAL: No signer verification!', type: 'comment' },
    { text: '    public entry fun mint_to_anyone(', type: 'function' },
    { text: '        to: address,', type: 'param' },
    { text: '        amount: u64', type: 'param' },
    { text: '    ) {', type: 'bracket' },
    { text: '        // Anyone can mint tokens!', type: 'comment' },
    { text: '        ...', type: 'code' },
    { text: '    }', type: 'bracket' },
    { text: '', type: 'empty' },
    { text: '    // ⚠️ Capability with copy ability', type: 'comment' },
    { text: '    struct AdminCap has copy, store {}', type: 'struct' },
    { text: '}', type: 'bracket' },
];

const alerts = [
    { text: '🚨 Missing signer verification', severity: 'critical' },
    { text: '⚠️ Capability with copy ability', severity: 'high' },
];

export function CodePreview() {
    const [currentLine, setCurrentLine] = useState(0);
    const [showAlerts, setShowAlerts] = useState(false);
    const [scanning, setScanning] = useState(false);

    useEffect(() => {
        // Type out code lines
        const timer = setInterval(() => {
            setCurrentLine((prev) => {
                if (prev < codeLines.length) return prev + 1;
                return prev;
            });
        }, 150);

        // Start scan after typing
        const scanTimer = setTimeout(() => {
            setScanning(true);
        }, 2500);

        // Show alerts after scan
        const alertTimer = setTimeout(() => {
            setShowAlerts(true);
        }, 4000);

        return () => {
            clearInterval(timer);
            clearTimeout(scanTimer);
            clearTimeout(alertTimer);
        };
    }, []);

    const getLineColor = (type: string) => {
        switch (type) {
            case 'keyword':
            case 'bracket':
                return 'text-[#c792ea]'; // Purple for keywords
            case 'function':
            case 'struct':
                return 'text-[#82aaff]'; // Blue for functions
            case 'comment':
                return 'text-[#ff7b72]'; // Red for comments (matching vanilla)
            case 'param':
                return 'text-[#82aaff]'; // Cyan for params
            default:
                return 'text-[#e2e8f0]';
        }
    };

    return (
        <motion.div
            className="relative"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            style={{ perspective: '1000px' }}
        >
            {/* Code Window - matching vanilla transform */}
            <motion.div
                className="relative bg-[rgba(15,15,25,0.9)] border border-primary/20 rounded-[16px] overflow-hidden"
                style={{
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
                    transform: 'rotateY(-5deg) rotateX(5deg)',
                }}
                whileHover={{ rotateY: 0, rotateX: 0 }}
                transition={{ duration: 0.5 }}
            >
                {/* Window Header - matching vanilla */}
                <div className="flex items-center gap-2 px-4 py-3 bg-black/30 border-b border-white/5">
                    <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
                    <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
                    <div className="w-3 h-3 rounded-full bg-[#28c840]" />
                    <span className="ml-2 text-[0.85rem] text-white/40 font-mono">vulnerable_token.move</span>
                </div>

                {/* Code Content - matching vanilla 24px padding, min-height 300px */}
                <pre className="p-6 font-mono text-[0.9rem] leading-[1.8] min-h-[300px] overflow-hidden">
                    <code>
                        {codeLines.slice(0, currentLine).map((line, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.1 }}
                                className={getLineColor(line.type)}
                            >
                                {line.text || '\u00A0'}
                            </motion.div>
                        ))}
                        {currentLine < codeLines.length && (
                            <span className="inline-block w-2 h-5 bg-primary animate-pulse ml-1" />
                        )}
                    </code>
                </pre>

                {/* Scan Line - matching vanilla gradient and animation */}
                {scanning && (
                    <motion.div
                        className="absolute left-0 w-full h-1 pointer-events-none"
                        style={{
                            background: 'linear-gradient(90deg, transparent, #6366f1, #22d3ee, transparent)',
                            boxShadow: '0 0 20px #6366f1',
                        }}
                        initial={{ top: 0, opacity: 1 }}
                        animate={{ top: '100%', opacity: 0 }}
                        transition={{ duration: 2, repeat: Infinity }}
                    />
                )}
            </motion.div>

            {/* Vulnerability Alerts - matching vanilla positioning and styling */}
            {showAlerts && (
                <div className="absolute -right-5 top-1/2 -translate-y-1/2 flex flex-col gap-3">
                    {alerts.map((alert, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.5, delay: i * 0.3 }}
                            className={`px-5 py-3 rounded-lg border-l-[3px] text-[0.85rem] font-medium ${alert.severity === 'critical'
                                    ? 'bg-red-500/10 border-red-500 text-red-500'
                                    : 'bg-orange-500/10 border-orange-500 text-orange-500'
                                }`}
                        >
                            {alert.text}
                        </motion.div>
                    ))}
                </div>
            )}
        </motion.div>
    );
}
