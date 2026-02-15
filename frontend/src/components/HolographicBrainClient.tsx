'use client';

import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { MeshDistortMaterial, Sphere, Float, Stars } from '@react-three/drei';
import * as THREE from 'three';

export type BrainState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'growing';

interface HolographicBrainProps {
  state?: BrainState;
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
  patterns?: number;
}

// Neural pathway particle system
function NeuralParticles({ state, count = 100 }: { state: BrainState; count?: number }) {
  const particlesRef = useRef<THREE.Points>(null);
  
  const particlePositions = useMemo(() => {
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 1.2 + Math.random() * 0.3;
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
    }
    return positions;
  }, [count]);

  useFrame((_, delta) => {
    if (!particlesRef.current) return;
    const speed = state === 'thinking' ? 0.5 : state === 'listening' ? 0.2 : 0.05;
    particlesRef.current.rotation.y += delta * speed;
    particlesRef.current.rotation.x += delta * speed * 0.3;
  });

  const particleColor = useMemo(() => {
    switch (state) {
      case 'thinking': return '#FFB88C';
      case 'speaking': return '#B490F5';
      case 'listening': return '#4FACFE';
      default: return '#E8EFFF';
    }
  }, [state]);

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[particlePositions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.03}
        color={particleColor}
        transparent
        opacity={state === 'thinking' ? 0.9 : 0.5}
        sizeAttenuation
      />
    </points>
  );
}

// Main brain sphere
function BrainSphere({ state }: { state: BrainState }) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  const distortParams = useMemo(() => {
    switch (state) {
      case 'thinking': return { distort: 0.5, speed: 4 };
      case 'listening': return { distort: 0.35, speed: 2 };
      case 'speaking': return { distort: 0.4, speed: 1.5 };
      case 'growing': return { distort: 0.6, speed: 3 };
      default: return { distort: 0.3, speed: 1 };
    }
  }, [state]);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const breathe = 1 + Math.sin(clock.getElapsedTime() * 0.8) * 0.02;
    meshRef.current.scale.setScalar(breathe);
  });

  return (
    <Float
      speed={state === 'idle' ? 1 : 2}
      rotationIntensity={state === 'thinking' ? 0.5 : 0.2}
      floatIntensity={state === 'thinking' ? 0.5 : 0.2}
    >
      <Sphere ref={meshRef} args={[1, 64, 64]}>
        <MeshDistortMaterial
          color="#E8EFFF"
          attach="material"
          distort={distortParams.distort}
          speed={distortParams.speed}
          roughness={0.1}
          metalness={0.1}
          transparent
          opacity={0.7}
        />
      </Sphere>
      
      <Sphere args={[0.85, 32, 32]}>
        <meshBasicMaterial
          color={state === 'thinking' ? '#FFB88C' : '#4FACFE'}
          transparent
          opacity={0.15}
        />
      </Sphere>
    </Float>
  );
}

// Complete brain scene
function BrainScene({ state }: { state: BrainState }) {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame((_, delta) => {
    if (!groupRef.current) return;
    const rotationSpeed = state === 'thinking' ? 0.2 : 
                          state === 'listening' ? 0.1 : 0.02;
    groupRef.current.rotation.y += delta * rotationSpeed;
  });

  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={0.5} color="#4FACFE" />
      <pointLight position={[-10, -10, -10]} intensity={0.3} color="#B490F5" />
      
      <group ref={groupRef}>
        <BrainSphere state={state} />
        <NeuralParticles state={state} count={150} />
      </group>
      
      <Stars
        radius={50}
        depth={50}
        count={300}
        factor={2}
        saturation={0}
        fade
        speed={0.5}
      />
    </>
  );
}

// Main exported component
export function HolographicBrain({
  state = 'idle',
  size = 'medium',
  onClick,
}: HolographicBrainProps) {
  const sizeMap = {
    small: 60,
    medium: 150,
    large: 300,
  };
  
  const dimension = sizeMap[size];

  return (
    <div
      style={{
        width: dimension,
        height: dimension,
        cursor: onClick ? 'pointer' : 'default',
        position: 'relative',
      }}
      onClick={onClick}
    >
      <Canvas
        camera={{ position: [0, 0, 3.5], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <BrainScene state={state} />
      </Canvas>
      
      {/* Glow effect overlay */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '80%',
          height: '80%',
          borderRadius: '50%',
          background: `radial-gradient(circle, 
            ${state === 'thinking' ? 'rgba(255, 184, 140, 0.15)' : 'rgba(79, 172, 254, 0.1)'} 0%, 
            transparent 70%)`,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
}

// Orb wrapper for positioning
export function BrainOrb({
  state = 'idle',
  minimized = false,
  expanded = false,
  onClick,
  patterns = 0,
}: {
  state?: BrainState;
  minimized?: boolean;
  expanded?: boolean;
  onClick?: () => void;
  patterns?: number;
}) {
  const containerClasses = [
    'brain-orb-container',
    minimized && 'minimized',
    expanded && 'expanded',
  ].filter(Boolean).join(' ');

  return (
    <div className={containerClasses} onClick={onClick}>
      <HolographicBrain
        state={state}
        size={minimized ? 'small' : expanded ? 'large' : 'medium'}
      />
    </div>
  );
}

export default HolographicBrain;
