# RAG Studio API Documentation

## Overview

RAG Studio is a modular, resumable, provider-agnostic document ingestion and RAG (Retrieval-Augmented Generation) platform. This API provides complete control over the document processing pipeline and RAG experimentation.

**Base URL**: `http://localhost:8000`  
**API Docs**: `http://localhost:8000/docs`  
**ReDoc**: `http://localhost:8000/redoc`

---

## Table of Contents

1. [Settings & Configuration](#settings--configuration)
2. [Document Management](#document-management)
3. [Pipeline Control](#pipeline-control)
4. [RAG Playground](#rag-playground)
5. [Vector Indexes](#vector-indexes)

---

## Settings & Configuration

Full customization for all providers and pipeline settings.

### Get All Settings
```bash
GET /api/v1/settings
```

Returns complete configuration including OCR, LLM, embedding, vector index providers, chunking, text cleaning, pipeline defaults, and paths.

### Get Available Providers
```bash
GET /api/v1/settings/providers
```

Returns all available providers with their current configurations.

### Get Provider Type Configuration
```bash
GET /api/v1/settings/providers/{provider_type}
```
**Parameters:**
- `provider_type`: `ocr`, `llm`, `embedding`, or `vector_index`

Returns configuration and schemas for all providers of that type.

### Get Specific Provider Config
```bash
GET /api/v1/settings/providers/{provider_type}/{provider_name}
```

Returns detailed configuration and schema for a specific provider.

### Set Default Provider
```bash
POST /api/v1/settings/providers/{provider_type}/default?provider_name={name}
```

Sets the default provider for a provider type.

### Update Provider Configuration
```bash
PUT /api/v1/settings/providers/{provider_type}/{provider_name}/config
Content-Type: application/json

{
  "model": "gpt-4o",
  "temperature": 0.7,
  "api_key": "your-api-key"
}
```

Updates configuration for a specific provider.

### Chunking Configuration
```bash
GET /api/v1/settings/chunking
PUT /api/v1/settings/chunking
```

Get or update chunking settings:
```json
{
  "strategy": "recursive",
  "chunk_size": 512,
  "chunk_overlap": 50,
  "separators": ["\n\n", "\n", ". ", " "],
  "min_chunk_size": 50,
  "keep_separator": false,
  "strip_whitespace": true
}
```

### Text Cleaning Configuration
```bash
GET /api/v1/settings/text-cleaning
PUT /api/v1/settings/text-cleaning
```

Configure text preprocessing options.

### Pipeline Defaults
```bash
GET /api/v1/settings/pipeline
PUT /api/v1/settings/pipeline
```

Set pipeline-wide defaults like auto-start, parallel processing, retries.

### Path Configuration
```bash
GET /api/v1/settings/paths
PUT /api/v1/settings/paths
```

Configure upload, output, database, cache, and log directories.

### Export/Import Settings
```bash
GET /api/v1/settings/export
POST /api/v1/settings/import
```

Export current settings as JSON or import from JSON.

### Reset to Defaults
```bash
POST /api/v1/settings/reset
```

Reset all settings to factory defaults.

---

## Document Management

### Upload Document
```bash
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: <PDF file>
```

**Response:**
```json
{
  "document_id": 1,
  "filename": "document.pdf",
  "status": "uploaded",
  "message": "Document uploaded successfully"
}
```

### List Documents
```bash
GET /api/v1/documents?status={status}&limit=20&offset=0
```

**Query Parameters:**
- `status`: Filter by status (uploaded, processing, completed, failed)
- `limit`: Number of results (1-100)
- `offset`: Pagination offset

### Get Document Details
```bash
GET /api/v1/documents/{document_id}
```

Returns document metadata and sample chunks.

### Delete Document
```bash
DELETE /api/v1/documents/{document_id}
```

Deletes document and all associated data.

---

## Pipeline Control

### Start Pipeline
```bash
POST /api/v1/pipeline/start?document_id=1
Content-Type: application/json

{
  "ocr_provider": "tesseract",
  "llm_provider": "ollama",
  "embedding_provider": "sentence_transformers",
  "vector_index_provider": "turbovec",
  "chunk_size": 512,
  "chunk_overlap": 50,
  "custom_stages": []
}
```

Starts processing pipeline for a document.

### Get Pipeline Status
```bash
GET /api/v1/pipeline/status/{pipeline_id}
```

**Response:**
```json
{
  "pipeline_id": "pipe_123",
  "document_id": 1,
  "status": "running",
  "current_stage": "embedding",
  "completed_stages": ["upload", "ocr", "cleaning", "chunking"],
  "failed_stage": null,
  "error_message": null,
  "progress_percentage": 72.5
}
```

### Resume Pipeline
```bash
POST /api/v1/pipeline/resume/{pipeline_id}
```

Resumes a failed or paused pipeline from the last successful stage.

---

## RAG Playground

Interactive testing and experimentation with your processed documents.

### List Available Models
```bash
GET /api/v1/rag/models
```

Returns available embedding and LLM models.

### Semantic Search Query
```bash
POST /api/v1/rag/query
Content-Type: application/json

{
  "query": "What is machine learning?",
  "top_k": 5,
  "document_id": 1,
  "index_name": "default",
  "embedding_provider": "sentence_transformers",
  "rerank": false
}
```

**Response:**
```json
{
  "query": "What is machine learning?",
  "results": [
    {
      "chunk_id": 12,
      "document_id": 1,
      "content": "Machine learning is a subset of AI...",
      "score": 0.95,
      "metadata": {"source": "doc.pdf", "page": 3},
      "page_number": 3
    }
  ],
  "total_results": 5,
  "query_time_ms": 45.2,
  "embedding_model": "all-MiniLM-L6-v2",
  "index_name": "default"
}
```

### Chat with Documents
```bash
POST /api/v1/rag/chat
Content-Type: application/json

{
  "message": "Explain the main concepts",
  "conversation_id": "conv_123",
  "top_k": 5,
  "system_prompt": "You are a helpful assistant.",
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false,
  "include_sources": true
}
```

**Response:**
```json
{
  "conversation_id": "conv_123",
  "message": "Based on the documents...",
  "sources": [...],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 300,
    "total_tokens": 450
  },
  "model": "llama3.2",
  "query_time_ms": 45.2,
  "total_time_ms": 1250.5
}
```

### Conversation Management

#### List Conversations
```bash
GET /api/v1/rag/conversations?limit=20
```

#### Get Conversation
```bash
GET /api/v1/rag/conversations/{conversation_id}
```

#### Delete Conversation
```bash
DELETE /api/v1/rag/conversations/{conversation_id}
```

#### Clear All Conversations
```bash
POST /api/v1/rag/conversations/clear
```

### Compare Embedding Models
```bash
GET /api/v1/rag/compare?query=machine+learning&models=all-MiniLM-L6-v2&models=all-mpnet-base-v2
```

Compares search results across different embedding models.

### Evaluate Retrieval Quality
```bash
POST /api/v1/rag/evaluate?query=test&expected_chunks=1&expected_chunks=2&expected_chunks=3
```

Calculates precision, recall, and F1 score for retrieval.

### Benchmark Performance
```bash
GET /api/v1/rag/benchmark?iterations=50
```

Runs performance benchmarks and returns latency statistics.

---

## Vector Indexes

### List Indexes
```bash
GET /api/v1/vector-indexes
```

### Create Index
```bash
POST /api/v1/vector-indexes/create?name=my_index&provider=turbovec&dimension=384&metric=cosine
```

---

## Provider Configuration Examples

### Configure OpenAI
```bash
PUT /api/v1/settings/providers/llm/openai/config
Content-Type: application/json

{
  "api_key": "sk-...",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

### Configure Ollama
```bash
PUT /api/v1/settings/providers/llm/ollama/config
Content-Type: application/json

{
  "base_url": "http://localhost:11434",
  "model": "llama3.2",
  "timeout": 120
}
```

### Configure Qdrant
```bash
PUT /api/v1/settings/providers/vector_index/qdrant/config
Content-Type: application/json

{
  "url": "http://localhost:6333",
  "api_key": "",
  "collection": "rag_collection",
  "vector_size": 384,
  "distance": "Cosine"
}
```

### Set Default Embedding Provider
```bash
POST /api/v1/settings/providers/embedding/default?provider_name=openai
```

---

## Error Responses

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Error message description"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. In production, consider adding rate limits based on your use case.

---

## Authentication

This API currently does not include authentication. For production use, implement appropriate authentication mechanisms (API keys, JWT, OAuth2, etc.).

---

## Support

For issues and feature requests, please refer to the project documentation.
