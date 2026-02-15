'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { Feather, Check } from 'lucide-react';
import { BrainOrb, type BrainState } from '@/components/HolographicBrain';
import { ReflectionCard } from '@/components/ReflectionCard';
import { EmptyState } from '@/components/EmptyState';
import { Navigation } from '@/components/Navigation';

interface Entry {
  id: string;
  content: string;
  entry_date: string;
  word_count: number;
}

interface Reflection {
  id: string;
  content: string;
  metadata: {
    entries_analyzed: number;
    date_range: string;
    concepts: Array<{
      id: string;
      name: string;
      description: string;
      source: string;
      relevance_score: number;
    }>;
    confidence: string;
    confidence_score: number;
  };
  disclaimer: string;
  created_at: string;
}

export default function JournalPage() {
  // State
  const [content, setContent] = useState('');
  const [entryId, setEntryId] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [wordCount, setWordCount] = useState(0);
  const [reflections, setReflections] = useState<Reflection[]>([]);
  const [brainState, setBrainState] = useState<BrainState>('idle');
  const [brainExpanded, setBrainExpanded] = useState(false);
  const [entryCount, setEntryCount] = useState(0);
  const [streak, setStreak] = useState(0);
  const [isFirstVisit, setIsFirstVisit] = useState(true);
  const [patterns, setPatterns] = useState(0);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Word count tracking
  useEffect(() => {
    const words = content.trim().split(/\s+/).filter(Boolean);
    setWordCount(words.length);
    
    // Brain responds to writing milestones
    if (words.length > 0 && words.length % 50 === 0) {
      setBrainState('listening');
      setTimeout(() => setBrainState('idle'), 500);
    }
  }, [content]);

  // Typing detection for brain state
  useEffect(() => {
    if (content.length > 0) {
      setBrainState('listening');
      
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      
      typingTimeoutRef.current = setTimeout(() => {
        setBrainState('idle');
      }, 2000);
    }
    
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [content]);

  // Autosave with debounce
  const autosave = useCallback(async () => {
    if (!content.trim()) return;

    setSaveStatus('saving');

    try {
      const response = await fetch('/api/entries/autosave', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          entry_id: entryId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setEntryId(data.entry_id);
        setSaveStatus('saved');
        setIsFirstVisit(false);
        setEntryCount(prev => prev + 1);

        setTimeout(() => setSaveStatus('idle'), 2000);
      }
    } catch (error) {
      console.error('Autosave failed:', error);
      setSaveStatus('idle');
    }
  }, [content, entryId]);

  // Debounced autosave trigger
  useEffect(() => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    if (content.trim()) {
      saveTimeoutRef.current = setTimeout(autosave, 3000);
    }

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [content, autosave]);

  // Fetch reflections
  useEffect(() => {
    const fetchReflections = async () => {
      if (entryCount < 3) return;
      
      try {
        setBrainState('thinking');
        const response = await fetch('/api/reflections/suggest');
        
        if (response.ok) {
          const data = await response.json();
          if (data.reflections?.length > 0) {
            setBrainState('speaking');
            setReflections(data.reflections);
            setPatterns(prev => prev + 1);
            setTimeout(() => setBrainState('idle'), 3000);
          } else {
            setBrainState('idle');
          }
        }
      } catch (error) {
        console.error('Failed to fetch reflections:', error);
        setBrainState('idle');
      }
    };

    const timer = setTimeout(fetchReflections, 2000);
    return () => clearTimeout(timer);
  }, [entryCount]);

  const handleDismissReflection = async (reflectionId: string) => {
    try {
      await fetch(`/api/reflections/${reflectionId}/dismiss`, { method: 'POST' });
      setReflections(reflections.filter(r => r.id !== reflectionId));
    } catch (error) {
      console.error('Failed to dismiss reflection:', error);
    }
  };

  const handleBrainClick = () => {
    setBrainExpanded(!brainExpanded);
  };

  // Determine time of day for background
  const getTimeOfDayClass = () => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return 'morning';
    if (hour >= 12 && hour < 17) return 'afternoon';
    if (hour >= 17 && hour < 21) return 'evening';
    return 'night';
  };

  return (
    <div className={`min-h-screen time-${getTimeOfDayClass()}`}>
      {/* Header */}
      <header className="app-header">
        <div className="app-logo">
          <Feather className="app-logo-icon" />
          <span>Pensieve</span>
        </div>

        <div className="header-meta">
          <span>{format(new Date(), 'EEEE, MMMM d')}</span>
          {streak > 0 && (
            <span className="streak-badge">
              🔥 {streak}-day streak
            </span>
          )}
        </div>
      </header>

      {/* Brain Orb */}
      <BrainOrb
        state={brainState}
        expanded={brainExpanded}
        onClick={handleBrainClick}
        patterns={patterns}
      />

      {/* Expanded brain overlay */}
      <AnimatePresence>
        {brainExpanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[999]"
            onClick={() => setBrainExpanded(false)}
          />
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="max-w-[var(--content-max-width)] mx-auto px-6 py-8">
        {/* Empty State or Journal */}
        {isFirstVisit && content.length === 0 ? (
          <EmptyState
            type="welcome"
            onStartWriting={() => textareaRef.current?.focus()}
          />
        ) : (
          <>
            {/* Journal Editor */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0.19, 1, 0.22, 1] }}
              className="journal-container"
            >
              <textarea
                ref={textareaRef}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Start writing..."
                className="journal-editor"
                autoFocus={!isFirstVisit}
              />
              <div className="word-count">{wordCount} words</div>
            </motion.div>

            {/* Reflections */}
            <AnimatePresence mode="popLayout">
              {reflections.map((reflection, index) => (
                <motion.div
                  key={reflection.id}
                  initial={{ opacity: 0, y: 30, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95, y: -20 }}
                  transition={{
                    duration: 0.5,
                    delay: index * 0.1,
                    ease: [0.19, 1, 0.22, 1],
                  }}
                  className="mt-8"
                >
                  <ReflectionCard
                    reflection={reflection}
                    brainState="speaking"
                    onDismiss={() => handleDismissReflection(reflection.id)}
                  />
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Building momentum state */}
            {entryCount > 0 && entryCount < 3 && reflections.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-12"
              >
                <EmptyState
                  type="building"
                  entryCount={entryCount}
                />
              </motion.div>
            )}
          </>
        )}
      </main>

      {/* Autosave Indicator */}
      <div className={`autosave-indicator ${saveStatus !== 'idle' ? 'visible' : ''} ${saveStatus}`}>
        {saveStatus === 'saving' && (
          <>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
              </svg>
            </motion.div>
            Saving...
          </>
        )}
        {saveStatus === 'saved' && (
          <>
            <Check size={16} />
            Saved
          </>
        )}
      </div>
    </div>
  );
}
