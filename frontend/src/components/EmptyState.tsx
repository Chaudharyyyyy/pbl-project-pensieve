'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import { HolographicBrain } from './HolographicBrain';

type EmptyStateType = 'welcome' | 'building' | 'ongoing' | 'inactive';

interface EmptyStateProps {
  type: EmptyStateType;
  entryCount?: number;
  streak?: number;
  lastEntryDays?: number;
  onStartWriting?: () => void;
}

export function EmptyState({
  type,
  entryCount = 0,
  streak = 0,
  lastEntryDays = 0,
  onStartWriting,
}: EmptyStateProps) {
  const content = getContent(type, entryCount, streak, lastEntryDays);

  return (
    <motion.div
      className="empty-state"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.19, 1, 0.22, 1] }}
    >
      {/* Brain Animation */}
      <motion.div
        className="empty-state-brain"
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 1, ease: [0.19, 1, 0.22, 1], delay: 0.2 }}
      >
        <HolographicBrain
          state={content.brainState}
          size="large"
          patterns={content.patterns}
        />
      </motion.div>

      {/* Streak Badge (if applicable) */}
      {streak > 0 && (
        <motion.div
          className="streak-badge"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.5, type: 'spring', stiffness: 200 }}
        >
          🔥 {streak}-day streak
        </motion.div>
      )}

      {/* Title */}
      <motion.h2
        className="empty-state-title"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        {content.title}
      </motion.h2>

      {/* Description */}
      <motion.p
        className="empty-state-text"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        {content.description}
      </motion.p>

      {/* Progress indicators for building state */}
      {type === 'building' && (
        <motion.div
          className="flex items-center gap-2 mb-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className={`w-3 h-3 rounded-full ${
                i <= entryCount
                  ? 'bg-accent-primary'
                  : 'bg-gray-200 dark:bg-gray-700'
              }`}
            />
          ))}
          <span className="text-small ml-2">
            {entryCount}/3 entries for first reflection
          </span>
        </motion.div>
      )}

      {/* Pattern preview for ongoing state */}
      {type === 'ongoing' && (
        <motion.div
          className="w-full max-w-sm bg-gray-50 dark:bg-gray-800/50 rounded-xl p-4 mb-6 text-left"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h4 className="text-caption font-medium mb-3 flex items-center gap-2">
            <Sparkles size={14} className="text-accent-warning" />
            Recent patterns
          </h4>
          <ul className="space-y-2 text-small">
            <li>• Your writing is more future-focused</li>
            <li>• Themes of growth appearing more</li>
            <li>• Emotional range expanding</li>
          </ul>
        </motion.div>
      )}

      {/* CTA Button */}
      <motion.button
        className="empty-state-cta"
        onClick={onStartWriting}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        whileHover={{ scale: 1.02, y: -2 }}
        whileTap={{ scale: 0.98 }}
      >
        {content.ctaText}
        <ArrowRight size={18} />
      </motion.button>
    </motion.div>
  );
}

function getContent(
  type: EmptyStateType,
  entryCount: number,
  streak: number,
  lastEntryDays: number
) {
  switch (type) {
    case 'welcome':
      return {
        title: 'Welcome to Pensieve',
        description:
          "This is your space for reflection. Write freely—I'll help you notice patterns over time.",
        ctaText: 'Start your first entry',
        brainState: 'idle' as const,
        patterns: 0,
      };

    case 'building':
      return {
        title: `You've written ${entryCount} ${
          entryCount === 1 ? 'entry' : 'entries'
        } so far`,
        description:
          "I'm starting to learn your patterns. A few more entries and I'll share my first reflection.",
        ctaText: 'Continue writing',
        brainState: 'listening' as const,
        patterns: entryCount * 2,
      };

    case 'ongoing':
      return {
        title: streak > 0 ? `${streak}-day streak` : "Welcome back",
        description:
          "You've been building a rich picture of your inner world. Let's continue today.",
        ctaText: "Write today's entry",
        brainState: 'idle' as const,
        patterns: 20 + streak,
      };

    case 'inactive':
      return {
        title: "I've missed you",
        description: `Your last entry was ${lastEntryDays} days ago. There's no pressure—I'm here whenever you're ready.`,
        ctaText: 'Pick up where you left off',
        brainState: 'idle' as const,
        patterns: 10,
      };

    default:
      return {
        title: 'Welcome',
        description: 'Start writing to begin your journey.',
        ctaText: 'Start writing',
        brainState: 'idle' as const,
        patterns: 0,
      };
  }
}

export default EmptyState;
