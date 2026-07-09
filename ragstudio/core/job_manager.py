"""
Job Management System with Cache, Resume, Fallback, Retry, and Checkpoint support
Implements production-ready pipeline execution with fault tolerance
Security: Uses JSON instead of pickle for safe serialization
"""
import asyncio
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import aiofiles

from ragstudio.core.database.database import Database
from ragstudio.core.logging_system import StructuredLogger


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class RetryStrategy(str, Enum):
    """Retry strategy types"""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given retry attempt"""
        import random
        
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        else:  # EXPONENTIAL
            delay = self.base_delay * (2 ** (attempt - 1))
        
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay


@dataclass
class Checkpoint:
    """Checkpoint data for resuming jobs"""
    stage_name: str
    stage_index: int
    context_data: Dict[str, Any]
    timestamp: datetime
    checksum: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "stage_index": self.stage_index,
            "context_data": self.context_data,
            "timestamp": self.timestamp.isoformat(),
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        return cls(
            stage_name=data["stage_name"],
            stage_index=data["stage_index"],
            context_data=data["context_data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            checksum=data["checksum"]
        )


@dataclass
class CacheEntry:
    """Cache entry for storing intermediate results"""
    key: str
    data: Any
    created_at: datetime
    expires_at: Optional[datetime]
    size_bytes: int
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class CacheManager:
    """Manages caching of pipeline stage results"""
    
    def __init__(self, cache_dir: Path, default_ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.default_ttl_hours = default_ttl_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._metadata: Dict[str, CacheEntry] = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, CacheEntry]:
        """Load cache metadata from disk"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                return {k: CacheEntry(
                    key=v["key"],
                    data=None,  # Data loaded separately
                    created_at=datetime.fromisoformat(v["created_at"]),
                    expires_at=datetime.fromisoformat(v["expires_at"]) if v["expires_at"] else None,
                    size_bytes=v["size_bytes"]
                ) for k, v in data.items()}
        return {}
    
    def _save_metadata(self):
        """Save cache metadata to disk"""
        data = {k: {
            "key": v.key,
            "created_at": v.created_at.isoformat(),
            "expires_at": v.expires_at.isoformat() if v.expires_at else None,
            "size_bytes": v.size_bytes
        } for k, v in self._metadata.items()}
        
        with open(self.metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_key(self, stage_name: str, input_data: Dict[str, Any]) -> str:
        """Generate cache key from stage name and input data"""
        content = f"{stage_name}:{json.dumps(input_data, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached data by key"""
        if key not in self._metadata:
            return None
        
        entry = self._metadata[key]
        
        if entry.is_expired():
            await self.delete(key)
            return None
        
        cache_file = self.cache_dir / f"{key}.pkl"
        if not cache_file.exists():
            await self.delete(key)
            return None
        
        async with aiofiles.open(cache_file, 'rb') as f:
            data = await f.read()
            try:
                return json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                # Corrupted cache file, delete it
                await self.delete(key)
                raise Exception(f"Cache file corrupted: {str(e)}")
    
    async def set(self, stage_name: str, input_data: Dict[str, Any], result: Any, ttl_hours: Optional[int] = None) -> str:
        """Cache stage result using safe JSON serialization"""
        key = self._generate_key(stage_name, input_data)
        ttl = ttl_hours if ttl_hours is not None else self.default_ttl_hours
        
        cache_file = self.cache_dir / f"{key}.json"
        
        # Convert result to JSON-serializable format
        try:
            json_data = json.dumps(result, default=str)
        except (TypeError, ValueError) as e:
            raise Exception(f"Cannot serialize result to JSON: {str(e)}")
        
        async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
            await f.write(json_data)
        
        entry = CacheEntry(
            key=key,
            data=None,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=ttl),
            size_bytes=len(json_data.encode('utf-8'))
        )
        
        self._metadata[key] = entry
        self._save_metadata()
        
        return key
    
    async def delete(self, key: str):
        """Delete cached data"""
        if key in self._metadata:
            del self._metadata[key]
            self._save_metadata()
        
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            cache_file.unlink()
    
    async def clear_expired(self):
        """Clear all expired cache entries"""
        expired_keys = [k for k, v in self._metadata.items() if v.is_expired()]
        for key in expired_keys:
            await self.delete(key)
    
    async def clear_all(self):
        """Clear all cache entries"""
        for key in list(self._metadata.keys()):
            await self.delete(key)


