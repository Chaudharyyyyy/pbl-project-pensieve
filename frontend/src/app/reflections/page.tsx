'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { Brain, Calendar, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { ReflectionCard } from '@/components/ReflectionCard';
import { Navigation } from '@/components/Navigation';

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

export default function ReflectionsPage() {
  const [reflections, setReflections] = useState<Reflection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const fetchReflections = async () => {
      try {
        const data = await api.getReflections(page, 10);
        setReflections(data.reflections);
        setTotal(data.total);
      } catch (error) {
        console.error('Failed to fetch reflections:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchReflections();
  }, [page]);

  const handleDismiss = async (reflectionId: string) => {
    try {
      await api.dismissReflection(reflectionId);
      setReflections(reflections.filter(r => r.id !== reflectionId));
    } catch (error) {
      console.error('Failed to dismiss reflection:', error);
    }
  };

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 pt-24 pb-12">
        <main className="max-w-4xl mx-auto px-6">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
              <Brain className="w-8 h-8 text-indigo-600" />
              Your Reflections
            </h1>
            <p className="mt-2 text-slate-600">
              Insights generated from your journal patterns over time
            </p>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            </div>
          )}

          {/* Empty State */}
          {!isLoading && reflections.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-20"
            >
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
                <Brain className="w-10 h-10 text-indigo-600" />
              </div>
              <h3 className="text-xl font-semibold text-slate-800 mb-2">
                No reflections yet
              </h3>
              <p className="text-slate-600 max-w-md mx-auto">
                Keep journaling! Reflections are generated after you have at least 3 entries 
                spanning 7 or more days.
              </p>
            </motion.div>
          )}

          {/* Reflections List */}
          <AnimatePresence mode="popLayout">
            {reflections.map((reflection, index) => (
              <motion.div
                key={reflection.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: index * 0.1 }}
                className="mb-6"
              >
                <div className="text-sm text-slate-500 mb-2 flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  {format(new Date(reflection.created_at), 'MMMM d, yyyy')}
                </div>
                <ReflectionCard
                  reflection={reflection}
                  brainState="idle"
                  onDismiss={() => handleDismiss(reflection.id)}
                />
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Pagination */}
          {total > 10 && (
            <div className="flex items-center justify-center gap-4 mt-8">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 rounded-lg bg-white border border-slate-200 text-slate-600
                         hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <span className="text-slate-600">
                Page {page} of {Math.ceil(total / 10)}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page >= Math.ceil(total / 10)}
                className="px-4 py-2 rounded-lg bg-white border border-slate-200 text-slate-600
                         hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
