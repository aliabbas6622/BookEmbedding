# RAG Studio – Product Requirements Document (PRD)

## Vision
Build a modular, resumable, provider-agnostic document ingestion and RAG platform. PDFs are one input type; the architecture must support future sources.

## Core Workflow
1. Upload PDF(s) and chapter JSON.
2. Validate JSON.
3. Create project folder.
4. Split PDF into chapter PDFs.
5. OCR each chapter.
6. Optional LLM OCR correction.
7. Chunk text.
8. Generate embeddings.
9. Cache embeddings.
10. Build one or more vector indexes.
11. Test in integrated RAG playground.

Every stage must checkpoint progress and resume after interruption.

## Folder Structure
```text
Projects/
  Book/
    original.pdf
    metadata.json
    chapters/
      Chapter 01/
        chapter.pdf
        extracted.txt
        corrected.txt
        chunks.json
        embeddings.bin
        metadata.json
        status.json
    indexes/
      turbovec/
      qdrant/
      faiss/
    cache/
    logs/
```

## Resume System
Each chapter has status.json:
- split
- ocr
- corrected
- chunked
- embedded
- indexed

Resume starts from first incomplete stage.

## Providers

### OCR
- Tesseract.js
- PaddleOCR (future)
- EasyOCR (future)

### LLM
- Ollama
- Gemini
- OpenRouter
- OpenAI-compatible endpoints
- Anthropic
- Groq

### Embeddings
- Ollama
- Gemini
- OpenAI
- OpenRouter
- Jina
- VoyageAI
- Nomic
- SentenceTransformers
- FastEmbed

### Vector Index
- TurboVec
- FAISS
- Qdrant
- Chroma
- Milvus
- Pinecone
- Weaviate
- LanceDB
- SQLiteVec
- pgvector
- Redis

## Architecture
Each provider implements a common interface.

- OCRProvider
- LLMProvider
- EmbeddingProvider
- VectorIndex
- Chunker

New providers should require minimal code.

## API Store
Multiple keys per provider.
Features:
- Round robin
- Weighted routing
- Least-used routing
- Failover
- Automatic retries
- Health checks
- Cooldown after failures
- Usage metrics
- RPM/TPM limits

## UI Pages
- Dashboard
- Books
- Upload
- Pipeline Viewer
- Chapter Viewer
- OCR Settings
- LLM Settings
- Embedding Settings
- Vector Store Manager
- API Store
- Logs
- Benchmark
- RAG Playground
- Settings

## Dashboard
Display:
- CPU
- RAM
- GPU
- Queue
- Progress
- API usage
- Cost
- Active jobs

## Upload
Support:
- Single upload
- Batch upload
- Drag & drop
- JSON validation
- Chapter preview

## Pipeline Viewer
Visual pipeline with stage colors:
- Pending
- Running
- Success
- Failed

## OCR
Configurable:
- Workers
- Threads
- Languages
- Confidence threshold
- Engine

## OCR Correction
Optional.
Editable prompts.
Retries.
Timeouts.

## Chunking
Strategies:
- Fixed
- Recursive
- Semantic
- Sentence
- Heading-aware

Configurable overlap and size.

## Embedding Cache
Hash text.
Reuse identical embeddings.
Avoid repeated API calls.

## Vector Index Manager
Allow multiple indexes per dataset simultaneously.

## TurboVec
TurboVec is a vector index backend, not an embedding model.
Pipeline:
Text -> Embedding -> Embedding Cache -> TurboVec

## Benchmarking
Compare providers by:
- Recall@K
- MRR
- Latency
- Build time
- Memory
- Disk
- Cost

## RAG Playground
Select:
- Book
- Index
- Embedding model
- LLM

Show:
- Retrieved chunks
- Similarity
- Sources
- Latency
- Final answer

## Logging
Detailed logs per stage.
Search.
Download.
Filter.

## Downloads
Export:
- OCR
- Corrected text
- Chunks
- Embeddings
- Metadata
- Logs
- ZIP

## Database
SQLite for metadata:
- Books
- Jobs
- Providers
- API Keys
- Logs
- Settings

Vectors remain in chosen vector backend.

## Performance Controls
User configurable:
- CPU cores
- Thread count
- Parallel OCR
- Parallel embeddings
- Concurrent LLM requests
- Upload concurrency
- Memory limits
- Disk cache

## Design
Minimal UI:
- White
- Soft accent color
- Clean typography
- Responsive
- Dark mode optional

## Future
- DOCX
- Markdown
- Websites
- YouTube transcripts
- Images
- EPUB
- REST API
- Webhooks
- Notifications
