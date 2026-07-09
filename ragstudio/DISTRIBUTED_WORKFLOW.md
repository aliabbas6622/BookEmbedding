# RAG Studio V2.5 - Distributed Workflow & Collaborative Processing

## Overview

RAG Studio V2.5 transforms the platform from a distributed document processing system into a **distributed workflow orchestration platform**. This upgrade enables multiple users, devices, and organizations to collaboratively execute different stages of the same pipeline without restarting workflows.

## Core Philosophy

The system revolves around four key concepts:

1. **Artifacts** - Immutable versioned outputs that flow between stages
2. **Stages** - Independent pipeline steps that process artifacts
3. **Workers** - Any entity capable of executing work (Desktop Agents, Cloud Workers, GPU Servers, etc.)
4. **Pipelines** - Ordered collections of stages owned by projects

### Key Principles

- Workers do NOT own projects - they temporarily execute stages
- Projects own pipelines
- Artifacts flow between stages
- Stages can move freely between workers
- No stage depends on which worker executed the previous stage

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Supabase Backend                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Workers  │  │  Tasks   │  │ Artifacts│  │  Events  │   │
│  │  Table   │  │  Table   │  │  Table   │  │   Bus    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│         │             │              │             │        │
│         └─────────────┴──────────────┴─────────────┘        │
│                           │                                  │
│                    Realtime Sync                             │
└───────────────────────────┼──────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Desktop      │  │   Cloud       │  │   GPU         │
│  Agent        │  │   Worker      │  │   Server      │
│  (Worker A)   │  │   (Worker B)  │  │   (Worker C)  │
└───────────────┘  └───────────────┘  └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    Task Marketplace
                (Claim → Execute → Complete)
```

## Database Schema

See `supabase/migrations/002_distributed_workflow.sql` for complete schema including:

- **workspaces** - Organizations/teams with role-based access
- **workers** - Registered processing nodes with capabilities
- **pipeline_stages** - Individual workflow steps with leasing
- **tasks** - Granular work units (pipeline/chapter/page/chunk level)
- **artifacts** - Immutable versioned outputs with checksums
- **audit_logs** - Complete immutable action history
- **event_bus** - Realtime event streaming
- **notifications** - User alerts and updates

All tables implement Row Level Security (RLS) for multi-tenant isolation.

## Core Components

### 1. Capability-Based Scheduler

The scheduler matches tasks to optimal workers based on advertised capabilities, not assumptions about worker type.

**Worker Capabilities Include:**
- CPU cores, RAM, GPU model/VRAM
- Supported pipeline stages (OCR, embedding, indexing, etc.)
- Installed models (Tesseract, Gemini, Nomic, etc.)
- Current load metrics (CPU%, RAM%, temperature)
- Network speed and available disk space

**Scoring Algorithm:**
```python
score = (cpu_cores * 10) + (ram_gb * 5) + (gpu_vram_gb * 20)
if cpu_usage > 80: score -= 50
elif cpu_usage > 50: score -= 20
if temperature < 70: score += 10
```

### 2. Task Leasing Manager

Prevents duplicate execution through transactional leasing:

```python
# Claim a task
lease = await lease_manager.claim_task(
    task_id="uuid",
    worker_id="worker-uuid",
    workspace_id="workspace-uuid"
)

if lease:
    # Execute task
    result = await execute_task(task)
    
    # Release lease on completion
    await lease_manager.release_lease(
        task_id="uuid",
        worker_id="worker-uuid",
        lease_token=lease.lease_token,
        success=True
    )
```

**Lease Properties:**
- Duration: 5 minutes (configurable)
- Automatic expiration if heartbeat stops
- Reclamation loop runs every 60 seconds
- Atomic claim operations prevent race conditions

### 3. Artifact Manager

Manages immutable versioned artifacts with integrity verification:

```python
# Register new artifact
artifact = await artifact_manager.register_artifact(
    workspace_id="uuid",
    stage_id="uuid",
    task_id="uuid",
    name="ocr_output.txt",
    artifact_type="ocr_text",
    storage_path="/path/to/file",
    checksum="sha256_hash",
    file_size=1024,
    metadata={"chunk_count": 150}
)

