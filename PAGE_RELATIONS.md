# RAG Studio - Page Relations & Function Mapping

## Overview
This document maps all pages, their routes, API endpoints, and function relationships in the RAG Studio application.

---

## 1. Dashboard (`/`)

**Page Type:** `DASHBOARD`  
**Icon:** 📊  
**Access:** Authenticated users

### Route Configuration
- **Path:** `/`
- **Navigation:** `navigation_manager.navigate("/")`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/documents` | GET | Fetch document list for stats |
| `/api/pipeline/sessions` | GET | Get active pipeline sessions |
| `/api/vector-indexes` | GET | Retrieve vector index statistics |
| `/api/system/status` | GET | System health check |

### Functions Called
```python
# Frontend
- loadDashboardStats()
- fetchRecentDocuments()
- getPipelineStatus()
- renderCharts()

# Backend
- db.get_documents_count()
- db.get_chunks_count()
- pipeline_orchestrator.get_active_sessions()
- vector_index.get_index_stats()
```

### Navigation Links
- → Upload: `/upload`
- → Documents: `/documents`
- → Pipeline: `/pipeline`
- → Settings: `/settings`

---

## 2. Upload Documents (`/upload`)

**Page Type:** `UPLOAD`  
**Icon:** 📤  
**Access:** Authenticated users

### Route Configuration
- **Path:** `/upload`
- **Query Params:** `auto_start` (bool)
- **Navigation:** `navigation_manager.navigate("/upload", query_params={"auto_start": true})`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/documents/upload` | POST | Upload PDF file |
| `/api/documents/{id}/validate` | GET | Validate uploaded document |
| `/api/pipeline/start` | POST | Start processing pipeline |

### Functions Called
```python
# Frontend
- handleFileUpload(file)
- validateDocument(document_id)
- startPipeline(document_id, config)
- showUploadProgress()

# Backend
- upload_stage.execute()
- validation_stage.execute()
- pipeline_orchestrator.start_session()
```

### Navigation Links
- ← Dashboard: `/`
- → Pipeline Monitor: `/pipeline/monitor?session_id={session_id}`
- → Documents: `/documents`

---

## 3. Pipeline Management (`/pipeline`)

**Page Type:** `PIPELINE`  
**Icon:** ⚙️  
**Access:** Authenticated users

### Route Configuration
- **Path:** `/pipeline`
- **Query Params:** `document_id`, `session_id`
- **Navigation:** `navigation_manager.navigate("/pipeline", query_params={"document_id": "123"})`

### Child Routes
- `/pipeline/monitor` - Real-time monitoring

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/pipeline/sessions` | GET | List all pipeline sessions |
| `/api/pipeline/session/{id}` | GET | Get session details |
| `/api/pipeline/start` | POST | Start new pipeline |
| `/api/pipeline/{id}/pause` | POST | Pause pipeline |
| `/api/pipeline/{id}/resume` | POST | Resume paused pipeline |
| `/api/pipeline/{id}/cancel` | POST | Cancel pipeline |

### Functions Called
```python
# Frontend
- listPipelineSessions()
- createPipeline(config)
- controlPipeline(action, session_id)
- renderPipelineGraph()

# Backend
- pipeline_orchestrator.create_session()
- pipeline_orchestrator.pause_session()
- pipeline_orchestrator.resume_session()
- db.update_pipeline_status()
```

### Navigation Links
- ← Dashboard: `/`
- → Monitor: `/pipeline/monitor?session_id={id}`
- → Documents: `/documents`

---

## 4. Pipeline Monitoring (`/pipeline/monitor`)

**Page Type:** `MONITORING`  
**Icon:** 📈  
**Access:** Authenticated users, requires active pipeline

### Route Configuration
- **Path:** `/pipeline/monitor`
- **Parent:** `/pipeline`
- **Query Params:** `session_id` (required)
- **Navigation:** `navigation_manager.navigate("/pipeline/monitor", query_params={"session_id": "abc"})`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/pipeline/session/{id}` | GET | Get session status |
| `/api/pipeline/session/{id}/logs` | GET | Stream pipeline logs |
| `/api/pipeline/session/{id}/metrics` | GET | Get performance metrics |
| `/api/pipeline/{id}/pause` | POST | Pause execution |
| `/api/pipeline/{id}/resume` | POST | Resume execution |

