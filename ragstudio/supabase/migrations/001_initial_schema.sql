-- RAG Studio Supabase Schema
-- Core tables for authentication, devices, jobs, and metadata

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS & PROFILES
-- ============================================

CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security for profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- ============================================
-- DEVICES
-- ============================================

CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    device_uuid UUID UNIQUE NOT NULL,
    name TEXT NOT NULL,
    os TEXT,
    cpu TEXT,
    ram_gb INTEGER,
    gpu TEXT,
    status TEXT DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'busy', 'error')),
    last_heartbeat TIMESTAMPTZ,
    software_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_devices_user_id ON devices(user_id);
CREATE INDEX idx_devices_status ON devices(status);

ALTER TABLE devices ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own devices" ON devices
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own devices" ON devices
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own devices" ON devices
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- BOOKS
-- ============================================

CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    author TEXT,
    file_path TEXT, -- Local path on device
    file_size BIGINT,
    page_count INTEGER,
    language TEXT,
    status TEXT DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')),
    cloud_sync BOOLEAN DEFAULT FALSE,
    sync_level TEXT DEFAULT 'metadata' CHECK (sync_level IN ('metadata', 'metadata+ocr', 'full')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_books_user_id ON books(user_id);
CREATE INDEX idx_books_device_id ON books(device_id);
CREATE INDEX idx_books_status ON books(status);

ALTER TABLE books ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own books" ON books
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own books" ON books
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own books" ON books
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own books" ON books
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================
-- CHAPTERS
-- ============================================

CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    title TEXT,
    start_page INTEGER,
    end_page INTEGER,
    file_path TEXT, -- Local path on device
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chapters_book_id ON chapters(book_id);
CREATE INDEX idx_chapters_status ON chapters(status);

ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own chapters" ON chapters
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM books WHERE books.id = chapters.book_id AND books.user_id = auth.uid()
        )
    );

-- ============================================
-- JOBS
-- ============================================

CREATE TYPE job_status AS ENUM (
    'pending',
    'queued',
    'running',
    'paused',
    'retrying',
    'completed',
    'cancelled',
    'failed'
);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    book_id UUID REFERENCES books(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    status job_status DEFAULT 'pending',
    current_stage TEXT,
    progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    eta_seconds INTEGER,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_device_id ON jobs(device_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own jobs" ON jobs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own jobs" ON jobs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own jobs" ON jobs
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- PIPELINE STAGES
-- ============================================

CREATE TABLE pipeline_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    stage_name TEXT NOT NULL,
    stage_order INTEGER NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms BIGINT,
    checkpoint_data JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pipeline_stages_job_id ON pipeline_stages(job_id);
CREATE INDEX idx_pipeline_stages_order ON pipeline_stages(job_id, stage_order);

ALTER TABLE pipeline_stages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own pipeline stages" ON pipeline_stages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM jobs WHERE jobs.id = pipeline_stages.job_id AND jobs.user_id = auth.uid()
        )
    );

-- ============================================
-- LOGS
-- ============================================

CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    stage_name TEXT,
    message TEXT NOT NULL,
    severity TEXT DEFAULT 'info' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_logs_user_id ON logs(user_id);
CREATE INDEX idx_logs_job_id ON logs(job_id);
CREATE INDEX idx_logs_created_at ON logs(created_at DESC);
CREATE INDEX idx_logs_severity ON logs(severity);

ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own logs" ON logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own logs" ON logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Auto-cleanup old logs (keep last 7 days)
-- Note: This requires pg_cron extension in production
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule(
--     'cleanup-logs',
--     '0 2 * * *',
--     $$DELETE FROM logs WHERE created_at < NOW() - INTERVAL '7 days'$$
-- );

-- ============================================
-- API PROVIDERS
-- ============================================

CREATE TABLE api_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    provider_type TEXT NOT NULL CHECK (provider_type IN ('llm', 'embedding', 'ocr')),
    is_active BOOLEAN DEFAULT TRUE,
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_providers_user_id ON api_providers(user_id);
CREATE INDEX idx_api_providers_type ON api_providers(provider_type);

ALTER TABLE api_providers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own providers" ON api_providers
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own providers" ON api_providers
    FOR ALL USING (auth.uid() = user_id);

-- ============================================
-- API KEYS (Encrypted)
-- ============================================

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES api_providers(id) ON DELETE CASCADE,
    key_name TEXT NOT NULL,
    encrypted_key TEXT NOT NULL, -- Encrypted with user-specific key
    key_hash TEXT NOT NULL, -- For identification without decryption
    quota_limit INTEGER,
    quota_used INTEGER DEFAULT 0,
    cooldown_until TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'unhealthy', 'unknown')),
    latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_provider_id ON api_keys(provider_id);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE;

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own API keys" ON api_keys
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own API keys" ON api_keys
    FOR ALL USING (auth.uid() = user_id);

