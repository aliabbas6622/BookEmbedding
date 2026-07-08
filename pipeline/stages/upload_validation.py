"""
Stage 1: File Upload and Validation
Handles PDF file upload, validation, and storage
"""
import os
import hashlib
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from pipeline.stages.base import PipelineStage, StageResult, PipelineContext


class UploadValidationStage(PipelineStage):
    """Stage 1: Upload and validate PDF files"""
    
    @property
    def name(self) -> str:
        return "upload_validation"
    
    @property
    def description(self) -> str:
        return "Upload and validate PDF files"
    
    @property
    def required_inputs(self) -> List[str]:
        return ["file_paths"]
    
    @property
    def outputs(self) -> List[str]:
        return ["validated_files", "file_metadata"]
    
    def __init__(self, upload_dir: str, max_file_size_mb: int = 100):
        self.upload_dir = Path(upload_dir)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.allowed_extensions = {".pdf"}
    
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute upload validation stage"""
        started_at = datetime.now()
        
        try:
            file_paths = context.get("file_paths")
            if not file_paths:
                return StageResult(
                    success=False,
                    message="No file paths provided",
                    started_at=started_at,
                    completed_at=datetime.now()
                )
            
            # Ensure upload directory exists
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            
            validated_files = []
            file_metadata = []
            
            for file_path_str in file_paths:
                file_path = Path(file_path_str)
                
                # Validate file exists
                if not file_path.exists():
                    context.add_error(f"File not found: {file_path}")
                    continue
                
                # Validate extension
                if file_path.suffix.lower() not in self.allowed_extensions:
                    context.add_error(f"Invalid file type: {file_path.suffix}")
                    continue
                
                # Validate file size
                file_size = file_path.stat().st_size
                if file_size > self.max_file_size_bytes:
                    context.add_error(f"File too large: {file_path} ({file_size} bytes)")
                    continue
                
                # Calculate file hash
                file_hash = self._calculate_hash(file_path)
                
                # Copy file to upload directory
                dest_path = self.upload_dir / f"{context.session_id}_{file_path.name}"
                
                # Read and write to handle potential path issues
                with open(file_path, 'rb') as src:
                    with open(dest_path, 'wb') as dst:
                        dst.write(src.read())
                
                validated_files.append(str(dest_path))
                file_metadata.append({
                    "original_name": file_path.name,
                    "stored_path": str(dest_path),
                    "size": file_size,
                    "hash": file_hash,
                    "extension": file_path.suffix.lower(),
                    "uploaded_at": datetime.now().isoformat()
                })
            
            if not validated_files:
                return StageResult(
                    success=False,
                    message="No valid files after validation",
                    error="; ".join(context.errors),
                    started_at=started_at,
                    completed_at=datetime.now()
                )
            
            context.set("validated_files", validated_files)
            context.set("file_metadata", file_metadata)
            
            return StageResult(
                success=True,
                message=f"Validated {len(validated_files)} file(s)",
                data={
                    "validated_files": validated_files,
                    "file_metadata": file_metadata
                },
                started_at=started_at,
                completed_at=datetime.now()
            )
            
        except Exception as e:
            return StageResult(
                success=False,
                message=f"Upload validation failed: {str(e)}",
                error=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