### Functions Called
```python
# Frontend
- streamPipelineLogs(session_id)
- updateProgressBars()
- renderStageStatus()
- pollMetrics(interval=5000)

# Backend
- pipeline_orchestrator.get_session_status()
- pipeline_orchestrator.get_stage_progress()
- db.get_pipeline_logs()
```

### Navigation Links
- ← Pipeline: `/pipeline`
- → Documents: `/documents/{document_id}` (on completion)

---

## 5. Documents Library (`/documents`)

**Page Type:** `DOCUMENTS`  
**Icon:** 📚  
**Access:** Authenticated users

### Route Configuration
- **Path:** `/documents`
- **Navigation:** `navigation_manager.navigate("/documents")`

### Child Routes
- `/documents/{document_id}` - Document details
- `/documents/{document_id}/chunks` - Text chunks
- `/documents/{document_id}/embeddings` - Embeddings

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/documents` | GET | List all documents |
| `/api/documents/{id}` | GET | Get document metadata |
| `/api/documents/{id}` | DELETE | Delete document |
| `/api/documents/{id}/chunks` | GET | Get document chunks |

### Functions Called
```python
# Frontend
- fetchDocumentsList(filters)
- deleteDocument(document_id)
- searchDocuments(query)
- paginateDocuments(page, limit)

# Backend
- db.get_all_documents()
- db.get_document_by_id()
- db.delete_document()
- db.get_chunks_by_document()
```

### Navigation Links
- ← Dashboard: `/`
- → Document Details: `/documents/{id}`
- → Upload: `/upload`

---

## 6. Document Details (`/documents/{document_id}`)

**Page Type:** `DOCUMENTS`  
**Icon:** 📄  
**Access:** Authenticated users, requires document

### Route Configuration
- **Path:** `/documents/{document_id}`
- **Parent:** `/documents`
- **Query Params:** `view_mode` (detail|preview)
- **Navigation:** `navigation_manager.navigate("/documents/{id}", params={"document_id": "123"})`

### Child Routes
- `/documents/{document_id}/chunks`
- `/documents/{document_id}/embeddings`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/documents/{id}` | GET | Get full document info |
| `/api/documents/{id}/chunks` | GET | Get chunk summary |
| `/api/documents/{id}/embeddings/stats` | GET | Get embedding statistics |
| `/api/vector-indexes/search` | POST | Search within document |

### Functions Called
```python
# Frontend
- loadDocumentDetails(id)
- renderMetadata()
- previewPDF()
- navigateToChunks(id)

# Backend
- db.get_document_by_id()
- db.get_chunks_count_by_document()
- db.get_embedding_stats()
```

### Navigation Links
- ← Documents: `/documents`
- → Chunks: `/documents/{id}/chunks`
- → Embeddings: `/documents/{id}/embeddings`
- → RAG Playground: `/rag-playground?document_id={id}`

---

## 7. Document Chunks (`/documents/{document_id}/chunks`)

**Page Type:** `CHUNKS`  
**Icon:** 🔪  
**Access:** Authenticated users, requires document

### Route Configuration
- **Path:** `/documents/{document_id}/chunks`
- **Parent:** `/documents/{document_id}`
- **Query Params:** `page`, `limit`, `search`
- **Navigation:** `navigation_manager.navigate("/documents/{id}/chunks", params={"document_id": "123"}, query_params={"page": 1})`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/documents/{id}/chunks` | GET | List chunks with pagination |
| `/api/chunks/{id}` | GET | Get single chunk details |
| `/api/chunks/{id}/embedding` | GET | Get chunk embedding vector |

### Functions Called
```python
# Frontend
- fetchChunks(document_id, page, limit)
- searchChunks(query)
- viewChunkEmbedding(chunk_id)
- exportChunks(format)

