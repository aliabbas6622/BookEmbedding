"""
RAG Studio API - FastAPI based REST API
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn

from ragstudio.core.config.settings import (
    API_HOST, API_PORT, UPLOAD_DIR, OUTPUT_DIR, 
    DEFAULT_OCR_PROVIDER, DEFAULT_LLM_PROVIDER,
    DEFAULT_EMBEDDING_PROVIDER, DEFAULT_VECTOR_INDEX_PROVIDER,
    DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
)
from ragstudio.core.database.database import Database
from ragstudio.pipeline.orchestrator import PipelineOrchestrator
from ragstudio.api.settings_routes import router as settings_router
from ragstudio.api.rag_playground import router as rag_router

# Initialize FastAPI app
app = FastAPI(
    title="RAG Studio API",
    description="Document ingestion and RAG pipeline API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(settings_router)
app.include_router(rag_router)

# Initialize database
db = Database()

# ============================================
# Pydantic Models for API Requests/Responses
# ============================================

class ProviderConfig(BaseModel):
    """Provider configuration model"""
    provider_type: str = Field(..., description="Type of provider (ocr, llm, embedding, vector_index)")
    name: str = Field(..., description="Provider name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Provider specific configuration")

class PipelineConfig(BaseModel):
    """Pipeline configuration model"""
    ocr_provider: str = Field(default=DEFAULT_OCR_PROVIDER, description="OCR provider name")
    llm_provider: str = Field(default=DEFAULT_LLM_PROVIDER, description="LLM provider name")
    embedding_provider: str = Field(default=DEFAULT_EMBEDDING_PROVIDER, description="Embedding provider name")
    vector_index_provider: str = Field(default=DEFAULT_VECTOR_INDEX_PROVIDER, description="Vector index provider name")
    chunk_size: int = Field(default=DEFAULT_CHUNK_SIZE, ge=100, le=4096, description="Chunk size for text splitting")
    chunk_overlap: int = Field(default=DEFAULT_CHUNK_OVERLAP, ge=0, le=500, description="Chunk overlap")
    custom_stages: List[str] = Field(default_factory=list, description="Custom pipeline stages to include")
    
class DocumentUploadResponse(BaseModel):
    """Document upload response model"""
    document_id: int
    filename: str
    status: str
    message: str

class PipelineStatusResponse(BaseModel):
    """Pipeline status response model"""
    pipeline_id: str
    document_id: int
    status: str
    current_stage: Optional[str]
    completed_stages: List[str]
    failed_stage: Optional[str]
    error_message: Optional[str]
    progress_percentage: float

class SearchResult(BaseModel):
    """Search result model"""
    chunk_id: int
    document_id: int
    content: str
    score: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    results: List[SearchResult]
    total_results: int

class SettingsResponse(BaseModel):
    """Settings response model"""
    providers: Dict[str, List[str]]
    defaults: Dict[str, Any]
    paths: Dict[str, str]

class SettingsUpdateRequest(BaseModel):
    """Settings update request model"""
    default_ocr_provider: Optional[str] = None
    default_llm_provider: Optional[str] = None
    default_embedding_provider: Optional[str] = None
    default_vector_index_provider: Optional[str] = None
    default_chunk_size: Optional[int] = None
    default_chunk_overlap: Optional[int] = None
    upload_directory: Optional[str] = None
    output_directory: Optional[str] = None

# ============================================
# Helper Functions
# ============================================

def get_available_providers() -> Dict[str, List[str]]:
    """Get list of available providers for each type"""
    return {
        "ocr": ["tesseract", "paddleocr", "easyocr"],
        "llm": ["ollama", "openai", "gemini", "anthropic"],
        "embedding": ["sentence_transformers", "openai", "cohere", "huggingface"],
        "vector_index": ["turbovec", "faiss", "qdrant", "chroma"]
    }

# ============================================
# API Endpoints
# ============================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to RAG Studio API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}

@app.get("/api/v1/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current API settings and available providers"""
    return SettingsResponse(
        providers=get_available_providers(),
        defaults={
            "ocr_provider": DEFAULT_OCR_PROVIDER,
            "llm_provider": DEFAULT_LLM_PROVIDER,
            "embedding_provider": DEFAULT_EMBEDDING_PROVIDER,
            "vector_index_provider": DEFAULT_VECTOR_INDEX_PROVIDER,
            "chunk_size": DEFAULT_CHUNK_SIZE,
            "chunk_overlap": DEFAULT_CHUNK_OVERLAP
        },
        paths={
            "upload_dir": str(UPLOAD_DIR),
            "output_dir": str(OUTPUT_DIR),
            "db_path": str(db.db_path)
        }
    )