# Link artifacts (lineage)
await artifact_manager.link_artifacts(
    parent_id="pdf_artifact_uuid",
    child_id="ocr_artifact_uuid",
    relationship="derived_from"
)

# Verify integrity
is_valid = await artifact_manager.verify_artifact_integrity(
    artifact_id="uuid",
    local_data=file_bytes
)
```

**Artifact Versioning:**
- Each stage output gets incrementing version (v1, v2, v3...)
- Artifacts are NEVER overwritten
- Old versions preserved for rollback and audit

### 4. Distributed Workflow Orchestrator

Main coordinator for worker lifecycle and task execution:

```python
from core.distributed import create_orchestrator

# Initialize orchestrator
orchestrator = create_orchestrator(
    supabase_url="https://xxx.supabase.co",
    supabase_key="service_role_key",
    worker_id="unique-worker-uuid",
    workspace_id="workspace-uuid"
)

# Start worker
await orchestrator.start()

# Claim and execute tasks
while True:
    task = await orchestrator.claim_next_task(
        stage_types=["ocr", "embedding"]
    )
    
    if task:
        try:
            result = await execute_stage(task)
            await orchestrator.complete_task(
                task_id=task["id"],
                success=True,
                artifacts=result.artifacts
            )
        except Exception as e:
            await orchestrator.complete_task(
                task_id=task["id"],
                success=False,
                error_message=str(e)
            )

# Graceful shutdown
await orchestrator.stop()
```

## Distribution Patterns

### Pipeline-Level Distribution

Different users execute different stages:

```
Ali (OCR) → Ahmed (Cleaning) → Sara (Embeddings) → Hamza (Indexing)
```

### Chapter-Level Distribution

Different chapters assigned to different workers:

```
Book: "Research Paper"
├─ Chapters 1-10  → Worker A (Desktop)
├─ Chapters 11-20 → Worker B (Laptop)
└─ Chapters 21-30 → Worker C (GPU Server)
```

### Page-Level Distribution

Pages split across workers:

```
PDF: 100 pages
├─ Pages 1-25   → Desktop Agent
├─ Pages 26-50  → Laptop
└─ Pages 51-75  → Cloud Worker
```

### Chunk-Level Distribution

Embedding generation parallelized:

```
Chunks: 1000
├─ Chunks 1-250   → Worker A
├─ Chunks 251-500 → Worker B
├─ Chunks 501-750 → Worker C
└─ Chunks 751-1000→ Worker D
```

Results merge automatically after completion.

## Task Marketplace

### Available Operations

| Operation | Description | Endpoint |
|-----------|-------------|----------|
| **Claim** | Worker claims unassigned task | `POST /api/tasks/:id/claim` |
| **Assign** | Manual assignment to user/worker | `POST /api/tasks/:id/assign` |
| **Delegate** | Transfer to another worker | `POST /api/tasks/:id/delegate` |
| **Reject** | Return task to queue | `POST /api/tasks/:id/reject` |
| **Pause** | Temporarily halt execution | `POST /api/tasks/:id/pause` |
| **Resume** | Continue paused task | `POST /api/tasks/:id/resume` |
| **Cancel** | Abort task permanently | `POST /api/tasks/:id/cancel` |

### Review Gates

Enable approval workflows:

```json
{
  "task_id": "uuid",
  "requires_review": true,
  "reviewer_id": "user-uuid",
  "review_status": "pending", // approved, rejected, changes_requested
  "review_comments": "OCR quality needs improvement"
}
```

Rejected work returns to previous stage automatically.

## Checkpointing & Resume

Every stage checkpoints automatically:

```python
# Stage execution with checkpointing
async def execute_stage_with_checkpoint(stage_id: str, data: Dict):
    try:
        # Process in batches
        for batch in data.batches():
            result = await process_batch(batch)
            
            # Auto-checkpoint after each batch
            await save_checkpoint(
                stage_id=stage_id,
                checkpoint_data={
                    "last_processed": batch.id,
                    "progress": batch.progress,
                    "partial_results": result
                }
            )
        
        return finalize_stage()
    
    except Exception as e:
        # Resume from last checkpoint on retry
        checkpoint = await get_last_checkpoint(stage_id)
        return await resume_from_checkpoint(checkpoint)
