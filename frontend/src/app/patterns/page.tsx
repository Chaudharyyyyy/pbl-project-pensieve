'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { format, subDays, eachDayOfInterval, isSameDay } from 'date-fns';
import { LineChart, Calendar, TrendingUp, Brain, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { Navigation } from '@/components/Navigation';

interface Entry {
  id: string;
  content: string;
  entry_date: string;
  word_count: number;
  created_at: string;
}

interface DayData {
  date: Date;
  hasEntry: boolean;
  wordCount: number;
}

export default function PatternsPage() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchEntries = async () => {
      try {
        const data = await api.getEntries(1, 100);
        setEntries(data.entries);
      } catch (error) {
        console.error('Failed to fetch entries:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEntries();
  }, []);

  // Generate last 30 days data
  const last30Days: DayData[] = eachDayOfInterval({
    start: subDays(new Date(), 29),
    end: new Date(),
  }).map(date => {
    const entry = entries.find(e => isSameDay(new Date(e.entry_date), date));
    return {
      date,
      hasEntry: !!entry,
      wordCount: entry?.word_count || 0,
    };
  });

  // Calculate stats
  const totalEntries = entries.length;
  const totalWords = entries.reduce((sum, e) => sum + (e.word_count || 0), 0);
  const avgWords = totalEntries > 0 ? Math.round(totalWords / totalEntries) : 0;
  const streakDays = calculateStreak(last30Days);

  function calculateStreak(days: DayData[]): number {
    let streak = 0;
    const reversed = [...days].reverse();
    for (const day of reversed) {
      if (day.hasEntry) {
        streak++;
      } else {
        break;
      }
    }
    return streak;
  }

  // Get max word count for scaling
  const maxWordCount = Math.max(...last30Days.map(d => d.wordCount), 1);

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 pt-24 pb-12">
        <main className="max-w-4xl mx-auto px-6">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
              <LineChart className="w-8 h-8 text-indigo-600" />
              Your Patterns
            </h1>
            <p className="mt-2 text-slate-600">
              Track your journaling habits and writing patterns
            </p>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            </div>
          ) : (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white rounded-xl p-5 shadow-sm border border-slate-100"
                >
                  <div className="text-sm text-slate-500 mb-1">Total Entries</div>
                  <div className="text-3xl font-bold text-slate-800">{totalEntries}</div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="bg-white rounded-xl p-5 shadow-sm border border-slate-100"
                >
                  <div className="text-sm text-slate-500 mb-1">Total Words</div>
                  <div className="text-3xl font-bold text-slate-800">{totalWords.toLocaleString()}</div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="bg-white rounded-xl p-5 shadow-sm border border-slate-100"
                >
                  <div className="text-sm text-slate-500 mb-1">Avg. Words/Entry</div>
                  <div className="text-3xl font-bold text-slate-800">{avgWords}</div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl p-5 shadow-sm text-white"
                >
                  <div className="text-sm text-white/80 mb-1">Current Streak</div>
                  <div className="text-3xl font-bold flex items-center gap-2">
                    {streakDays} 🔥
                  </div>
                </motion.div>
              </div>

              {/* Activity Heatmap */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 mb-8"
              >
                <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-indigo-600" />
                  Last 30 Days
                </h2>

                <div className="grid grid-cols-10 gap-2">
                  {last30Days.map((day, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.02 }}
                      className="relative group"
                    >
                      <div
                        className={`aspect-square rounded-lg transition-all ${
                          day.hasEntry
                            ? 'bg-gradient-to-br from-indigo-400 to-purple-500'
                            : 'bg-slate-100'
                        }`}
                        style={{
                          opacity: day.hasEntry ? 0.4 + (day.wordCount / maxWordCount) * 0.6 : 1,
                        }}
                      />
                      
                      {/* Tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 
                                    bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 
                                    transition-opacity pointer-events-none whitespace-nowrap z-10">
                        {format(day.date, 'MMM d')}
                        {day.hasEntry && ` • ${day.wordCount} words`}
                      </div>
                    </motion.div>
                  ))}
                </div>

                <div className="flex items-center justify-end gap-2 mt-4 text-xs text-slate-500">
                  <span>Less</span>
                  <div className="flex gap-1">
                    <div className="w-3 h-3 rounded bg-slate-100" />
                    <div className="w-3 h-3 rounded bg-indigo-200" />
                    <div className="w-3 h-3 rounded bg-indigo-400" />
                    <div className="w-3 h-3 rounded bg-indigo-600" />
                  </div>
                  <span>More</span>
                </div>
              </motion.div>

              {/* Word Count Chart */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="bg-white rounded-xl p-6 shadow-sm border border-slate-100"
              >
                <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-indigo-600" />
                  Word Count Trend
                </h2>

                <div className="h-40 flex items-end gap-1">
                  {last30Days.map((day, index) => (
                    <motion.div
                      key={index}
                      initial={{ height: 0 }}
                      animate={{ height: day.wordCount > 0 ? `${(day.wordCount / maxWordCount) * 100}%` : '4px' }}
                      transition={{ delay: index * 0.02, duration: 0.5 }}
                      className={`flex-1 rounded-t transition-colors ${
                        day.wordCount > 0
                          ? 'bg-gradient-to-t from-indigo-500 to-purple-400'
                          : 'bg-slate-100'
                      }`}
                    />
                  ))}
                </div>

                <div className="flex justify-between mt-2 text-xs text-slate-400">
                  <span>{format(subDays(new Date(), 29), 'MMM d')}</span>
                  <span>{format(new Date(), 'MMM d')}</span>
                </div>
              </motion.div>

              {/* Info Box */}
              {totalEntries < 3 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                  className="mt-8 p-6 rounded-xl bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-100"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-full bg-white shadow-sm">
                      <Brain className="w-6 h-6 text-indigo-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-800 mb-1">
                        Keep writing to unlock insights
                      </h3>
                      <p className="text-sm text-slate-600">
                        After 3+ entries over 7+ days, Pensieve will analyze your patterns 
                        and generate personalized reflections grounded in psychological research.
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </>
          )}
        </main>
      </div>
    </>
  );
}