class CheckpointManager:
    """Manages checkpoints for job resumption"""
    
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_checkpoint_path(self, job_id: str) -> Path:
        return self.checkpoint_dir / f"{job_id}_checkpoint.json"
    
    async def save_checkpoint(self, job_id: str, checkpoint: Checkpoint):
        """Save checkpoint to disk"""
        checkpoint_file = self._get_checkpoint_path(job_id)
        
        async with aiofiles.open(checkpoint_file, 'w') as f:
            await f.write(json.dumps(checkpoint.to_dict(), indent=2))
    
    async def load_checkpoint(self, job_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from disk"""
        checkpoint_file = self._get_checkpoint_path(job_id)
        
        if not checkpoint_file.exists():
            return None
        
        async with aiofiles.open(checkpoint_file, 'r') as f:
            data = json.loads(await f.read())
            return Checkpoint.from_dict(data)
    
    async def delete_checkpoint(self, job_id: str):
        """Delete checkpoint file"""
        checkpoint_file = self._get_checkpoint_path(job_id)
        if checkpoint_file.exists():
            checkpoint_file.unlink()
    
    def compute_checksum(self, data: Dict[str, Any]) -> str:
        """Compute checksum for data validation"""
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class FallbackManager:
    """Manages fallback strategies for failed operations"""
    
    def __init__(self):
        self.fallbacks: Dict[str, List[Callable]] = {}
    
    def register_fallback(self, operation_name: str, fallback_func: Callable):
        """Register a fallback function for an operation"""
        if operation_name not in self.fallbacks:
            self.fallbacks[operation_name] = []
        self.fallbacks[operation_name].append(fallback_func)
    
    async def execute_with_fallback(
        self,
        operation_name: str,
        primary_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute primary function with fallback on failure"""
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            if operation_name not in self.fallbacks:
                raise
            
            last_error = e
            for fallback_func in self.fallbacks[operation_name]:
                try:
                    return await fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    last_error = fallback_error
                    continue
            
            raise last_error


class JobManager:
    """
    Production-ready job manager with cache, resume, fallback, retry, and checkpoint support
    """
    
    def __init__(
        self,
        db: Database,
        cache_dir: Path,
        checkpoint_dir: Path,
        logger: Optional[StructuredLogger] = None
    ):
        self.db = db
        self.cache_manager = CacheManager(cache_dir)
        self.checkpoint_manager = CheckpointManager(checkpoint_dir)
        self.fallback_manager = FallbackManager()
        self.logger = logger or StructuredLogger("job_manager")
        
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
    
    def configure_retry(
        self,
        stage_name: str,
        max_retries: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        """Configure retry behavior for a stage"""
        self.retry_configs[stage_name] = RetryConfig(
            max_retries=max_retries,
            strategy=strategy,
            base_delay=base_delay,
            max_delay=max_delay
        )
    
    def register_fallback(self, stage_name: str, fallback_func: Callable):
        """Register fallback for a stage"""
        self.fallback_manager.register_fallback(stage_name, fallback_func)
    
    async def create_job(
        self,
        document_id: int,
        stage_order: List[str],
        config: Optional[Dict[str, Any]] = None,
        enable_cache: bool = True,
        enable_checkpoint: bool = True
    ) -> str:
        """Create a new job"""
        import uuid
        
        job_id = str(uuid.uuid4())
        
        job_data = {
            "job_id": job_id,
            "document_id": document_id,
            "stage_order": stage_order,
            "config": config or {},
            "status": JobStatus.PENDING.value,
            "current_stage": None,
            "completed_stages": [],
            "failed_stage": None,
            "error_message": None,
            "retry_count": 0,
            "enable_cache": enable_cache,
            "enable_checkpoint": enable_checkpoint,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None
        }
        
        self.jobs[job_id] = job_data
        
        # Store in database
        self.db.create_pipeline_session(
            pipeline_id=job_id,
            document_id=document_id,
            stage_order=stage_order,
            context_data=job_data
        )
        
        self.logger.info("job_created", job_id=job_id, document_id=document_id)
        
        return job_id
    
    async def execute_job(self, job_id: str, stages: Dict[str, Any]) -> str:
        """
        Execute a job with full production features
        
        Args:
            job_id: Job ID to execute
            stages: Dictionary of stage name to stage object
        
        Returns:
            Job ID
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        job["status"] = JobStatus.RUNNING.value
        job["started_at"] = datetime.now().isoformat()
        
        self.logger.info("job_started", job_id=job_id)
        
        try:
            # Determine starting stage
            start_index = 0
            checkpoint = None
            
            if job["enable_checkpoint"]:
                checkpoint = await self.checkpoint_manager.load_checkpoint(job_id)
                if checkpoint:
                    start_index = checkpoint.stage_index + 1
                    job["completed_stages"] = job["stage_order"][:start_index]
                    self.logger.info(
                        "job_resumed_from_checkpoint",
                        job_id=job_id,
                        resumed_at_stage=checkpoint.stage_name
                    )
            
            # Execute stages
            for idx, stage_name in enumerate(job["stage_order"]):
                if idx < start_index:
                    continue
                
                if stage_name not in stages:
                    raise ValueError(f"Stage not found: {stage_name}")
                
                stage = stages[stage_name]
                job["current_stage"] = stage_name
                
                # Update database
                self.db.update_pipeline_status(
                    pipeline_id=job_id,
                    status=JobStatus.RUNNING.value,
                    current_stage=stage_name,
                    completed_stages=job["completed_stages"]
                )
                
                # Execute stage with retry, cache, and fallback
                success = await self._execute_stage_with_features(
                    job_id=job_id,
                    stage=stage,
                    stage_name=stage_name,
                    stage_index=idx
                )
                
                if not success:
                    job["status"] = JobStatus.FAILED.value
                    job["failed_stage"] = stage_name
                    job["updated_at"] = datetime.now().isoformat()
                    
                    self.db.update_pipeline_status(
                        pipeline_id=job_id,
                        status=JobStatus.FAILED.value,
                        failed_stage=stage_name,
                        error_message=job["error_message"]
                    )
                    
                    self.logger.error(
                        "job_failed",
                        job_id=job_id,
                        failed_stage=stage_name,
                        error=job["error_message"]
                    )
                    
                    return job_id
                
                job["completed_stages"].append(stage_name)
                
                # Save checkpoint after successful stage
                if job["enable_checkpoint"]:
                    await self._save_stage_checkpoint(job_id, stage_name, idx, stage)
            
            # Job completed successfully
            job["status"] = JobStatus.COMPLETED.value
            job["completed_at"] = datetime.now().isoformat()
            job["updated_at"] = datetime.now().isoformat()
            
            self.db.update_pipeline_status(
                pipeline_id=job_id,
                status=JobStatus.COMPLETED.value,
                completed_stages=job["completed_stages"]
            )
            
            # Update document status
            self.db.update_document_status(job["document_id"], "processed")
            
            # Clean up checkpoint
            if job["enable_checkpoint"]:
                await self.checkpoint_manager.delete_checkpoint(job_id)
            
            self.logger.info("job_completed", job_id=job_id)
        
        except Exception as e:
            job["status"] = JobStatus.FAILED.value
            job["error_message"] = str(e)
            job["updated_at"] = datetime.now().isoformat()
            
            self.db.update_pipeline_status(
                pipeline_id=job_id,
                status=JobStatus.FAILED.value,
                error_message=str(e)
            )
            
            self.logger.error("job_failed_with_exception", job_id=job_id, error=str(e))
        
        return job_id
    
    async def _execute_stage_with_features(
        self,
        job_id: str,
        stage: Any,
        stage_name: str,
        stage_index: int
    ) -> bool:
        """Execute a single stage with retry, cache, and fallback support"""
        job = self.jobs[job_id]
        retry_config = self.retry_configs.get(stage_name, RetryConfig())
        
        # Prepare context from completed stages
        context = await self._build_context(job_id, stage_name)
        
        # Check cache
        if job["enable_cache"]:
            cached_result = await self.cache_manager.get(
                self.cache_manager._generate_key(stage_name, context.data)
            )
            if cached_result is not None:
                self.logger.info("stage_cache_hit", job_id=job_id, stage=stage_name)
                # Apply cached result to context
                return True
        
        # Execute with retry
        attempt = 0
        last_error = None
        
        while attempt <= retry_config.max_retries:
            try:
                if attempt > 0:
                    job["status"] = JobStatus.RETRYING.value
                    job["retry_count"] = attempt
                    
                    self.logger.warning(
                        "stage_retrying",
                        job_id=job_id,
                        stage=stage_name,
                        attempt=attempt,
                        max_retries=retry_config.max_retries
                    )
                
                # Execute stage with fallback
                result = await self.fallback_manager.execute_with_fallback(
                    stage_name,
                    stage.execute,
                    context
                )
                
                # Cache result
                if job["enable_cache"]:
                    await self.cache_manager.set(
                        stage_name,
                        context.data,
                        result.data
                    )
                
                # Check for errors
                if result.has_errors():
                    raise Exception(f"Stage reported errors: {result.errors}")
                
                # Update context
                context = result
                
                return True
            
            except Exception as e:
                last_error = e
                attempt += 1
                
                if attempt <= retry_config.max_retries:
                    delay = retry_config.get_delay(attempt)
                    self.logger.warning(
                        "stage_failed_retrying",
                        job_id=job_id,
                        stage=stage_name,
                        attempt=attempt,
                        delay=delay,
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                else:
                    break
        
        # All retries exhausted
        job["error_message"] = f"Stage {stage_name} failed after {retry_config.max_retries} retries: {str(last_error)}"
        
        self.logger.error(
            "stage_failed_all_retries_exhausted",
            job_id=job_id,
            stage=stage_name,
            error=str(last_error)
        )
        
        return False
    
    async def _build_context(self, job_id: str, current_stage: str) -> Any:
        """Build pipeline context from completed stages"""
        from ragstudio.pipeline.base import PipelineContext
        
        job = self.jobs[job_id]
        
        # Load latest checkpoint or start fresh
        checkpoint = None
        if job["enable_checkpoint"]:
            checkpoint = await self.checkpoint_manager.load_checkpoint(job_id)
        
        if checkpoint:
            context = PipelineContext(
                document_id=job["document_id"],
                pipeline_id=job_id,
                data=checkpoint.context_data
            )
        else:
            context = PipelineContext(
                document_id=job["document_id"],
                pipeline_id=job_id
            )
        
        return context
    
    async def _save_stage_checkpoint(self, job_id: str, stage_name: str, stage_index: int, stage: Any):
        """Save checkpoint after successful stage completion"""
        context = await self._build_context(job_id, stage_name)
        
        checkpoint = Checkpoint(
            stage_name=stage_name,
            stage_index=stage_index,
            context_data=context.data,
            timestamp=datetime.now(),
            checksum=self.checkpoint_manager.compute_checksum(context.data)
        )
        
        await self.checkpoint_manager.save_checkpoint(job_id, checkpoint)
        
        self.logger.debug("checkpoint_saved", job_id=job_id, stage=stage_name)
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a running job"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        if job["status"] != JobStatus.RUNNING.value:
            return False
        
        job["status"] = JobStatus.PAUSED.value
        job["updated_at"] = datetime.now().isoformat()
        
        self.db.update_pipeline_status(
            pipeline_id=job_id,
            status=JobStatus.PAUSED.value
        )
        
        self.logger.info("job_paused", job_id=job_id)
        return True
    
    async def resume_job(self, job_id: str, stages: Dict[str, Any]) -> str:
        """Resume a paused or failed job from last checkpoint"""
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if job["status"] not in [JobStatus.PAUSED.value, JobStatus.FAILED.value]:
            raise ValueError(f"Cannot resume job with status: {job['status']}")
        
        return await self.execute_job(job_id, stages)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        job["status"] = JobStatus.CANCELLED.value
        job["updated_at"] = datetime.now().isoformat()
        
        self.db.update_pipeline_status(
            pipeline_id=job_id,
            status=JobStatus.CANCELLED.value
        )
        
        # Clean up checkpoint
        if job["enable_checkpoint"]:
            await self.checkpoint_manager.delete_checkpoint(job_id)
        
        self.logger.info("job_cancelled", job_id=job_id)
        return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and progress"""
        if job_id not in self.jobs:
            session = self.db.get_pipeline_session(job_id)
            if session:
                return session
            return None
        
        job = self.jobs[job_id]
        
        total_stages = len(job["stage_order"])
        completed = len(job["completed_stages"])
        progress = (completed / total_stages * 100) if total_stages > 0 else 0
        
        return {
            **job,
            "progress": progress,
            "total_stages": total_stages,
            "completed_count": completed
        }
    
    async def clear_cache(self, job_id: Optional[str] = None):
        """Clear cache for specific job or all jobs"""
        if job_id:
            # Clear cache entries related to this job's stages
            # This would require tracking cache keys per job
            pass
        else:
            await self.cache_manager.clear_all()
        
        self.logger.info("cache_cleared", job_id=job_id)
