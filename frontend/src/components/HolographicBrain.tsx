'use client';

import dynamic from 'next/dynamic';
import { type BrainState } from './HolographicBrainClient';

// Dynamic import with no SSR to avoid Three.js hydration issues
const HolographicBrainClient = dynamic(
  () => import('./HolographicBrainClient').then((mod) => mod.HolographicBrain),
  {
    ssr: false,
    loading: () => (
      <div className="animate-pulse bg-gradient-to-br from-blue-100 to-purple-100 rounded-full" 
           style={{ width: '100%', height: '100%' }} />
    ),
  }
);

export type { BrainState };

interface HolographicBrainProps {
  state?: BrainState;
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
  patterns?: number;
}

export function HolographicBrain(props: HolographicBrainProps) {
  return <HolographicBrainClient {...props} />;
}

// Orb wrapper - also needs dynamic import
const BrainOrbClient = dynamic(
  () => import('./HolographicBrainClient').then((mod) => mod.BrainOrb),
  {
    ssr: false,
    loading: () => (
      <div className="brain-orb-container">
        <div className="animate-pulse bg-gradient-to-br from-blue-100 to-purple-100 rounded-full w-full h-full" />
      </div>
    ),
  }
);

export function BrainOrb(props: {
  state?: BrainState;
  minimized?: boolean;
  expanded?: boolean;
  onClick?: () => void;
  patterns?: number;
}) {
  return <BrainOrbClient {...props} />;
}

export default HolographicBrain;
