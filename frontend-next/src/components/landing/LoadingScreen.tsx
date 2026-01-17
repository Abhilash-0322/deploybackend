'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export function LoadingScreen() {
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Match vanilla timing: 2.5s delay before fade out
        const timer = setTimeout(() => {
            setIsLoading(false);
        }, 2500);
        return () => clearTimeout(timer);
    }, []);

    return (
        <AnimatePresence>
            {isLoading && (
                <motion.div
                    initial={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                    className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#050507]"
                >
                    <div className="text-center">
                        {/* Animated Shield - matching vanilla 100px size */}
                        <div className="w-[100px] h-[100px] mx-auto mb-5">
                            <svg viewBox="0 0 100 100" className="w-full h-full">
                                <defs>
                                    <linearGradient id="shieldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                        <stop offset="0%" stopColor="#6366f1" />
                                        <stop offset="100%" stopColor="#8b5cf6" />
                                    </linearGradient>
                                </defs>
                                {/* Shield path with draw animation - matching vanilla 2s duration */}
                                <motion.path
                                    d="M50 5 L90 20 L90 50 C90 75 50 95 50 95 C50 95 10 75 10 50 L10 20 Z"
                                    fill="none"
                                    stroke="url(#shieldGradient)"
                                    strokeWidth="3"
                                    initial={{ pathLength: 0 }}
                                    animate={{ pathLength: 1 }}
                                    transition={{ duration: 2, ease: 'easeInOut' }}
                                />
                                {/* Checkmark with delayed draw - matching vanilla 0.5s at 1.5s delay */}
                                <motion.path
                                    d="M30 50 L45 65 L70 35"
                                    fill="none"
                                    stroke="#10b981"
                                    strokeWidth="4"
                                    strokeLinecap="round"
                                    initial={{ pathLength: 0 }}
                                    animate={{ pathLength: 1 }}
                                    transition={{ duration: 0.5, delay: 1.5, ease: 'easeInOut' }}
                                />
                            </svg>
                        </div>
                        {/* Loading text - matching vanilla pulse animation */}
                        <motion.p
                            className="text-white/70 font-medium"
                            style={{ fontFamily: 'var(--font-display)' }}
                            animate={{ opacity: [0.6, 1, 0.6] }}
                            transition={{ duration: 1, repeat: Infinity }}
                        >
                            Initializing Shield...
                        </motion.p>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
