'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ExternalLink, X, Lightbulb, ArrowRight } from 'lucide-react';
import { HolographicBrain, type BrainState } from './HolographicBrain';

interface Concept {
  id: string;
  name: string;
  description: string;
  source: string;
  relevance_score: number;
}

interface ReflectionMetadata {
  entries_analyzed: number;
  date_range: string;
  concepts: Concept[];
  confidence: string;
  confidence_score: number;
}

interface Reflection {
  id: string;
  content: string;
  metadata: ReflectionMetadata;
  disclaimer: string;
  created_at: string;
}

interface Props {
  reflection: Reflection;
  brainState?: BrainState;
  onDismiss: () => void;
}

export function ReflectionCard({ reflection, brainState = 'speaking', onDismiss }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Confidence visualization
  const confidenceLevel = 
    reflection.metadata.confidence === 'high' ? 4 :
    reflection.metadata.confidence === 'moderate' ? 3 : 2;

  // Type-out animation for text
  const textVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.008,
      },
    },
  };

  const charVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  };

  return (
    <motion.div
      layout
      className="reflection-card"
      initial={{ opacity: 0, y: 20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5, ease: [0.19, 1, 0.22, 1] }}
    >
      {/* Header with Brain */}
      <div className="reflection-header">
        <div className="reflection-brain">
          <HolographicBrain state={brainState} size="small" patterns={3} />
        </div>
        
        <div className="reflection-content">
          {/* Meta info */}
          <div className="flex items-center justify-between mb-3">
            <div className="text-caption flex items-center gap-2">
              <span>Based on {reflection.metadata.entries_analyzed} entries</span>
              <span className="text-tertiary">•</span>
              <span>{reflection.metadata.date_range}</span>
            </div>
            
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={onDismiss}
              className="p-1.5 rounded-full hover:bg-black/5 transition-colors"
              aria-label="Dismiss reflection"
            >
              <X size={16} className="text-tertiary" />
            </motion.button>
          </div>

          {/* Reflection content with typewriter effect */}
          <motion.p
            className="reflection-text"
            variants={textVariants}
            initial="hidden"
            animate="visible"
          >
            {reflection.content.split('').map((char, i) => (
              <motion.span key={i} variants={charVariants}>
                {char}
              </motion.span>
            ))}
          </motion.p>
        </div>
      </div>

      {/* Expandable "Why this insight?" section */}
      <div className="reflection-expand">
        <motion.button
          className="reflection-expand-trigger"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
        >
          <span className="flex items-center gap-2">
            <Lightbulb size={16} />
            Why this insight?
          </span>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.3 }}
          >
            <ChevronDown size={16} />
          </motion.div>
        </motion.button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: [0.19, 1, 0.22, 1] }}
              className="overflow-hidden"
            >
              <div className="reflection-expand-content">
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-primary mb-2">
                      This reflection draws from:
                    </h4>
                    <ul className="space-y-1 text-caption">
                      <li>• Your recent journal entries</li>
                      <li>• Detected emotional patterns</li>
                      <li>• Recurring themes in your writing</li>
                    </ul>
                  </div>

                  {reflection.metadata.concepts.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-primary mb-2">
                        Related concepts:
                      </h4>
                      {reflection.metadata.concepts.map((concept) => (
                        <div
                          key={concept.id}
                          className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg mb-2"
                        >
                          <div className="font-medium text-accent-insight text-sm">
                            {concept.name}
                          </div>
                          <div className="text-xs text-tertiary mt-1">
                            {concept.description}
                          </div>
                          <div className="text-xs text-tertiary mt-2 italic">
                            Source: {concept.source}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Concept Tags */}
      {reflection.metadata.concepts.length > 0 && (
        <motion.div className="concept-tags">
          {reflection.metadata.concepts.slice(0, 3).map((concept, i) => (
            <motion.a
              key={concept.id}
              href={`/concepts/${concept.id}`}
              className="concept-tag"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + i * 0.1 }}
              whileHover={{ scale: 1.03 }}
            >
              {concept.name}
              <ArrowRight size={14} />
            </motion.a>
          ))}
        </motion.div>
      )}

      {/* Metadata Footer */}
      <div className="reflection-meta">
        <span>Confidence:</span>
        <div className="confidence-dots">
          {[1, 2, 3, 4, 5].map((level) => (
            <div
              key={level}
              className={`confidence-dot ${level <= confidenceLevel ? 'active' : ''}`}
            />
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <p className="disclaimer">
        {reflection.disclaimer}
      </p>
    </motion.div>
  );
}

export default ReflectionCard;
