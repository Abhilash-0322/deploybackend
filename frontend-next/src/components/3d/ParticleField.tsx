'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ParticleFieldProps {
    count?: number;
    color?: string;
}

export function ParticleField({ count = 2000, color = '#6366f1' }: ParticleFieldProps) {
    const points = useRef<THREE.Points>(null);

    const particles = useMemo(() => {
        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);

        const baseColor = new THREE.Color(color);
        const accentColor = new THREE.Color('#22d3ee');

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;

            // Spread particles in a sphere
            const radius = 50 + Math.random() * 50;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);

            positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i3 + 2] = radius * Math.cos(phi);

            // Mix colors
            const mixColor = baseColor.clone().lerp(accentColor, Math.random() * 0.3);
            colors[i3] = mixColor.r;
            colors[i3 + 1] = mixColor.g;
            colors[i3 + 2] = mixColor.b;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        return geometry;
    }, [count, color]);

    useFrame((state) => {
        if (!points.current) return;

        points.current.rotation.y += 0.0003;
        points.current.rotation.x += 0.0001;

        // Subtle floating motion
        points.current.position.y = Math.sin(state.clock.elapsedTime * 0.2) * 0.5;
    });

    return (
        <points ref={points} geometry={particles}>
            <pointsMaterial
                size={0.15}
                vertexColors
                transparent
                opacity={0.8}
                sizeAttenuation
                blending={THREE.AdditiveBlending}
            />
        </points>
    );
}
