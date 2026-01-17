'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';

export function FloatingShield() {
    const meshRef = useRef<THREE.Mesh>(null);

    useFrame((state) => {
        if (!meshRef.current) return;

        // Gentle rotation
        meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
        meshRef.current.rotation.x = Math.cos(state.clock.elapsedTime * 0.2) * 0.05;
    });

    return (
        <Float
            speed={2}
            rotationIntensity={0.3}
            floatIntensity={0.5}
        >
            <group ref={meshRef}>
                {/* Shield shape using custom geometry */}
                <mesh position={[0, 0, 0]}>
                    <shapeGeometry args={[createShieldShape()]} />
                    <MeshDistortMaterial
                        color="#6366f1"
                        distort={0.1}
                        speed={2}
                        roughness={0.2}
                        metalness={0.8}
                    />
                </mesh>

                {/* Inner glow */}
                <mesh position={[0, 0, 0.1]} scale={0.9}>
                    <shapeGeometry args={[createShieldShape()]} />
                    <meshBasicMaterial
                        color="#8b5cf6"
                        transparent
                        opacity={0.3}
                    />
                </mesh>

                {/* Checkmark */}
                <mesh position={[0, -0.2, 0.2]}>
                    <boxGeometry args={[0.6, 0.15, 0.1]} />
                    <meshStandardMaterial color="#10b981" emissive="#10b981" emissiveIntensity={0.5} />
                </mesh>
                <mesh position={[-0.15, 0.1, 0.2]} rotation={[0, 0, Math.PI / 4]}>
                    <boxGeometry args={[0.4, 0.15, 0.1]} />
                    <meshStandardMaterial color="#10b981" emissive="#10b981" emissiveIntensity={0.5} />
                </mesh>
            </group>
        </Float>
    );
}

function createShieldShape(): THREE.Shape {
    const shape = new THREE.Shape();

    // Shield outline
    shape.moveTo(0, 2);
    shape.bezierCurveTo(1.5, 1.8, 2, 1, 2, 0);
    shape.bezierCurveTo(2, -1.5, 0, -2.5, 0, -2.5);
    shape.bezierCurveTo(0, -2.5, -2, -1.5, -2, 0);
    shape.bezierCurveTo(-2, 1, -1.5, 1.8, 0, 2);

    return shape;
}