```

**Checkpoint Guarantees:**
- Saved after every successful batch
- Includes progress percentage and partial results
- Survives worker crashes and restarts
- Resumes exactly from last successful point
- Never restarts completed work

## Realtime Collaboration

### CRDT-Based Synchronization

Used for collaborative objects (NOT task ownership):

- Prompt templates
- OCR corrections
- Annotations and bookmarks
- Notes and tags
- Workflow definitions
- Comments and project metadata

**Features:**
- Live cursors showing other users' positions
- Presence indicators (who's online)
- Undo/Redo with conflict resolution
- Offline editing with automatic sync
- Version history for all changes

### Event Bus

Modules communicate through events:

```python
# Emit event
await orchestrator._emit_event("STAGE_COMPLETED", {
    "stage_id": "uuid",
    "worker_id": "worker-uuid",
    "artifacts": ["artifact-uuid-1", "artifact-uuid-2"]
})

# Subscribe to events (frontend)
const channel = supabase
  .channel('workflow-events')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'event_bus',
      filter: `workspace_id=eq.${workspaceId}`
    },
    (payload) => {
      handleEvent(payload.new)
    }
  )
  .subscribe()
```

**Event Types:**
- `PIPELINE_CREATED`
- `STAGE_COMPLETED`
- `TASK_ASSIGNED` / `TASK_ACCEPTED` / `TASK_REJECTED`
- `TASK_FAILED`
- `WORKER_ONLINE` / `WORKER_OFFLINE`
- `ARTIFACT_UPLOADED`
- `BENCHMARK_COMPLETED`
- `REVIEW_REQUESTED` / `REVIEW_APPROVED`

## Notifications

Users receive notifications for:

- Task assignments
- Task completions
- Review requests
- Worker offline alerts
- Pipeline finished
- API quota exhausted
- Benchmark completed

Delivered via:
- In-app notifications (Realtime)
- Email (future)
- Push notifications (mobile, future)
- Webhooks (future)

## Workspace Collaboration

### Roles & Permissions

| Role | Permissions |
|------|-------------|
| **Owner** | Full control, billing, delete workspace |
| **Admin** | Manage members, settings, all projects |
| **Project Manager** | Create/edit projects, assign tasks |
| **Researcher** | Execute pipelines, view benchmarks |
| **Contributor** | Claim tasks, upload artifacts |
| **Reviewer** | Approve/reject work, add comments |
| **Viewer** | Read-only access |

### Workspace Resources

Each workspace contains:
- Projects (books/documents)
- Registered workers
- Members with roles
- Pipeline templates
- Prompt templates
- Benchmark history
- Audit logs
- Shared settings

## Security

### Row Level Security (RLS)

All tables enforce RLS policies:

```sql
-- Example: Only workspace members can view tasks
CREATE POLICY "Members can view tasks" ON tasks
    FOR SELECT USING (check_workspace_membership(workspace_id));
```

### Authentication

- Supabase Auth (Email/Password, Google, GitHub)
- JWT tokens for API requests
- Device registration required for workers
- Encrypted API key storage

### Audit Trail

Every action recorded immutably:

```json
{
  "id": 12345,
  "workspace_id": "uuid",
  "user_id": "user-uuid",
  "event_type": "TASK_ASSIGNED",
  "entity_type": "task",
  "entity_id": "task-uuid",
  "details": {
    "assigned_to": "user-uuid",
    "previous_status": "pending",
    "new_status": "queued"
  },
  "created_at": "2025-01-15T10:30:00Z"
}
```

## API Reference

### Worker Management

#### Register Worker
```http
POST /api/workers/register
Content-Type: application/json