# Backend
- db.get_chunks_by_document()
- db.get_chunk_by_id()
- db.get_embedding_vector()
```

### Navigation Links
- ← Document Details: `/documents/{id}`
- → Embeddings: `/documents/{id}/embeddings`

---

## 8. Embeddings View (`/documents/{document_id}/embeddings`)

**Page Type:** `EMBEDDINGS`  
**Icon:** 🔢  
**Access:** Authenticated users, requires document

### Route Configuration
- **Path:** `/documents/{document_id}/embeddings`
- **Parent:** `/documents/{document_id}`
- **Query Params:** `embedding_provider`, `dimensionality`
- **Navigation:** `navigation_manager.navigate("/documents/{id}/embeddings", params={"document_id": "123"})`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/documents/{id}/embeddings` | GET | Get embedding data |
| `/api/embeddings/compute` | POST | Recompute embeddings |
| `/api/embeddings/visualize` | POST | Generate 2D/3D visualization |

### Functions Called
```python
# Frontend
- loadEmbeddings(document_id)
- visualizeEmbeddings(dimensions)
- compareProviders()
- downloadEmbeddings()

# Backend
- db.get_embeddings_by_document()
- embedding_provider.compute_batch()
- dimensionality_reduction.pca()
```

### Navigation Links
- ← Document Details: `/documents/{id}`
- → Chunks: `/documents/{id}/chunks`
- → Vector Index: `/vector-index`

---

## 9. Vector Index (`/vector-index`)

**Page Type:** `VECTOR_INDEX`  
**Icon:** 🗂️  
**Access:** Authenticated users

### Route Configuration
- **Path:** `/vector-index`
- **Navigation:** `navigation_manager.navigate("/vector-index")`

### Child Routes
- `/vector-index/{index_id}` - Index details

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/vector-indexes` | GET | List all indexes |
| `/api/vector-indexes` | POST | Create new index |
| `/api/vector-indexes/{id}` | GET | Get index details |
| `/api/vector-indexes/{id}` | DELETE | Delete index |
| `/api/vector-indexes/search` | POST | Semantic search |

### Functions Called
```python
# Frontend
- listVectorIndexes()
- createIndex(config)
- deleteIndex(index_id)
- performSearch(query, filters)

# Backend
- vector_index_provider.list_indexes()
- vector_index_provider.create_index()
- vector_index_provider.search()
- db.get_index_metadata()
```

### Navigation Links
- ← Dashboard: `/`
- → Index Details: `/vector-index/{id}`
- → RAG Playground: `/rag-playground`

---

## 10. Index Details (`/vector-index/{index_id}`)

**Page Type:** `VECTOR_INDEX`  
**Icon:** 📋  
**Access:** Authenticated users

### Route Configuration
- **Path:** `/vector-index/{index_id}`
- **Parent:** `/vector-index`
- **Query Params:** `view_metrics`
- **Navigation:** `navigation_manager.navigate("/vector-index/{id}", params={"index_id": "xyz"})`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/vector-indexes/{id}` | GET | Get detailed index info |
| `/api/vector-indexes/{id}/stats` | GET | Get index statistics |
| `/api/vector-indexes/{id}/rebuild` | POST | Rebuild index |

### Functions Called
```python
# Frontend
- loadIndexDetails(id)
- renderMetrics()
- rebuildIndex()
- exportIndexConfig()

# Backend
- vector_index_provider.get_index_info()
- vector_index_provider.get_stats()
- vector_index_provider.rebuild()
```

### Navigation Links
- ← Vector Index: `/vector-index`
- → RAG Playground: `/rag-playground?index_id={id}`

---

## 11. General Settings (`/settings`)

**Page Type:** `SETTINGS`  
**Icon:** 🔧  
**Access:** Admin only

### Route Configuration
- **Path:** `/settings`
- **Navigation:** `navigation_manager.navigate("/settings")`

### Child Routes
- `/settings/api` - API & Provider settings

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/settings` | GET | Get all settings |
| `/api/settings` | PUT | Update settings |
| `/api/settings/export` | GET | Export settings JSON |
| `/api/settings/import` | POST | Import settings |
| `/api/settings/reset` | POST | Reset to defaults |

### Functions Called
```python
# Frontend
- loadSettings()
- saveSettings(config)
- exportSettings()
- importSettings(file)
- resetToDefaults()

