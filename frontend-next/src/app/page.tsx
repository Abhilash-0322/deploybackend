'use client';

import dynamic from 'next/dynamic';
import { Hero } from '@/components/landing/Hero';
import { Features } from '@/components/landing/Features';
import { DemoSection } from '@/components/landing/DemoSection';
import { TechStack } from '@/components/landing/TechStack';
import { CTA } from '@/components/landing/CTA';
import { LoadingScreen } from '@/components/landing/LoadingScreen';
import { Navbar } from '@/components/ui/Navbar';
import './landing.css';

// Dynamically import 3D scene to avoid SSR issues
const Scene = dynamic(
  () => import('@/components/3d/Scene').then((mod) => mod.Scene),
  { ssr: false }
);

export default function LandingPage() {
  return (
    <>
      {/* Loading Screen */}
      <LoadingScreen />

      {/* 3D Background */}
      <Scene showShield={false} />

      {/* Navigation */}
      <Navbar />

      {/* Content */}
      <Hero />
      <Features />
      <DemoSection />
      <TechStack />
      <CTA />
      
      {/* Footer */}
      <footer style={{
        padding: '40px 80px',
        textAlign: 'center',
        borderTop: '1px solid rgba(255, 255, 255, 0.05)',
        color: 'var(--text-muted)',
        fontSize: '0.9rem'
      }}>
        <p>Aptos Shield - Built for Hackathon 2026</p>
      </footer>
    </>
  );
}