@app.post("/api/v1/settings")
async def update_settings(settings: SettingsUpdateRequest):
    """Update default settings"""
    # Note: In production, you'd want to persist these to a config file or database
    updates = {}
    
    if settings.default_ocr_provider:
        if settings.default_ocr_provider not in get_available_providers()["ocr"]:
            raise HTTPException(status_code=400, detail=f"Invalid OCR provider: {settings.default_ocr_provider}")
        updates["default_ocr_provider"] = settings.default_ocr_provider
        
    if settings.default_llm_provider:
        if settings.default_llm_provider not in get_available_providers()["llm"]:
            raise HTTPException(status_code=400, detail=f"Invalid LLM provider: {settings.default_llm_provider}")
        updates["default_llm_provider"] = settings.default_llm_provider
        
    if settings.default_embedding_provider:
        if settings.default_embedding_provider not in get_available_providers()["embedding"]:
            raise HTTPException(status_code=400, detail=f"Invalid embedding provider: {settings.default_embedding_provider}")
        updates["default_embedding_provider"] = settings.default_embedding_provider
        
    if settings.default_vector_index_provider:
        if settings.default_vector_index_provider not in get_available_providers()["vector_index"]:
            raise HTTPException(status_code=400, detail=f"Invalid vector index provider: {settings.default_vector_index_provider}")
        updates["default_vector_index_provider"] = settings.default_vector_index_provider
        
    if settings.default_chunk_size:
        if not (100 <= settings.default_chunk_size <= 4096):
            raise HTTPException(status_code=400, detail="Chunk size must be between 100 and 4096")
        updates["default_chunk_size"] = settings.default_chunk_size
        
    if settings.default_chunk_overlap:
        if not (0 <= settings.default_chunk_overlap <= 500):
            raise HTTPException(status_code=400, detail="Chunk overlap must be between 0 and 500")
        updates["default_chunk_overlap"] = settings.default_chunk_overlap
    
    return {
        "message": "Settings updated successfully",
        "updated": updates
    }

@app.get("/api/v1/providers")
async def list_providers():
    """List all available providers"""
    return {
        "providers": get_available_providers(),
        "defaults": {
            "ocr": DEFAULT_OCR_PROVIDER,
            "llm": DEFAULT_LLM_PROVIDER,
            "embedding": DEFAULT_EMBEDDING_PROVIDER,
            "vector_index": DEFAULT_VECTOR_INDEX_PROVIDER
        }
    }

@app.get("/api/v1/providers/{provider_type}")
async def get_provider_details(provider_type: str):
    """Get details for a specific provider type"""
    providers = get_available_providers()
    
    if provider_type not in providers:
        raise HTTPException(status_code=404, detail=f"Provider type '{provider_type}' not found")
    
    provider_details = {
        "ocr": {
            "tesseract": {"description": "Open source OCR by Google", "config_schema": {"lang": "str", "psm": "int"}},
            "paddleocr": {"description": "PaddlePaddle OCR", "config_schema": {"lang": "str", "use_gpu": "bool"}},
            "easyocr": {"description": "Ready-to-use OCR", "config_schema": {"lang": "list", "gpu": "bool"}}
        },
        "llm": {
            "ollama": {"description": "Local LLM runner", "config_schema": {"model": "str", "base_url": "str"}},
            "openai": {"description": "OpenAI GPT models", "config_schema": {"api_key": "str", "model": "str"}},
            "gemini": {"description": "Google Gemini", "config_schema": {"api_key": "str", "model": "str"}},
            "anthropic": {"description": "Anthropic Claude", "config_schema": {"api_key": "str", "model": "str"}}
        },
        "embedding": {
            "sentence_transformers": {"description": "HuggingFace sentence transformers", "config_schema": {"model_name": "str", "device": "str"}},
            "openai": {"description": "OpenAI embeddings", "config_schema": {"api_key": "str", "model": "str"}},
            "cohere": {"description": "Cohere embeddings", "config_schema": {"api_key": "str", "model": "str"}},
            "huggingface": {"description": "HuggingFace inference API", "config_schema": {"api_token": "str", "model": "str"}}
        },
        "vector_index": {
            "turbovec": {"description": "In-memory vector index", "config_schema": {"dimension": "int", "metric": "str"}},
            "faiss": {"description": "Facebook AI Similarity Search", "config_schema": {"dimension": "int", "index_type": "str"}},
            "qdrant": {"description": "Qdrant vector database", "config_schema": {"url": "str", "collection": "str"}},
            "chroma": {"description": "Chroma vector database", "config_schema": {"path": "str", "collection": "str"}}
        }
    }
    
    return {
        "provider_type": provider_type,
        "providers": provider_details.get(provider_type, {})
    }

