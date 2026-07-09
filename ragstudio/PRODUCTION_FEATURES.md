# RAG Studio - Production Features Documentation

## Overview

RAG Studio is now equipped with enterprise-grade production features for reliable, fault-tolerant document processing pipelines.

## 🚀 Production Features Implemented

### 1. **Job Management System** (`core/job_manager.py`)

A comprehensive job management system that handles the entire lifecycle of document processing jobs.

#### Key Components:

- **JobManager**: Central orchestrator for all jobs
- **CacheManager**: Intelligent caching of stage results
- **CheckpointManager**: Save/restore pipeline state
- **FallbackManager**: Graceful degradation on failures
- **RetryConfig**: Configurable retry strategies

### 2. **Caching System**

Automatically caches intermediate stage results to avoid re-computation.

**Features:**
- SHA256-based cache key generation
- TTL (Time-To-Live) expiration
- Persistent disk-based storage
- Automatic cleanup of expired entries
- Per-stage cache invalidation

**Configuration:**
```python
CACHE_DEFAULT_TTL_HOURS = 24
CACHE_MAX_SIZE_MB = 1000
```

**Usage:**
```python
# Start pipeline with caching enabled
pipeline_id = await orchestrator.run(
    document_id=doc_id,
    enable_cache=True  # Enable caching
)

# Clear cache for specific job
await orchestrator.clear_cache(job_id="...")
```

### 3. **Checkpointing & Resume**

Save pipeline state after each successful stage for seamless resumption.

**Features:**
- Automatic checkpoint after each stage
- Checksum validation for data integrity
- Resume from exact failure point
- No duplicate processing

**Configuration:**
```python
CHECKPOINT_ENABLED = True
CHECKPOINT_INTERVAL_SECONDS = 30
```

**Usage:**
```python
# Start pipeline with checkpointing
pipeline_id = await orchestrator.run(
    document_id=doc_id,
    enable_checkpoint=True
)

# Resume failed pipeline
await orchestrator.resume(pipeline_id)
```

### 4. **Retry System**

Automatic retry with configurable strategies for transient failures.

**Supported Strategies:**
- **Fixed**: Constant delay between retries
- **Exponential**: Backoff with 2^n growth
- **Linear**: Linear increase in delay

**Default Configuration:**
```python
# OCR Stage
max_retries=3, strategy=EXPONENTIAL, base_delay=2.0s, max_delay=30.0s

# LLM Correction Stage
max_retries=5, strategy=EXPONENTIAL, base_delay=1.0s, max_delay=60.0s

# Embedding Stage
max_retries=3, strategy=EXPONENTIAL, base_delay=2.0s, max_delay=45.0s

# Vector Index Stage
max_retries=5, strategy=EXPONENTIAL, base_delay=1.0s, max_delay=30.0s
```

**Custom Configuration:**
```python
orchestrator.job_manager.configure_retry(
    stage_name="ocr_extraction",
    max_retries=5,
    strategy=RetryStrategy.EXPONENTIAL,
    base_delay=3.0,
    max_delay=60.0
)
```

### 5. **Fallback System**

Graceful degradation when primary operations fail.

**Usage:**
```python
# Register fallback for OCR stage
async def ocr_fallback(context):
    # Use alternative OCR provider
    return await easy_ocr.execute(context)

orchestrator.register_fallback("ocr_extraction", ocr_fallback)
```

### 6. **Job Control**

Full control over job execution lifecycle.

**Operations:**
- **Start**: Begin processing with options
- **Pause**: Temporarily halt running job
- **Resume**: Continue from checkpoint
- **Cancel**: Stop and cleanup job
- **Status**: Get detailed progress

### 7. **Enhanced Logging**

Structured JSON logging for all job events.

**Log Events:**
- `job_created`, `job_started`, `job_completed`, `job_failed`
- `stage_cache_hit`, `stage_retrying`, `stage_failed_retrying`
- `checkpoint_saved`, `job_resumed_from_checkpoint`

## 📡 API Endpoints

### Pipeline Management

#### Start Pipeline
```http
POST /api/v1/pipeline/start?document_id=1&enable_cache=true&enable_checkpoint=true
```

**Response:**
```json
{
  "pipeline_id": "uuid",
  "document_id": 1,
  "status": "started",
  "features": {
    "cache_enabled": true,
    "checkpoint_enabled": true
  }
}
```

#### Pause Pipeline
```http
POST /api/v1/pipeline/pause/{pipeline_id}
```

#### Resume Pipeline
```http
POST /api/v1/pipeline/resume/{pipeline_id}
```