# Backend
- config_manager.get_all()
- config_manager.update()
- config_manager.export_json()
- config_manager.import_json()
```

### Navigation Links
- ← Dashboard: `/`
- → API Settings: `/settings/api`
- → Providers: `/providers`

---

## 12. API & Provider Settings (`/settings/api`)

**Page Type:** `API_SETTINGS`  
**Icon:** 🔌  
**Access:** Admin only

### Route Configuration
- **Path:** `/settings/api`
- **Parent:** `/settings`
- **Navigation:** `navigation_manager.navigate("/settings/api")`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/settings/providers` | GET | Get provider configurations |
| `/api/settings/providers/{type}` | PUT | Update provider config |
| `/api/settings/chunking` | GET/PUT | Chunking settings |
| `/api/settings/cleaning` | GET/PUT | Text cleaning settings |
| `/api/settings/pipeline` | GET/PUT | Pipeline defaults |
| `/api/settings/paths` | GET/PUT | Path configurations |
| `/api/providers/test` | POST | Test provider connection |

### Functions Called
```python
# Frontend
- loadProviderConfigs()
- updateProviderConfig(type, config)
- testProviderConnection(provider)
- configureChunking(strategy, size, overlap)
- configureCleaning(patterns)

# Backend
- ocr_provider.initialize()
- llm_provider.test_connection()
- embedding_provider.validate_config()
- vector_index_provider.check_availability()
```

### Navigation Links
- ← Settings: `/settings`
- → Providers: `/providers`

---

## 13. RAG Playground (`/rag-playground`)

**Page Type:** `RAG_PLAYGROUND`  
**Icon:** 🎮  
**Access:** Authenticated users

### Route Configuration
- **Path:** `/rag-playground`
- **Navigation:** `navigation_manager.navigate("/rag-playground")`

### Child Routes
- `/rag-playground/chat/{conversation_id}`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/rag/query` | POST | Semantic search query |
| `/api/rag/chat` | POST | Chat with context |
| `/api/rag/conversations` | GET | List conversations |
| `/api/rag/conversations/{id}` | GET | Get conversation |
| `/api/rag/conversations` | DELETE | Delete conversation |
| `/api/rag/compare` | POST | Compare models |
| `/api/rag/evaluate` | POST | Evaluate retrieval quality |
| `/api/rag/benchmark` | POST | Performance benchmark |

### Functions Called
```python
# Frontend
- sendQuery(query, filters)
- startChat(message, system_prompt)
- loadConversation(id)
- compareModels(queries, models)
- evaluateRetrieval(ground_truth)
- runBenchmark(iterations)

# Backend
- rag_engine.semantic_search()
- rag_engine.generate_response()
- rag_engine.build_context()
- evaluation_metrics.calculate_precision_recall()
- benchmark.measure_latency()
```

### Navigation Links
- ← Dashboard: `/`
- → Chat Session: `/rag-playground/chat/{id}`
- → Documents: `/documents`
- → Vector Index: `/vector-index`

---

## 14. Chat Session (`/rag-playground/chat/{conversation_id}`)

**Page Type:** `RAG_PLAYGROUND`  
**Icon:** 💬  
**Access:** Authenticated users

### Route Configuration
- **Path:** `/rag-playground/chat/{conversation_id}`
- **Parent:** `/rag-playground`
- **Navigation:** `navigation_manager.navigate("/rag-playground/chat/{id}", params={"conversation_id": "conv123"})`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/rag/chat` | POST | Continue conversation |
| `/api/rag/conversations/{id}` | GET | Load conversation history |
| `/api/rag/conversations/{id}` | DELETE | Delete conversation |

### Functions Called
```python
# Frontend
- loadChatHistory(conversation_id)
- sendMessage(message)
- streamResponse()
- exportConversation(format)

# Backend
- rag_engine.chat_with_memory()
- db.get_conversation_messages()
- llm_provider.stream_completion()
```

### Navigation Links
- ← RAG Playground: `/rag-playground`

---

## 15. Provider Management (`/providers`)

**Page Type:** `PROVIDERS`  
**Icon:** 🔗  
**Access:** Admin only

