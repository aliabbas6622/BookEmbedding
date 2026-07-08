# RAG Studio

A modular, resumable document ingestion and RAG (Retrieval-Augmented Generation) platform.

## Features

- **Modular Pipeline Architecture**: 6-stage pipeline (Upload → OCR → LLM Correction → Chunking → Embedding → Indexing)
- **Plugin-Based Providers**: Support for multiple OCR, LLM, Embedding, and Vector Index providers
- **Resumable Jobs**: Checkpointing and recovery for long-running pipelines
- **API Key Management**: Multiple keys with rotation, health checks, quotas, and retries
- **Structured Logging**: JSON logs with filtering and export capabilities
- **RAG Playground**: Interactive testing and benchmarking tools

## Project Structure

```
ragstudio/
├── api/                    # FastAPI REST API
│   ├── main.py            # Main API application
│   ├── rag_playground.py  # RAG playground endpoints
│   └── settings_routes.py # Settings management
├── core/                   # Core components
│   ├── config/            # Configuration settings
│   ├── database/          # SQLite database layer
│   ├── providers/         # Provider implementations
│   │   ├── ocr/          # OCR providers (Tesseract, etc.)
│   │   ├── llm/          # LLM providers (Ollama, OpenAI, etc.)
│   │   ├── embeddings/   # Embedding providers
│   │   └── vector_index/ # Vector index providers
│   ├── api_key_manager.py # API key management
│   └── logging_system.py  # Structured logging
├── pipeline/              # Pipeline stages
│   ├── base.py           # Base classes for stages
│   ├── orchestrator.py   # Pipeline orchestration
│   ├── upload_validation.py
│   ├── ocr_extraction.py
│   ├── llm_correction.py
│   ├── text_cleaning.py
│   ├── chunking.py
│   ├── embedding.py
│   └── vector_index.py
├── frontend/             # Frontend components (Next.js)
├── plugins/             # Plugin directory
├── cache/               # Cache directory
├── logs/                # Log files
├── indexes/             # Vector indexes
└── temp/                # Temporary files
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Starting the API Server

```bash
cd ragstudio
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Using the Pipeline

```python
from ragstudio import Database, PipelineOrchestrator
from ragstudio.pipeline import (
    UploadValidationStage,
    OCRExtractionStage,
    LLMCorrectionStage,
    TextCleaningStage,
    ChunkingStage,
    EmbeddingStage,
    VectorIndexStage
)

# Initialize database
db = Database()

# Create orchestrator
orchestrator = PipelineOrchestrator(db=db)

# Register stages
orchestrator.register_stage(UploadValidationStage())
orchestrator.register_stage(OCRExtractionStage({"provider": "tesseract"}))
orchestrator.register_stage(LLMCorrectionStage({"provider": "ollama", "enabled": True}))
orchestrator.register_stage(TextCleaningStage())
orchestrator.register_stage(ChunkingStage({"chunk_size": 512, "chunk_overlap": 50}))
orchestrator.register_stage(EmbeddingStage({"provider": "sentence_transformers"}))
orchestrator.register_stage(VectorIndexStage({"provider": "turbovec"}))

# Run pipeline
pipeline_id = await orchestrator.run(document_id=1)
```

## API Endpoints

- `POST /api/v1/documents/upload` - Upload a document
- `POST /api/v1/pipeline/start` - Start processing pipeline
- `GET /api/v1/pipeline/status/{pipeline_id}` - Get pipeline status
- `POST /api/v1/pipeline/resume/{pipeline_id}` - Resume failed pipeline
- `POST /api/v1/rag/search` - Search documents
- `POST /api/v1/rag/chat` - Chat with documents
- `GET /api/v1/rag/models` - List available models
- `GET /api/v1/providers` - List available providers

## Provider Support

### OCR Providers
- Tesseract (built-in)
- PaddleOCR (coming soon)
- EasyOCR (coming soon)

### LLM Providers
- Ollama (local)
- OpenAI
- Google Gemini
- Anthropic Claude

### Embedding Providers
- Sentence Transformers (local)
- OpenAI
- Cohere
- HuggingFace

### Vector Index Providers
- TurboVec (in-memory)
- FAISS
- Qdrant
- Chroma

## Configuration

Edit `core/config/settings.py` to customize:

- Database path
- Upload directory
- Default providers
- Chunk size and overlap
- API host and port

## License

MIT License
