'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Menu, X } from 'lucide-react';

const navLinks = [
    { href: '/#features', label: 'Features' },
    { href: '/#demo', label: 'Demo' },
    { href: '/#tech', label: 'Technology' },
];

export function Navbar() {
    const [scrolled, setScrolled] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const pathname = usePathname();

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 100);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <>
            {/* Navigation - matching vanilla px-60, py-20 */}
            <motion.nav
                initial={{ y: -100 }}
                animate={{ y: 0 }}
                transition={{ duration: 0.6, ease: [0.25, 0.4, 0.25, 1] }}
                className={`fixed top-0 left-0 right-0 z-[100] transition-all duration-300 ${scrolled
                        ? 'bg-[rgba(5,5,7,0.9)] backdrop-blur-[20px] py-[15px] px-[60px] border-b border-primary/10'
                        : 'bg-transparent py-5 px-[60px]'
                    }`}
            >
                <div className="flex items-center justify-between">
                    {/* Logo - matching vanilla */}
                    <Link href="/" className="flex items-center gap-3">
                        <div
                            className="w-10 h-10 rounded-[10px] bg-gradient-to-br from-primary to-violet-600 flex items-center justify-center"
                            style={{ boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)' }}
                        >
                            <Shield className="w-[22px] h-[22px] text-white" />
                        </div>
                        <span
                            className="font-semibold text-[1.25rem] text-white"
                            style={{ fontFamily: 'var(--font-display)' }}
                        >
                            Aptos Shield
                        </span>
                    </Link>

                    {/* Desktop Links - matching vanilla 40px gap */}
                    <div className="hidden md:flex items-center gap-10">
                        {navLinks.map((link) => (
                            <Link
                                key={link.href}
                                href={link.href}
                                className="text-[0.95rem] text-white/70 hover:text-white transition-colors duration-300"
                            >
                                {link.label}
                            </Link>
                        ))}
                        <Link
                            href="/dashboard"
                            className="px-6 py-2.5 bg-primary hover:bg-violet-600 text-white text-[0.95rem] font-medium rounded-lg transition-all duration-300 hover:-translate-y-0.5"
                            style={{ boxShadow: '0 4px 20px rgba(99, 102, 241, 0.4)' }}
                        >
                            Launch App
                        </Link>
                    </div>

                    {/* Mobile Menu Button */}
                    <button
                        onClick={() => setMobileOpen(!mobileOpen)}
                        className="md:hidden p-2 text-white"
                    >
                        {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                    </button>
                </div>
            </motion.nav>

            {/* Mobile Menu */}
            <AnimatePresence>
                {mobileOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="fixed inset-x-0 top-20 z-40 bg-[rgba(5,5,7,0.95)] backdrop-blur-xl border-b border-white/5 md:hidden"
                    >
                        <div className="p-6 space-y-4">
                            {navLinks.map((link) => (
                                <Link
                                    key={link.href}
                                    href={link.href}
                                    onClick={() => setMobileOpen(false)}
                                    className="block py-3 text-lg font-medium text-white/70 hover:text-white transition-colors"
                                >
                                    {link.label}
                                </Link>
                            ))}
                            <Link
                                href="/dashboard"
                                onClick={() => setMobileOpen(false)}
                                className="block w-full py-3 text-center bg-primary text-white font-semibold rounded-lg"
                            >
                                Launch App
                            </Link>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