### Route Configuration
- **Path:** `/providers`
- **Query Params:** `provider_type`, `test_connection`
- **Navigation:** `navigation_manager.navigate("/providers", query_params={"provider_type": "llm"})`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/providers` | GET | List all providers |
| `/api/providers/{type}` | GET | Get providers by type |
| `/api/providers/{type}/{name}/test` | POST | Test specific provider |
| `/api/providers/{type}/{name}/configure` | PUT | Configure provider |

### Functions Called
```python
# Frontend
- listProviders(type)
- testProvider(type, name, config)
- configureProvider(type, name, settings)
- setDefaultProvider(type, name)

# Backend
- provider_registry.get_providers()
- ocr_provider.test_connection()
- llm_provider.validate_api_key()
- embedding_provider.check_model_availability()
- vector_index_provider.verify_installation()
```

### Navigation Links
- ← Settings: `/settings`
- → API Settings: `/settings/api`

---

## 16. Help & Documentation (`/help`)

**Page Type:** `HELP`  
**Icon:** ❓  
**Access:** Public (no auth required)

### Route Configuration
- **Path:** `/help`
- **Navigation:** `navigation_manager.navigate("/help")`

### Connected API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/docs` | GET | OpenAPI documentation |
| `/api/help/guides` | GET | User guides |
| `/api/help/faq` | GET | Frequently asked questions |

### Functions Called
```python
# Frontend
- loadDocumentation()
- searchHelp(query)
- openApiDocs()
- reportIssue()

# Backend
- docs_generator.generate_openapi()
- knowledge_base.search_articles()
```

### Navigation Links
- ← Any page (accessible globally)
- → API Docs: `/docs` (Swagger UI)

---

## Cross-Page Function Dependencies

### Database Layer Usage
All pages interact with the database through these common functions:
```python
db.get_document_by_id()          # Used by: Documents, Chunks, Embeddings, Pipeline
db.get_chunks_by_document()      # Used by: Chunks, Embeddings, RAG Playground
db.get_embedding_vector()        # Used by: Embeddings, RAG Playground
db.update_pipeline_status()      # Used by: Pipeline, Monitoring
db.get_all_documents()           # Used by: Dashboard, Documents
```

### Pipeline Orchestrator Usage
```python
orchestrator.create_session()    # Used by: Upload, Pipeline
orchestrator.start_session()     # Used by: Upload, Pipeline
orchestrator.pause_session()     # Used by: Pipeline, Monitoring
orchestrator.resume_session()    # Used by: Pipeline, Monitoring
orchestrator.get_session_status() # Used by: Monitoring, Dashboard
```

### Provider Interface Usage
```python
ocr_provider.extract_text()      # Used by: Pipeline (OCR Stage)
llm_provider.generate()          # Used by: RAG Playground, Pipeline (Enrichment)
embedding_provider.embed()       # Used by: Pipeline (Embedding Stage), RAG Playground
vector_index_provider.index()    # Used by: Pipeline (Vector Index Stage)
vector_index_provider.search()   # Used by: RAG Playground, Documents
```

### Navigation Manager Usage
All pages use the navigation manager for routing:
```python
navigation_manager.navigate()    # All pages
navigation_manager.go_back()     # All pages
navigation_manager.build_url()   # Dynamic link generation
navigation_manager.get_current_state()  # State management
```

---

## Event Flow Diagrams

### Document Upload Flow
```
Upload Page → API: /documents/upload 
           → Validation Stage 
           → Pipeline Start 
           → Monitoring Page 
           → Documents List
```

### RAG Query Flow
```
RAG Playground → API: /rag/query 
              → Embedding Provider 
              → Vector Index Search 
              → Context Building 
              → LLM Generation 
              → Response Display
```

### Pipeline Execution Flow
```
Pipeline Page → Create Session 
             → Configure Stages 
             → Start Execution 
             → Monitoring (Real-time) 
             → Completion 
             → Results Available
```

---

## Summary Statistics

- **Total Pages:** 16
- **Total Routes:** 24 (including dynamic routes)
- **API Endpoints:** 47+
- **Page Types:** 12 unique types
- **Navigation Guards:** Authentication, document requirements, pipeline status
- **Cross-page Dependencies:** Database (8 functions), Pipeline (5 functions), Providers (4 interfaces)
