-- Pensieve Database Schema
-- PostgreSQL 15+ with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================
-- USERS TABLE (Authentication Only)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    encryption_key_salt BYTEA NOT NULL,  -- Salt for deriving encryption key
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for email lookups
CREATE INDEX idx_users_email ON users(email);

-- ============================================
-- ENCRYPTED JOURNAL ENTRIES
-- ============================================
CREATE TABLE entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_content BYTEA NOT NULL,      -- AES-256-GCM encrypted content
    encryption_iv BYTEA NOT NULL,          -- Initialization vector
    auth_tag BYTEA NOT NULL,               -- GCM authentication tag
    entry_date DATE NOT NULL,
    word_count INTEGER,                    -- Metadata only, no content
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient user queries
CREATE INDEX idx_entries_user_id ON entries(user_id);
CREATE INDEX idx_entries_user_date ON entries(user_id, entry_date DESC);

-- ============================================
-- PATTERN METADATA (No Raw Text)
-- ============================================
CREATE TABLE pattern_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entry_ids UUID[] NOT NULL,             -- Which entries contributed
    pattern_type TEXT NOT NULL,            -- 'emotion', 'theme', 'linguistic', 'temporal'
    metadata JSONB NOT NULL,               -- Pattern-specific data
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_pattern_type CHECK (
        pattern_type IN ('emotion', 'theme', 'linguistic', 'temporal')
    )
);

-- Index for pattern queries
CREATE INDEX idx_patterns_user_type ON pattern_metadata(user_id, pattern_type);
CREATE INDEX idx_patterns_detected ON pattern_metadata(user_id, detected_at DESC);

-- ============================================
-- GENERATED REFLECTIONS
-- ============================================
CREATE TABLE reflections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,                 -- Plain text reflection (not user content)
    metadata JSONB NOT NULL,               -- Confidence, sources, concepts used
    entry_ids UUID[] NOT NULL,             -- Entries analyzed
    date_range_start DATE NOT NULL,
    date_range_end DATE NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score <= 0.80),  -- Hard cap at 80%
    created_at TIMESTAMPTZ DEFAULT NOW(),
    dismissed_at TIMESTAMPTZ,              -- User dismissed this reflection
    
    -- Ensure minimum entry threshold
    CONSTRAINT min_entries CHECK (array_length(entry_ids, 1) >= 3)
);

-- Index for reflection queries
CREATE INDEX idx_reflections_user ON reflections(user_id, created_at DESC);

-- ============================================
-- THEORY/CONCEPT DATABASE (Global, Read-Only)
-- ============================================
CREATE TABLE concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    category TEXT NOT NULL,                -- 'psychology', 'philosophy', 'research'
    subcategory TEXT,                      -- More specific classification
    description TEXT NOT NULL,
    source_citation TEXT NOT NULL,
    source_year INTEGER,
    tags TEXT[] DEFAULT '{}',
    embedding VECTOR(384) NOT NULL,        -- Sentence-BERT embedding
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_category CHECK (
        category IN ('psychology', 'philosophy', 'research')
    )
);

-- Vector similarity index for RAG
CREATE INDEX idx_concepts_embedding ON concepts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Text search index
CREATE INDEX idx_concepts_name ON concepts(name);
CREATE INDEX idx_concepts_category ON concepts(category);

-- ============================================
-- AUDIT LOG (Transparency)
-- ============================================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,                  -- 'entry_created', 'reflection_generated', etc.
    entity_type TEXT NOT NULL,             -- 'entry', 'reflection', 'pattern'
    entity_id UUID,
    metadata JSONB DEFAULT '{}',           -- Action-specific details (NO content)
    model_version TEXT,                    -- ML model version if applicable
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for audit queries
CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_log(action, created_at DESC);

-- ============================================
-- SESSION MANAGEMENT
-- ============================================
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,              -- Hashed session token
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for session lookups
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- ============================================
-- USER PREFERENCES
-- ============================================
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    reflection_frequency TEXT DEFAULT 'normal',  -- 'low', 'normal', 'high'
    theme TEXT DEFAULT 'system',                 -- 'light', 'dark', 'system'
    notification_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_frequency CHECK (
        reflection_frequency IN ('low', 'normal', 'high')
    )
);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_entries_updated_at
    BEFORE UPDATE ON entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- SECURITY POLICIES (Row Level Security)
-- ============================================

-- Enable RLS
ALTER TABLE entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE pattern_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE reflections ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Note: Policies would be created per application role
-- Example policy (implement based on your auth strategy):
-- CREATE POLICY entries_user_policy ON entries
--     FOR ALL TO authenticated_user
--     USING (user_id = current_user_id());
