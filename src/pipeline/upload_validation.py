"""
Upload validation stage - validates uploaded documents
"""
from pathlib import Path
from typing import Dict, Any, Optional

from src.pipeline.base import PipelineStage, PipelineContext


class UploadValidationStage(PipelineStage):
    """Validates uploaded documents before processing"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("upload_validation", config)
        self.allowed_extensions = config.get("allowed_extensions", {".pdf"})
        self.max_file_size_mb = config.get("max_file_size_mb", 100)
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute upload validation"""
        from config.settings import UPLOAD_DIR
        
        document_id = context.document_id
        
        # Get document info from database
        doc = context.get("document_info")
        if not doc:
            db = context.get("db")
            if db:
                doc = db.get_document(document_id)
                context.set("document_info", doc)
        
        if not doc:
            context.add_error(f"Document {document_id} not found")
            return context
        
        file_path = Path(doc["file_path"])
        
        # Check file exists
        if not file_path.exists():
            context.add_error(f"File not found: {file_path}")
            return context
        
        # Check file extension
        if file_path.suffix.lower() not in self.allowed_extensions:
            context.add_error(
                f"Invalid file extension: {file_path.suffix}. "
                f"Allowed: {self.allowed_extensions}"
            )
            return context
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            context.add_error(
                f"File too large: {file_size_mb:.2f}MB. "
                f"Max allowed: {self.max_file_size_mb}MB"
            )
            return context
        
        # Store validated file path
        context.set("file_path", str(file_path))
        context.set("filename", doc["filename"])
        
        return context
