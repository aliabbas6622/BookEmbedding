"""
Pipeline orchestrator - manages execution of pipeline stages
Integrated with JobManager for production-ready features
"""
import asyncio
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from ragstudio.pipeline.base import PipelineContext, PipelineStage, StageResult
from ragstudio.core.database.database import Database
from ragstudio.core.job_manager import JobManager, JobStatus, RetryStrategy


class PipelineOrchestrator:
    """Orchestrates the execution of pipeline stages with production features"""
    
    def __init__(
        self,
        db: Database,
        cache_dir: Optional[Path] = None,
        checkpoint_dir: Optional[Path] = None
    ):
        self.db = db
        self.stages: Dict[str, PipelineStage] = {}
        
        # Initialize job manager with production features
        from config.settings import CACHE_DIR, CHECKPOINT_DIR
        
        self.job_manager = JobManager(
            db=db,
            cache_dir=cache_dir or CACHE_DIR,
            checkpoint_dir=checkpoint_dir or CHECKPOINT_DIR
        )
        
        # Configure default retry strategies for each stage
        self._configure_default_retries()
    
    def register_stage(self, stage: PipelineStage):
        """Register a pipeline stage"""
        self.stages[stage.name] = stage
    
    def _configure_default_retries(self):
        """Configure default retry strategies for each stage"""
        # OCR might fail due to resource constraints - retry with exponential backoff
        self.job_manager.configure_retry(
            stage_name="ocr_extraction",
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=2.0,
            max_delay=30.0
        )
        
        # LLM correction might have API rate limits
        self.job_manager.configure_retry(
            stage_name="llm_correction",
            max_retries=5,
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            max_delay=60.0
        )
        
        # Embedding generation might fail due to API issues
        self.job_manager.configure_retry(
            stage_name="embedding",
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=2.0,
            max_delay=45.0
        )
        
        # Vector indexing is critical - more retries
        self.job_manager.configure_retry(
            stage_name="vector_index",
            max_retries=5,
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            max_delay=30.0
        )
    
    def get_default_stage_order(self) -> List[str]:
        """Get default order of stages"""
        return [
            "upload_validation",
            "ocr_extraction",
            "llm_correction",  # Optional stage for OCR correction
            "text_cleaning",
            "chunking",
            "embedding",
            "vector_index"
        ]
    
    async def run(
        self,
        document_id: int,
        config: Optional[Dict[str, Any]] = None,
        stage_order: Optional[List[str]] = None,
        enable_cache: bool = True,
        enable_checkpoint: bool = True
    ) -> str:
        """
        Run the pipeline for a document with production features
        
        Args:
            document_id: ID of the document to process
            config: Pipeline configuration
            stage_order: Optional custom order of stages
            enable_cache: Enable caching of stage results
            enable_checkpoint: Enable checkpointing for resumption
            
        Returns:
            Pipeline session ID (job ID)
        """
        config = config or {}
        stage_order = stage_order or self.get_default_stage_order()
        
        # Create job with JobManager
        job_id = await self.job_manager.create_job(
            document_id=document_id,
            stage_order=stage_order,
            config=config,
            enable_cache=enable_cache,
            enable_checkpoint=enable_checkpoint
        )
        
        # Execute job asynchronously
        asyncio.create_task(self.job_manager.execute_job(job_id, self.stages))
        
        return job_id
    
    async def resume(self, pipeline_id: str) -> str:
        """
        Resume a failed or paused pipeline from the last successful checkpoint
        
        Args:
            pipeline_id: ID of the pipeline to resume (job ID)
            
        Returns:
            Pipeline session ID
        """
        return await self.job_manager.resume_job(pipeline_id, self.stages)
    
    async def pause(self, pipeline_id: str) -> bool:
        """
        Pause a running pipeline
        
        Args:
            pipeline_id: ID of the pipeline to pause
            
        Returns:
            True if paused successfully
        """
        return await self.job_manager.pause_job(pipeline_id)
    
    async def cancel(self, pipeline_id: str) -> bool:
        """
        Cancel a pipeline job
        
        Args:
            pipeline_id: ID of the pipeline to cancel
            
        Returns:
            True if cancelled successfully
        """
        return await self.job_manager.cancel_job(pipeline_id)
    
    def get_job_status(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed job status and progress
        
        Args:
            pipeline_id: ID of the job
            
        Returns:
            Job status dictionary with progress information
        """
        return self.job_manager.get_job_status(pipeline_id)
    
    def register_fallback(self, stage_name: str, fallback_func):
        """
        Register a fallback function for a stage
        
        Args:
            stage_name: Name of the stage
            fallback_func: Fallback function to call on failure
        """
        self.job_manager.register_fallback(stage_name, fallback_func)
    
    async def clear_cache(self, job_id: Optional[str] = None):
        """
        Clear cache for specific job or all jobs
        
        Args:
            job_id: Optional job ID to clear cache for
        """
        await self.job_manager.clear_cache(job_id)