-- ============================================
-- BENCHMARK RESULTS
-- ============================================

CREATE TABLE benchmark_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    embedding_model TEXT,
    chunking_strategy TEXT,
    vector_index_type TEXT,
    recall_at_k FLOAT,
    mrr FLOAT,
    latency_ms FLOAT,
    memory_mb FLOAT,
    disk_mb FLOAT,
    cost_usd FLOAT,
    throughput_docs_per_sec FLOAT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_benchmark_results_user_id ON benchmark_results(user_id);
CREATE INDEX idx_benchmark_results_created_at ON benchmark_results(created_at DESC);

ALTER TABLE benchmark_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own benchmarks" ON benchmark_results
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own benchmarks" ON benchmark_results
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================
-- USER SETTINGS
-- ============================================

CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    cpu_threads INTEGER DEFAULT 4,
    worker_count INTEGER DEFAULT 2,
    concurrent_ocr INTEGER DEFAULT 2,
    concurrent_embeddings INTEGER DEFAULT 4,
    concurrent_llm INTEGER DEFAULT 2,
    ram_limit_mb INTEGER DEFAULT 8192,
    disk_cache_gb INTEGER DEFAULT 10,
    gpu_enabled BOOLEAN DEFAULT FALSE,
    default_vector_index TEXT DEFAULT 'turbovec',
    default_embedding_model TEXT DEFAULT 'ollama/nomic-embed-text',
    auto_retry BOOLEAN DEFAULT TRUE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own settings" ON user_settings
    FOR ALL USING (auth.uid() = user_id);

-- ============================================
-- NOTIFICATIONS
-- ============================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info' CHECK (type IN ('info', 'success', 'warning', 'error')),
    is_read BOOLEAN DEFAULT FALSE,
    related_job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own notifications" ON notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications" ON notifications
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- PROMPT TEMPLATES
-- ============================================

CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    template_type TEXT NOT NULL CHECK (template_type IN ('ocr_correction', 'chunking', 'embedding', 'rag')),
    content TEXT NOT NULL,
    variables JSONB,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prompt_templates_user_id ON prompt_templates(user_id);
CREATE INDEX idx_prompt_templates_type ON prompt_templates(template_type);

ALTER TABLE prompt_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own templates" ON prompt_templates
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own templates" ON prompt_templates
    FOR ALL USING (auth.uid() = user_id);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chapters_updated_at BEFORE UPDATE ON chapters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_providers_updated_at BEFORE UPDATE ON api_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_templates_updated_at BEFORE UPDATE ON prompt_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to create profile on user signup
CREATE OR REPLACE FUNCTION create_profile_on_signup()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, email)
    VALUES (NEW.id, NEW.email);
    
    INSERT INTO user_settings (user_id)
    VALUES (NEW.id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_profile_on_signup();

-- ============================================
-- REALTIME SUBSCRIPTIONS
-- ============================================

-- Enable realtime for key tables
ALTER PUBLICATION supabase_realtime ADD TABLE jobs;
ALTER PUBLICATION supabase_realtime ADD TABLE logs;
ALTER PUBLICATION supabase_realtime ADD TABLE devices;
ALTER PUBLICATION supabase_realtime ADD TABLE notifications;
ALTER PUBLICATION supabase_realtime ADD TABLE pipeline_stages;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE profiles IS 'User profiles linked to Supabase Auth';
COMMENT ON TABLE devices IS 'Registered desktop agents per user';
COMMENT ON TABLE books IS 'Document metadata (files stored locally)';
COMMENT ON TABLE chapters IS 'Book chapters extracted during processing';
COMMENT ON TABLE jobs IS 'Pipeline jobs with resumable state';
COMMENT ON TABLE pipeline_stages IS 'Individual stages within a job';
COMMENT ON TABLE logs IS 'Structured logs with realtime streaming';
COMMENT ON TABLE api_providers IS 'Configured AI providers (LLM, Embedding, OCR)';
COMMENT ON TABLE api_keys IS 'Encrypted API keys with rotation support';
COMMENT ON TABLE benchmark_results IS 'Performance benchmarks for comparison';
COMMENT ON TABLE user_settings IS 'User-configurable performance settings';
COMMENT ON TABLE notifications IS 'Realtime notifications for users';
COMMENT ON TABLE prompt_templates IS 'Customizable prompt templates';
