-- RAG Studio V2.5: Distributed Workflow & Collaborative Processing Schema
-- Enables multi-user, multi-device, multi-org collaborative pipeline execution

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. WORKSPACES & COLLABORATION
-- ==========================================

-- Workspaces (Organizations/Teams)
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb, -- Workspace-level config
    crdt_state JSONB DEFAULT '{}'::jsonb -- For CRDT synchronization
);

-- Workspace Members & Roles
CREATE TYPE workspace_role AS ENUM ('owner', 'admin', 'project_manager', 'researcher', 'contributor', 'reviewer', 'viewer');

CREATE TABLE workspace_members (
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role workspace_role NOT NULL DEFAULT 'viewer',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id)
);

-- ==========================================
-- 2. DISTRIBUTED WORKERS
-- ==========================================

-- Worker Registration (Desktop Agents, Cloud Workers, etc.)
CREATE TYPE worker_status AS ENUM ('online', 'offline', 'busy', 'maintenance', 'unhealthy');

CREATE TABLE workers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    device_uuid UUID UNIQUE NOT NULL,
    os_info JSONB, -- { platform, version, arch }
    hardware_specs JSONB, -- { cpu_cores, ram_gb, gpu_model, gpu_vram_gb, storage_gb }
    capabilities JSONB DEFAULT '[]'::jsonb, -- [ 'ocr', 'llm_correction', 'embedding', 'indexing' ]
    installed_models JSONB DEFAULT '[]'::jsonb, -- [ 'tesseract', 'gemini-pro', 'nomic-embed' ]
    status worker_status DEFAULT 'offline',
    current_task_id UUID, -- Reference to active task
    last_heartbeat TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb, -- { temperature, battery, network_speed }
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Worker Heartbeat Log (for auditing and analytics)
CREATE TABLE worker_heartbeats (
    id BIGSERIAL PRIMARY KEY,
    worker_id UUID REFERENCES workers(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    status worker_status,
    load_metrics JSONB, -- { cpu_usage, ram_usage, gpu_usage, temperature }
    current_task_id UUID
);

-- ==========================================
-- 3. PIPELINES & STAGES (Enhanced)
-- ==========================================

-- Pipeline Templates
CREATE TABLE pipeline_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    definition JSONB NOT NULL, -- { stages: [{ type, config, fallback }] }
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pipelines (Instances)
CREATE TYPE pipeline_status AS ENUM ('draft', 'running', 'paused', 'completed', 'failed', 'cancelled');

CREATE TABLE pipelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id UUID REFERENCES books(id) ON DELETE CASCADE, -- Reusing 'books' as projects for now
    template_id UUID REFERENCES pipeline_templates(id),
    status pipeline_status DEFAULT 'draft',
    current_stage_index INT DEFAULT 0,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Pipeline Stages (The core workflow units)
CREATE TYPE stage_status AS ENUM ('pending', 'queued', 'running', 'completed', 'failed', 'rejected', 'cancelled');

CREATE TABLE pipeline_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_id UUID REFERENCES pipelines(id) ON DELETE CASCADE,
    stage_index INT NOT NULL,
    stage_type TEXT NOT NULL, -- 'upload', 'split', 'ocr', 'cleaning', 'chunking', 'embedding', 'indexing'
    status stage_status DEFAULT 'pending',
    config JSONB DEFAULT '{}'::jsonb,
    
    -- Distribution Control
    assigned_worker_id UUID REFERENCES workers(id),
    claimed_by_worker_id UUID REFERENCES workers(id),
    lease_expires_at TIMESTAMPTZ,
    
    -- Execution Metrics
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    
    -- Checkpointing
    checkpoint_data JSONB, -- Last successful state
    artifact_version INT DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(pipeline_id, stage_index)
);

-- ==========================================
-- 4. TASKS & MARKETPLACE
-- ==========================================

-- Granular Tasks (Chapter/Page/Chunk level)
CREATE TYPE task_granularity AS ENUM ('pipeline', 'chapter', 'page_range', 'chunk_batch');
CREATE TYPE task_priority AS ENUM ('low', 'normal', 'high', 'critical');

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES pipeline_stages(id) ON DELETE CASCADE,
    granularity task_granularity DEFAULT 'pipeline',
    
    -- Scope Definition
    book_id UUID REFERENCES books(id),
    chapter_ids UUID[], -- Array of chapter IDs
    page_start INT,
    page_end INT,
    chunk_ids UUID[], -- Array of chunk IDs
    
    priority task_priority DEFAULT 'normal',
    status stage_status DEFAULT 'pending',
    
    -- Assignment
    assigned_to_user_id UUID REFERENCES auth.users(id),
    claimed_by_worker_id UUID REFERENCES workers(id),
    lease_token UUID, -- Unique token for leasing
    lease_expires_at TIMESTAMPTZ,
    
    -- Review Workflow
    requires_review BOOLEAN DEFAULT FALSE,
    reviewed_by UUID REFERENCES auth.users(id),
    review_status TEXT, -- 'approved', 'rejected', 'changes_requested'
    review_comments TEXT,
    
    -- Metrics
    progress INT DEFAULT 0, -- 0-100
    retry_count INT DEFAULT 0,
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ==========================================
-- 5. ARTIFACTS (Immutable Versioned Storage)
-- ==========================================

CREATE TYPE artifact_type AS ENUM ('pdf', 'chapter_pdf', 'ocr_text', 'cleaned_text', 'chunks', 'embeddings', 'vector_index', 'report');

CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES pipeline_stages(id),
    task_id UUID REFERENCES tasks(id),
    
    name TEXT NOT NULL,
    type artifact_type NOT NULL,
    version INT NOT NULL, -- v1, v2, v3...
    
    -- Storage Reference (S3, Local, NAS)
    storage_provider TEXT DEFAULT 'local', -- 'local', 's3', 'nas'
    storage_path TEXT NOT NULL,
    storage_url TEXT, -- Pre-signed URL if cloud
    file_size_bytes BIGINT,
    checksum_sha256 TEXT NOT NULL, -- Integrity check
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb, -- { chunk_count, embedding_dim, index_type }
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(stage_id, name, version) -- Prevent overwrites
);

-- Artifact Dependencies (Lineage)
CREATE TABLE artifact_dependencies (
    parent_artifact_id UUID REFERENCES artifacts(id) ON DELETE CASCADE,
    child_artifact_id UUID REFERENCES artifacts(id) ON DELETE CASCADE,
    relationship TEXT, -- 'derived_from', 'merged_into', 'split_from'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (parent_artifact_id, child_artifact_id)
);

-- ==========================================
-- 6. AUDIT TRAIL & EVENTS
-- ==========================================

CREATE TYPE event_type AS ENUM (
    'PIPELINE_CREATED', 'STAGE_COMPLETED', 'TASK_ASSIGNED', 'TASK_ACCEPTED', 
    'TASK_REJECTED', 'TASK_FAILED', 'WORKER_ONLINE', 'WORKER_OFFLINE', 
    'ARTIFACT_UPLOADED', 'BENCHMARK_COMPLETED', 'REVIEW_REQUESTED', 'REVIEW_APPROVED'
);

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id),
    user_id UUID REFERENCES auth.users(id),
    worker_id UUID REFERENCES workers(id),
    event_type event_type NOT NULL,
    entity_type TEXT, -- 'pipeline', 'task', 'artifact'
    entity_id UUID,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Realtime Event Bus (Subscriptions)
CREATE TABLE event_bus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    event_type event_type NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- Enable Realtime for event_bus
ALTER PUBLICATION supabase_realtime ADD TABLE event_bus;

-- ==========================================
-- 7. NOTIFICATIONS
-- ==========================================

CREATE TYPE notification_type AS ENUM ('task_assigned', 'task_completed', 'review_required', 'worker_offline', 'pipeline_finished', 'error');

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id),
    type notification_type NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    related_entity_type TEXT,
    related_entity_id UUID,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- 8. INDEXES & PERFORMANCE
-- ==========================================

CREATE INDEX idx_workers_status ON workers(status);
CREATE INDEX idx_workers_capabilities ON workers USING GIN(capabilities);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to_user_id);
CREATE INDEX idx_tasks_lease ON tasks(lease_expires_at) WHERE status = 'pending';
CREATE INDEX idx_artifacts_stage ON artifacts(stage_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_event_bus_workspace ON event_bus(workspace_id, created_at DESC);

-- ==========================================
-- 9. ROW LEVEL SECURITY (RLS)
-- ==========================================

-- Enable RLS on all new tables
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE workers ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Helper Function: Check Workspace Membership
CREATE OR REPLACE FUNCTION check_workspace_membership(target_workspace_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM workspace_members wm
        JOIN auth.users u ON u.id = wm.user_id
        WHERE wm.workspace_id = target_workspace_id
        AND u.id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Workspaces Policies
CREATE POLICY "Users can view their workspaces" ON workspaces
    FOR SELECT USING (check_workspace_membership(id));

CREATE POLICY "Owners can create workspaces" ON workspaces
    FOR INSERT WITH CHECK (owner_id = auth.uid());

-- Workers Policies
CREATE POLICY "Members can view workers" ON workers
    FOR SELECT USING (check_workspace_membership(workspace_id));

CREATE POLICY "Workers can update own status" ON workers
    FOR UPDATE USING (auth.uid() = owner_id OR id IN (SELECT id FROM workers WHERE owner_id = auth.uid()));

-- Tasks Policies
CREATE POLICY "Members can view tasks" ON tasks
    FOR SELECT USING (check_workspace_membership(workspace_id));

CREATE POLICY "Members can claim tasks" ON tasks
    FOR UPDATE USING (check_workspace_membership(workspace_id));

-- Artifacts Policies
CREATE POLICY "Members can view artifacts" ON artifacts
    FOR SELECT USING (check_workspace_membership(workspace_id));

-- Audit Logs Policies
CREATE POLICY "Admins can view audit logs" ON audit_logs
    FOR SELECT USING (check_workspace_membership(workspace_id));

-- ==========================================
-- 10. TRIGGERS
-- ==========================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON workspaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workers_updated_at BEFORE UPDATE ON workers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipelines_updated_at BEFORE UPDATE ON pipelines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_stages_updated_at BEFORE UPDATE ON pipeline_stages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-create notification on task assignment
CREATE OR REPLACE FUNCTION create_task_notification()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.assigned_to_user_id IS NOT NULL AND OLD.assigned_to_user_id IS DISTINCT FROM NEW.assigned_to_user_id THEN
        INSERT INTO notifications (user_id, workspace_id, type, title, message, related_entity_type, related_entity_id)
        VALUES (
            NEW.assigned_to_user_id,
            NEW.workspace_id,
            'task_assigned',
            'New Task Assigned',
            'You have been assigned a new task in the pipeline.',
            'task',
            NEW.id
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_task_notification
AFTER UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION create_task_notification();
