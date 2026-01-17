'use client';

import { DemoSection } from '@/components/landing/DemoSection';
import { Footer } from '@/components/landing/CTA';
import { Navbar } from '@/components/ui/Navbar';

export default function DemoPage() {
    return (
        <div className="min-h-screen" style={{ paddingTop: '72px' }}>
            <Navbar />
            <DemoSection />
            <Footer />
        </div>
    );
}
