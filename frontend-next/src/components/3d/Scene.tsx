'use client';

import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, Preload } from '@react-three/drei';
import { ParticleField } from './ParticleField';
import { FloatingShield } from './FloatingShield';

interface SceneProps {
    showShield?: boolean;
    interactive?: boolean;
}

export function Scene({ showShield = true, interactive = false }: SceneProps) {
    return (
        <div className="absolute inset-0 -z-10">
            <Canvas
                camera={{ position: [0, 0, 30], fov: 60 }}
                dpr={[1, 2]}
                gl={{ antialias: true, alpha: true }}
            >
                <Suspense fallback={null}>
                    {/* Lighting */}
                    <ambientLight intensity={0.4} />
                    <pointLight position={[10, 10, 10]} intensity={1} color="#6366f1" />
                    <pointLight position={[-10, -10, -10]} intensity={0.5} color="#22d3ee" />

                    {/* Particle Background */}
                    <ParticleField count={1500} />

                    {/* Floating Shield */}
                    {showShield && (
                        <group position={[8, 0, 0]} scale={2}>
                            <FloatingShield />
                        </group>
                    )}

                    {/* Environment for reflections */}
                    <Environment preset="night" />

                    {/* Optional controls for development */}
                    {interactive && <OrbitControls enableZoom={false} enablePan={false} />}

                    <Preload all />
                </Suspense>
            </Canvas>
        </div>
    );
}