@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    background_tasks: BackgroundTasks = None
):
    """Upload a document for processing"""
    # Validate file extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Register document in database
        doc_id = db.insert_document(
            filename=file.filename,
            file_path=str(file_path),
            file_size=len(content),
            status="uploaded"
        )
        
        return DocumentUploadResponse(
            document_id=doc_id,
            filename=file.filename,
            status="uploaded",
            message="Document uploaded successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@app.post("/api/v1/pipeline/start")
async def start_pipeline(
    document_id: int = Query(..., description="Document ID to process"),
    config: PipelineConfig = None,
    enable_cache: bool = True,
    enable_checkpoint: bool = True
):
    """Start processing pipeline for a document with production features"""
    if config is None:
        config = PipelineConfig()
    
    # Get document from database
    doc = db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    
    # Initialize orchestrator with cache and checkpoint directories
    from ragstudio.core.config.settings import CACHE_DIR, CHECKPOINT_DIR
    
    orchestrator = PipelineOrchestrator(
        db=db,
        cache_dir=CACHE_DIR,
        checkpoint_dir=CHECKPOINT_DIR
    )
    
    # Start pipeline
    try:
        pipeline_id = await orchestrator.run(
            document_id=document_id,
            config=config.model_dump(),
            enable_cache=enable_cache,
            enable_checkpoint=enable_checkpoint
        )
        
        return {
            "pipeline_id": pipeline_id,
            "document_id": document_id,
            "status": "started",
            "message": "Pipeline started successfully",
            "features": {
                "cache_enabled": enable_cache,
                "checkpoint_enabled": enable_checkpoint
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")


@app.post("/api/v1/pipeline/pause/{pipeline_id}")
async def pause_pipeline(pipeline_id: str):
    """Pause a running pipeline"""
    from ragstudio.core.config.settings import CACHE_DIR, CHECKPOINT_DIR
    
    orchestrator = PipelineOrchestrator(
        db=db,
        cache_dir=CACHE_DIR,
        checkpoint_dir=CHECKPOINT_DIR
    )
    
    try:
        success = await orchestrator.pause(pipeline_id)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot pause pipeline - not in running state")
        
        return {
            "pipeline_id": pipeline_id,
            "status": "paused",
            "message": "Pipeline paused successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause pipeline: {str(e)}")


@app.post("/api/v1/pipeline/resume/{pipeline_id}")
async def resume_pipeline(pipeline_id: str):
    """Resume a failed or paused pipeline from last checkpoint"""
    from ragstudio.core.config.settings import CACHE_DIR, CHECKPOINT_DIR
    
    orchestrator = PipelineOrchestrator(
        db=db,
        cache_dir=CACHE_DIR,
        checkpoint_dir=CHECKPOINT_DIR
    )
    
    try:
        await orchestrator.resume(pipeline_id)
        return {
            "pipeline_id": pipeline_id,
            "status": "resumed",
            "message": "Pipeline resumed successfully from last checkpoint"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume pipeline: {str(e)}")


@app.post("/api/v1/pipeline/cancel/{pipeline_id}")
async def cancel_pipeline(pipeline_id: str):
    """Cancel a running pipeline"""
    from ragstudio.core.config.settings import CACHE_DIR, CHECKPOINT_DIR
    
    orchestrator = PipelineOrchestrator(
        db=db,
        cache_dir=CACHE_DIR,
        checkpoint_dir=CHECKPOINT_DIR
    )
    
    try:
        success = await orchestrator.cancel(pipeline_id)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot cancel pipeline")
        
        return {
            "pipeline_id": pipeline_id,
            "status": "cancelled",
            "message": "Pipeline cancelled successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel pipeline: {str(e)}")


@app.get("/api/v1/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get detailed job status with progress information"""
    from ragstudio.core.config.settings import CACHE_DIR, CHECKPOINT_DIR
    
    orchestrator = PipelineOrchestrator(
        db=db,
        cache_dir=CACHE_DIR,
        checkpoint_dir=CHECKPOINT_DIR
    )
    
    status = orchestrator.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "job_id": job_id,
        "status": status.get("status"),
        "progress": status.get("progress", 0),
        "current_stage": status.get("current_stage"),
        "completed_stages": status.get("completed_stages", []),
        "total_stages": status.get("total_stages", 0),
        "retry_count": status.get("retry_count", 0),
        "error_message": status.get("error_message"),
        "created_at": status.get("created_at"),
        "started_at": status.get("started_at"),
        "completed_at": status.get("completed_at")
    }


@app.post("/api/v1/jobs/{job_id}/cache/clear")
async def clear_job_cache(job_id: str):
    """Clear cache for a specific job"""
    from ragstudio.core.config.settings import CACHE_DIR, CHECKPOINT_DIR
    
    orchestrator = PipelineOrchestrator(
        db=db,
        cache_dir=CACHE_DIR,
        checkpoint_dir=CHECKPOINT_DIR
    )
    
    try:
        await orchestrator.clear_cache(job_id)
        return {
            "job_id": job_id,
            "message": "Cache cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.post("/api/v1/rag/search", response_model=SearchResponse)
async def search_documents(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, ge=1, le=50, description="Number of results to return"),
    document_id: Optional[int] = Query(None, description="Filter by document ID"),
    index_name: Optional[str] = Query(None, description="Specific vector index to search")
):
    """Search documents using RAG"""
    # Get embedding provider
    embedding_provider_name = DEFAULT_EMBEDDING_PROVIDER
    # In production, you'd load the actual provider based on settings
    
    # Get vector index provider
    vector_provider_name = DEFAULT_VECTOR_INDEX_PROVIDER
    
    try:
        # Perform search (simplified - in production this would use actual providers)
        results = db.search_chunks(
            query=query,
            top_k=top_k,
            document_id=document_id
        )
        
        formatted_results = [
            SearchResult(
                chunk_id=r["id"],
                document_id=r["document_id"],
                content=r["content"],
                score=r.get("score", 0.0),
                metadata=r.get("metadata", {})
            )
            for r in results
        ]
        
        return SearchResponse(
            query=query,
            results=formatted_results,
            total_results=len(formatted_results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/v1/documents")
async def list_documents(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List all documents"""
    documents = db.list_documents(limit=limit, offset=offset)
    
    if status:
        documents = [d for d in documents if d.get("status") == status]
    
    return {
        "documents": documents,
        "total": len(documents),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: int):
    """Get document details"""
    doc = db.get_document(document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    
    # Get chunks for this document
    chunks = db.get_chunks_for_document(document_id, limit=10)
    
    return {
        "document": doc,
        "chunks_count": len(chunks),
        "sample_chunks": chunks[:5]
    }

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: int):
    """Delete a document and its associated data"""
    try:
        db.delete_document(document_id)
        return {
            "message": f"Document {document_id} deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.get("/api/v1/vector-indexes")
async def list_vector_indexes():
    """List all vector indexes"""
    indexes = db.list_vector_indexes()
    return {
        "indexes": indexes,
        "total": len(indexes)
    }

@app.post("/api/v1/vector-indexes/create")
async def create_vector_index(
    name: str = Query(..., description="Index name"),
    provider: str = Query(DEFAULT_VECTOR_INDEX_PROVIDER, description="Vector index provider"),
    dimension: int = Query(384, ge=1, description="Vector dimension"),
    metric: str = Query("cosine", description="Distance metric")
):
    """Create a new vector index"""
    try:
        index_id = db.insert_vector_index(
            name=name,
            provider=provider,
            config={"dimension": dimension, "metric": metric}
        )
        
        return {
            "index_id": index_id,
            "name": name,
            "provider": provider,
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create index: {str(e)}")

# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
