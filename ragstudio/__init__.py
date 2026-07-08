"""
RAG Studio - Modular Document Ingestion and RAG Platform
"""

__version__ = "1.0.0"
__author__ = "RAG Studio Team"

from .pipeline import (
    PipelineStage,
    PipelineContext,
    UploadValidationStage,
    OCRExtractionStage,
    TextCleaningStage,
    LLMCorrectionStage,
    ChunkingStage,
    EmbeddingStage,
    VectorIndexStage
)

from .core.database.database import Database
from .pipeline.orchestrator import PipelineOrchestrator

__all__ = [
    # Pipeline stages
    "PipelineStage",
    "PipelineContext",
    "UploadValidationStage",
    "OCRExtractionStage",
    "TextCleaningStage",
    "LLMCorrectionStage",
    "ChunkingStage",
    "EmbeddingStage",
    "VectorIndexStage",
    
    # Core components
    "Database",
    "PipelineOrchestrator",
    
    # Version
    "__version__"
]