#### Cancel Pipeline
```http
POST /api/v1/pipeline/cancel/{pipeline_id}
```

#### Get Job Status
```http
GET /api/v1/jobs/{job_id}/status
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "running",
  "progress": 57.14,
  "current_stage": "embedding",
  "completed_stages": ["upload_validation", "ocr_extraction", "chunking"],
  "total_stages": 7,
  "retry_count": 1,
  "error_message": null,
  "created_at": "2024-01-01T00:00:00",
  "started_at": "2024-01-01T00:00:01",
  "completed_at": null
}
```

#### Clear Job Cache
```http
POST /api/v1/jobs/{job_id}/cache/clear
```

## 🔧 Configuration

All settings are in `core/config/settings.py`:

```python
# Cache settings
CACHE_DEFAULT_TTL_HOURS = 24
CACHE_MAX_SIZE_MB = 1000

# Checkpoint settings
CHECKPOINT_ENABLED = True
CHECKPOINT_INTERVAL_SECONDS = 30

# Retry settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 1.0
DEFAULT_RETRY_MAX_DELAY = 60.0

# Job settings
JOB_TIMEOUT_SECONDS = 3600
MAX_CONCURRENT_JOBS = 5

# Directories
CACHE_DIR = PROJECT_ROOT / "cache"
CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
LOGS_DIR = PROJECT_ROOT / "logs"
INDEXES_DIR = PROJECT_ROOT / "indexes"
TEMP_DIR = PROJECT_ROOT / "temp"
PLUGINS_DIR = PROJECT_ROOT / "plugins"
```

## 📊 Job States

```
PENDING → RUNNING → COMPLETED
              ↓
           FAILED → RETRYING → RUNNING
              ↓
           PAUSED → RESUMED → RUNNING
              ↓
           CANCELLED
```

## 🎯 Usage Examples

### Basic Pipeline with All Features
```python
from ragstudio.core.database.database import Database
from ragstudio.pipeline.orchestrator import PipelineOrchestrator

# Initialize
db = Database()
orchestrator = PipelineOrchestrator(db=db)

# Start pipeline with production features
pipeline_id = await orchestrator.run(
    document_id=1,
    enable_cache=True,
    enable_checkpoint=True
)

# Monitor progress
status = orchestrator.get_job_status(pipeline_id)
print(f"Progress: {status['progress']}%")
print(f"Current Stage: {status['current_stage']}")

# Handle failure - resume from checkpoint
if status['status'] == 'failed':
    await orchestrator.resume(pipeline_id)

# Pause if needed
await orchestrator.pause(pipeline_id)

# Cancel if required
await orchestrator.cancel(pipeline_id)
```

### Custom Retry Configuration
```python
# Configure custom retry for embedding stage
orchestrator.job_manager.configure_retry(
    stage_name="embedding",
    max_retries=10,
    strategy=RetryStrategy.LINEAR,
    base_delay=5.0,
    max_delay=120.0
)
```

### Register Fallback Handler
```python
# Fallback to secondary OCR provider
async def fallback_ocr(context):
    from ragstudio.core.providers.ocr.easyocr import EasyOCRProvider
    provider = EasyOCRProvider()
    return await provider.execute(context)

orchestrator.register_fallback("ocr_extraction", fallback_ocr)
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Job Manager                        │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │    Cache     │  │  Checkpoint  │  │  Fallback │ │
│  │   Manager    │  │   Manager    │  │  Manager  │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │          Retry Engine (Configurable)         │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│              Pipeline Orchestrator                  │
│  Upload → OCR → LLM → Clean → Chunk → Embed → Index │
└─────────────────────────────────────────────────────┘
```

## 🎁 Benefits

1. **Reliability**: Automatic recovery from failures
2. **Efficiency**: Cache prevents redundant computation
3. **Resumability**: Pick up where you left off
4. **Flexibility**: Configurable retry and fallback strategies
5. **Observability**: Detailed logging and status tracking
6. **Control**: Pause, resume, cancel jobs on demand
7. **Scalability**: Ready for production workloads

## 📝 Best Practices

1. **Always enable checkpointing** for large documents
2. **Use caching** when processing similar documents
3. **Configure appropriate retry limits** based on stage criticality
4. **Register fallbacks** for critical stages (OCR, Embedding)
5. **Monitor job status** via API or logs
6. **Clear cache periodically** to manage disk space
7. **Set reasonable timeouts** based on document size

## 🔍 Monitoring

Check logs in `/workspace/ragstudio/logs/`:
```bash
tail -f logs/pipeline_*.log
```

Monitor job status:
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}/status
```

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready ✅
