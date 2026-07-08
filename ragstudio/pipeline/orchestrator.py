"""
Pipeline orchestrator - manages execution of pipeline stages
"""
import asyncio
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from ragstudio.pipeline.base import PipelineContext, PipelineStage, StageResult
from ragstudio.core.database.database import Database


class PipelineOrchestrator:
    """Orchestrates the execution of pipeline stages"""
    
    def __init__(self, db: Database):
        self.db = db
        self.stages: Dict[str, PipelineStage] = {}
    
    def register_stage(self, stage: PipelineStage):
        """Register a pipeline stage"""
        self.stages[stage.name] = stage
    
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
        stage_order: Optional[List[str]] = None
    ) -> str:
        """
        Run the pipeline for a document
        
        Args:
            document_id: ID of the document to process
            config: Pipeline configuration
            stage_order: Optional custom order of stages
            
        Returns:
            Pipeline session ID
        """
        config = config or {}
        stage_order = stage_order or self.get_default_stage_order()
        
        # Create pipeline session
        pipeline_id = str(uuid.uuid4())
        
        self.db.create_pipeline_session(
            pipeline_id=pipeline_id,
            document_id=document_id,
            stage_order=stage_order,
            context_data={"config": config}
        )
        
        # Initialize context
        context = PipelineContext(
            document_id=document_id,
            pipeline_id=pipeline_id
        )
        
        # Execute stages
        completed_stages = []
        
        try:
            for stage_name in stage_order:
                if stage_name not in self.stages:
                    raise ValueError(f"Unknown stage: {stage_name}")
                
                stage = self.stages[stage_name]
                
                # Update status
                self.db.update_pipeline_status(
                    pipeline_id=pipeline_id,
                    status="running",
                    current_stage=stage_name,
                    completed_stages=completed_stages
                )
                
                try:
                    # Before hook
                    context = await stage.before_execute(context)
                    
                    # Execute stage
                    context = await stage.execute(context)
                    
                    # After hook
                    context = await stage.after_execute(context)
                    
                    # Check for errors
                    if context.has_errors():
                        raise Exception(f"Stage {stage_name} reported errors: {context.errors}")
                    
                    completed_stages.append(stage_name)
                    
                except Exception as e:
                    # Handle stage error
                    context = await stage.on_error(context, e)
                    self.db.update_pipeline_status(
                        pipeline_id=pipeline_id,
                        status="failed",
                        current_stage=stage_name,
                        completed_stages=completed_stages,
                        failed_stage=stage_name,
                        error_message=str(e)
                    )
                    raise
            
            # All stages completed successfully
            self.db.update_pipeline_status(
                pipeline_id=pipeline_id,
                status="completed",
                current_stage=None,
                completed_stages=completed_stages
            )
            
            # Update document status
            self.db.update_document_status(document_id, "processed")
            
        except Exception as e:
            # Pipeline failed
            self.db.update_pipeline_status(
                pipeline_id=pipeline_id,
                status="failed",
                error_message=str(e)
            )
            raise
        
        return pipeline_id
    
    async def resume(self, pipeline_id: str) -> str:
        """
        Resume a failed pipeline from the last successful stage
        
        Args:
            pipeline_id: ID of the pipeline to resume
            
        Returns:
            Pipeline session ID
        """
        session = self.db.get_pipeline_session(pipeline_id)
        
        if not session:
            raise ValueError(f"Pipeline session not found: {pipeline_id}")
        
        if session["status"] not in ["failed", "paused"]:
            raise ValueError(f"Cannot resume pipeline with status: {session['status']}")
        
        stage_order = session["stage_order"]
        completed_stages = session.get("completed_stages", [])
        document_id = session["document_id"]
        config = session.get("context_data", {}).get("config", {})
        
        # Find the next stage to execute
        remaining_stages = [s for s in stage_order if s not in completed_stages]
        
        if not remaining_stages:
            raise ValueError("No remaining stages to execute")
        
        # Initialize context
        context = PipelineContext(
            document_id=document_id,
            pipeline_id=pipeline_id,
            data=session.get("context_data", {}).get("data", {})
        )
        
        # Execute remaining stages
        try:
            for stage_name in remaining_stages:
                if stage_name not in self.stages:
                    raise ValueError(f"Unknown stage: {stage_name}")
                
                stage = self.stages[stage_name]
                
                # Update status
                self.db.update_pipeline_status(
                    pipeline_id=pipeline_id,
                    status="running",
                    current_stage=stage_name,
                    completed_stages=completed_stages
                )
                
                try:
                    context = await stage.before_execute(context)
                    context = await stage.execute(context)
                    context = await stage.after_execute(context)
                    
                    if context.has_errors():
                        raise Exception(f"Stage {stage_name} reported errors: {context.errors}")
                    
                    completed_stages.append(stage_name)
                    
                except Exception as e:
                    context = await stage.on_error(context, e)
                    self.db.update_pipeline_status(
                        pipeline_id=pipeline_id,
                        status="failed",
                        current_stage=stage_name,
                        completed_stages=completed_stages,
                        failed_stage=stage_name,
                        error_message=str(e)
                    )
                    raise
            
            # All stages completed successfully
            self.db.update_pipeline_status(
                pipeline_id=pipeline_id,
                status="completed",
                current_stage=None,
                completed_stages=completed_stages
            )
            
            # Update document status
            self.db.update_document_status(document_id, "processed")
            
        except Exception as e:
            self.db.update_pipeline_status(
                pipeline_id=pipeline_id,
                status="failed",
                error_message=str(e)
            )
            raise
        
        return pipeline_id
    
    def save_checkpoint(self, pipeline_id: str, context: PipelineContext):
        """Save pipeline checkpoint for resumption"""
        from ragstudio.core.config.settings import PIPELINE_STATUS_DIR
        
        checkpoint_file = PIPELINE_STATUS_DIR / f"{pipeline_id}.json"
        
        checkpoint_data = {
            "pipeline_id": pipeline_id,
            "timestamp": datetime.now().isoformat(),
            "context_data": context.data,
            "metadata": context.metadata
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
    
    def load_checkpoint(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Load pipeline checkpoint"""
        from ragstudio.core.config.settings import PIPELINE_STATUS_DIR
        
        checkpoint_file = PIPELINE_STATUS_DIR / f"{pipeline_id}.json"
        
        if not checkpoint_file.exists():
            return None
        
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