{
  "device_uuid": "unique-device-id",
  "name": "My Desktop Worker",
  "os_info": {
    "platform": "Linux",
    "version": "5.15.0"
  },
  "hardware_specs": {
    "cpu_cores": 8,
    "ram_gb": 32,
    "gpu_model": "RTX 4090",
    "gpu_vram_gb": 24,
    "storage_gb": 1000
  },
  "capabilities": ["ocr", "embedding", "indexing"],
  "installed_models": ["tesseract", "nomic-embed-text"]
}
```

#### Send Heartbeat
```http
POST /api/workers/:id/heartbeat
Content-Type: application/json

{
  "metrics": {
    "cpu_usage": 45.2,
    "ram_usage": 62.1,
    "temperature": 65,
    "available_disk_gb": 450
  }
}
```

### Task Management

#### Claim Task
```http
POST /api/tasks/:id/claim
Authorization: Bearer <worker-token>

{
  "worker_id": "worker-uuid"
}

Response:
{
  "success": true,
  "lease": {
    "task_id": "uuid",
    "worker_id": "worker-uuid",
    "lease_token": "lease-uuid",
    "expires_at": "2025-01-15T10:35:00Z"
  }
}
```

#### Complete Task
```http
POST /api/tasks/:id/complete
Authorization: Bearer <worker-token>

{
  "success": true,
  "artifacts": [
    {
      "name": "embeddings.bin",
      "type": "embeddings",
      "storage_path": "/path/to/file",
      "checksum": "sha256_hash",
      "file_size": 1048576,
      "metadata": {
        "dimension": 768,
        "chunk_count": 150
      }
    }
  ]
}
```

#### Assign Task (Manual)
```http
POST /api/tasks/:id/assign
Authorization: Bearer <user-token>

{
  "assigned_to_user_id": "user-uuid",
  "priority": "high"
}
```

#### Review Task
```http
POST /api/tasks/:id/review
Authorization: Bearer <reviewer-token>

{
  "approved": false,
  "comments": "OCR quality below threshold, please re-run with higher DPI"
}
```

### Artifact Management

#### Get Latest Artifact
```http
GET /api/artifacts/latest?stage_id=:stage_id&name=ocr_output.txt
Authorization: Bearer <user-token>

Response:
{
  "id": "artifact-uuid",
  "name": "ocr_output.txt",
  "type": "ocr_text",
  "version": 3,
  "storage_path": "/path/to/v3/ocr_output.txt",
  "checksum_sha256": "abc123...",
  "metadata": {
    "word_count": 5000,
    "confidence_avg": 0.95
  }
}
```

#### Get Artifact Lineage
```http
GET /api/artifacts/:id/lineage
Authorization: Bearer <user-token>

Response:
{
  "artifact": {...},
  "parents": [
    {
      "id": "parent-uuid",
      "relationship": "derived_from"
    }
  ],
  "children": [
    {
      "id": "child-uuid",
      "relationship": "merged_into"
    }
  ]
}
```

### Analytics & Monitoring

#### Get Worker Status
```http
GET /api/workspaces/:id/workers
Authorization: Bearer <user-token>

Response:
[
  {
    "id": "worker-uuid",
    "name": "GPU Server",
    "status": "busy",
    "current_task_id": "task-uuid",
    "hardware_specs": {...},
    "metadata": {
      "cpu_usage": 78,
      "gpu_usage": 92,
      "temperature": 72
    },
    "last_heartbeat": "2025-01-15T10:29:30Z"
  }
]
```

#### Get Audit Logs
```http
GET /api/workspaces/:id/audit-logs?event_type=TASK_COMPLETED&limit=50
Authorization: Bearer <admin-token>

