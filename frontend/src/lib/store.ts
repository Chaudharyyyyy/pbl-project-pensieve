/**
 * Pensieve Global State Store
 * 
 * Zustand store for auth state, entries, and reflections.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Types
interface User {
  id: string;
  email: string;
}

interface Entry {
  id: string;
  content: string;
  entry_date: string;
  word_count: number;
  created_at: string;
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

// Auth Store
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  login: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      login: (user) => set({ user, isAuthenticated: true }),
      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
        }
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'pensieve-auth',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

// Journal Store
interface JournalState {
  entries: Entry[];
  currentEntryId: string | null;
  currentContent: string;
  isSaving: boolean;
  lastSaved: Date | null;
  
  setEntries: (entries: Entry[]) => void;
  addEntry: (entry: Entry) => void;
  setCurrentEntryId: (id: string | null) => void;
  setCurrentContent: (content: string) => void;
  setIsSaving: (saving: boolean) => void;
  setLastSaved: (date: Date | null) => void;
  clearJournal: () => void;
}

export const useJournalStore = create<JournalState>()((set) => ({
  entries: [],
  currentEntryId: null,
  currentContent: '',
  isSaving: false,
  lastSaved: null,
  
  setEntries: (entries) => set({ entries }),
  addEntry: (entry) => set((state) => ({ 
    entries: [entry, ...state.entries.filter(e => e.id !== entry.id)] 
  })),
  setCurrentEntryId: (id) => set({ currentEntryId: id }),
  setCurrentContent: (content) => set({ currentContent: content }),
  setIsSaving: (saving) => set({ isSaving: saving }),
  setLastSaved: (date) => set({ lastSaved: date }),
  clearJournal: () => set({ 
    entries: [], 
    currentEntryId: null, 
    currentContent: '', 
    isSaving: false, 
    lastSaved: null 
  }),
}));

// Reflections Store
interface ReflectionState {
  reflections: Reflection[];
  isLoading: boolean;
  
  setReflections: (reflections: Reflection[]) => void;
  addReflection: (reflection: Reflection) => void;
  removeReflection: (id: string) => void;
  setIsLoading: (loading: boolean) => void;
  clearReflections: () => void;
}

export const useReflectionStore = create<ReflectionState>()((set) => ({
  reflections: [],
  isLoading: false,
  
  setReflections: (reflections) => set({ reflections }),
  addReflection: (reflection) => set((state) => ({ 
    reflections: [reflection, ...state.reflections] 
  })),
  removeReflection: (id) => set((state) => ({ 
    reflections: state.reflections.filter(r => r.id !== id) 
  })),
  setIsLoading: (loading) => set({ isLoading: loading }),
  clearReflections: () => set({ reflections: [], isLoading: false }),
}));

// Brain State Store
type BrainState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'growing';

interface BrainUIState {
  state: BrainState;
  expanded: boolean;
  patterns: number;
  
  setState: (state: BrainState) => void;
  setExpanded: (expanded: boolean) => void;
  incrementPatterns: () => void;
}

export const useBrainStore = create<BrainUIState>()((set) => ({
  state: 'idle',
  expanded: false,
  patterns: 0,
  
  setState: (state) => set({ state }),
  setExpanded: (expanded) => set({ expanded }),
  incrementPatterns: () => set((s) => ({ patterns: s.patterns + 1 })),
}));