Response:
[
  {
    "id": 12345,
    "event_type": "TASK_COMPLETED",
    "user_id": "user-uuid",
    "worker_id": "worker-uuid",
    "details": {...},
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

## Configuration

### Environment Variables

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_key
SUPABASE_ANON_KEY=your_anon_key

# Worker Configuration
WORKER_ID=unique-worker-uuid
WORKSPACE_ID=workspace-uuid
HEARTBEAT_INTERVAL=30
LEASE_DURATION_MINUTES=5

# Storage
LOCAL_STORAGE_PATH=./artifacts
S3_BUCKET=ragstudio-artifacts
S3_REGION=us-east-1

# Performance
MAX_CONCURRENT_TASKS=5
BATCH_SIZE=100
CHECKPOINT_INTERVAL_BATCHES=10
```

### Pipeline Templates

Create reusable workflow definitions:

```json
{
  "name": "High-Quality OCR Pipeline",
  "description": "Multi-stage OCR with LLM correction",
  "definition": {
    "stages": [
      {
        "type": "split",
        "config": {
          "mode": "chapter",
          "min_pages_per_chapter": 5
        }
      },
      {
        "type": "ocr",
        "config": {
          "engine": "tesseract",
          "dpi": 300,
          "languages": ["eng"]
        },
        "fallback": "easyocr"
      },
      {
        "type": "llm_correction",
        "config": {
          "model": "gemini-pro",
          "prompt_template": "ocr_cleanup_v2"
        }
      },
      {
        "type": "chunking",
        "config": {
          "strategy": "semantic",
          "max_tokens": 512
        }
      },
      {
        "type": "embedding",
        "config": {
          "model": "nomic-embed-text",
          "dimension": 768
        }
      },
      {
        "type": "indexing",
        "config": {
          "store": "turbovec",
          "quantization": "pq"
        }
      }
    ]
  }
}
```

## Best Practices

### 1. Worker Design

- Register with accurate capability advertisements
- Send heartbeats reliably (every 30 seconds)
- Release leases promptly on completion/failure
- Handle SIGTERM for graceful shutdown
- Log structured metrics for monitoring

### 2. Task Execution

- Claim tasks atomically (handle claim failures)
- Renew leases for long-running tasks
- Checkpoint frequently (every batch)
- Validate artifact checksums before upload
- Emit events for significant state changes

### 3. Error Handling

- Distinguish transient vs permanent failures
- Implement exponential backoff for retries
- Set appropriate max_retries per stage type
- Provide detailed error messages for debugging
- Use review gates for quality-critical stages

### 4. Scaling

- Use chapter/page-level distribution for large books
- Balance load across heterogeneous workers
- Monitor worker health metrics proactively
- Implement circuit breakers for failing workers
- Cache embeddings to avoid recomputation

## Migration Guide

### From V2.0 to V2.5

1. **Run Database Migration**
   ```bash
   supabase db push --file supabase/migrations/002_distributed_workflow.sql
   ```

2. **Update Desktop Agents**
   ```python
   # Old approach (single-user)
   pipeline.execute(book_id="uuid")
   
   # New approach (distributed)
   orchestrator = create_orchestrator(...)
   await orchestrator.start()
   task = await orchestrator.claim_next_task()
   ```

3. **Migrate Existing Jobs**
   ```sql
   -- Convert existing jobs to tasks
   INSERT INTO tasks (workspace_id, stage_id, granularity, status)
   SELECT 
     j.workspace_id,
     s.id,
     'pipeline'::task_granularity,
     CASE 
       WHEN j.status = 'completed' THEN 'completed'
       ELSE 'queued'
     END
   FROM jobs j
   JOIN pipeline_stages s ON s.pipeline_id = j.pipeline_id;
   ```

4. **Update Frontend**
   - Import new types from `types/distributed-workflow.ts`
   - Subscribe to realtime event bus
   - Add task marketplace UI
   - Implement worker management dashboard

## Future Roadmap

Planned enhancements requiring minimal architectural changes:

- [ ] Distributed GPU clusters with NCCL support
- [ ] Kubernetes operator for auto-scaling workers
- [ ] Federated workspaces across organizations
- [ ] Public worker marketplace (paid tasks)
- [ ] Plugin marketplace for custom stages
- [ ] Scheduled/triggered pipelines
- [ ] AI supervisor agents for quality control
- [ ] Enterprise teams with SSO integration
- [ ] Advanced analytics and cost tracking

## Support

For issues and questions:
- GitHub Issues: https://github.com/ragstudio/ragstudio/issues
- Documentation: https://docs.ragstudio.io
- Discord: https://discord.gg/ragstudio

---

**Version:** 2.5.0  
**Last Updated:** January 2025  
**Status:** Production Ready
