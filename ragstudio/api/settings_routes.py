"""
RAG Studio Settings API - Full customization for all providers
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
import json

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])

# ============================================
# Pydantic Models for Provider Configurations
# ============================================

class OCRProviderConfig(BaseModel):
    """OCR provider configuration"""
    enabled: bool = True
    default_provider: str = "tesseract"
    providers: Dict[str, Dict[str, Any]] = {
        "tesseract": {
            "lang": "eng",
            "psm": 6,
            "oem": 3,
            "timeout": 30
        },
        "paddleocr": {
            "lang": "en",
            "use_gpu": False,
            "show_log": False,
            "det_model_dir": None,
            "rec_model_dir": None
        },
        "easyocr": {
            "lang": ["en"],
            "gpu": False,
            "model_storage_directory": None,
            "download_enabled": True
        }
    }

class LLMProviderConfig(BaseModel):
    """LLM provider configuration"""
    enabled: bool = True
    default_provider: str = "ollama"
    providers: Dict[str, Dict[str, Any]] = {
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "llama3.2",
            "timeout": 120,
            "num_ctx": 4096
        },
        "openai": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2048,
            "timeout": 60
        },
        "gemini": {
            "api_key": "",
            "model": "gemini-1.5-flash",
            "temperature": 0.7,
            "max_output_tokens": 2048,
            "timeout": 60
        },
        "anthropic": {
            "api_key": "",
            "base_url": "https://api.anthropic.com",
            "model": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2048,
            "timeout": 60
        }
    }

class EmbeddingProviderConfig(BaseModel):
    """Embedding provider configuration"""
    enabled: bool = True
    default_provider: str = "sentence_transformers"
    providers: Dict[str, Dict[str, Any]] = {
        "sentence_transformers": {
            "model_name": "all-MiniLM-L6-v2",
            "device": "cpu",
            "max_seq_length": 512,
            "normalize_embeddings": True,
            "batch_size": 32
        },
        "openai": {
            "api_key": "",
            "model": "text-embedding-3-small",
            "dimensions": 1536,
            "base_url": "https://api.openai.com/v1",
            "timeout": 60
        },
        "cohere": {
            "api_key": "",
            "model": "embed-multilingual-v3.0",
            "input_type": "search_document",
            "truncate": "END",
            "timeout": 60
        },
        "huggingface": {
            "api_token": "",
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "task": "feature-extraction",
            "wait_for_model": True,
            "timeout": 60
        }
    }

class VectorIndexProviderConfig(BaseModel):
    """Vector index provider configuration"""
    enabled: bool = True
    default_provider: str = "turbovec"
    providers: Dict[str, Dict[str, Any]] = {
        "turbovec": {
            "dimension": 384,
            "metric": "cosine",
            "store_metadata": True
        },
        "faiss": {
            "dimension": 384,
            "index_type": "Flat",
            "metric": "IP",
            "nprobe": 10,
            "ef_search": 40,
            "use_gpu": False
        },
        "qdrant": {
            "url": "http://localhost:6333",
            "api_key": "",
            "collection": "rag_collection",
            "vector_size": 384,
            "distance": "Cosine",
            "recreate_collection": False,
            "timeout": 30
        },
        "chroma": {
            "path": "./chroma_db",
            "collection": "rag_collection",
            "tenant": "default_tenant",
            "database": "default_database",
            "metadata": {}
        }
    }

class ChunkingConfig(BaseModel):
    """Text chunking configuration"""
    strategy: Literal["recursive", "semantic", "fixed"] = "recursive"
    chunk_size: int = Field(default=512, ge=100, le=4096)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    separators: Optional[List[str]] = ["\n\n", "\n", ". ", " ", ""]
    min_chunk_size: int = Field(default=50, ge=10)
    keep_separator: bool = False
    strip_whitespace: bool = True

class TextCleaningConfig(BaseModel):
    """Text cleaning configuration"""
    remove_extra_whitespace: bool = True
    remove_special_chars: bool = False
    normalize_unicode: bool = True
    lowercase: bool = False
    remove_numbers: bool = False
    custom_patterns: List[str] = []
    preserve_formatting: bool = True

class PipelineDefaultsConfig(BaseModel):
    """Pipeline default configuration"""
    ocr_provider: str = "tesseract"
    llm_provider: str = "ollama"
    embedding_provider: str = "sentence_transformers"
    vector_index_provider: str = "turbovec"
    auto_start_pipeline: bool = False
    parallel_processing: bool = False
    max_retries: int = 3
    retry_delay_seconds: int = 5

class PathConfig(BaseModel):
    """Path configuration"""
    upload_directory: str = "./uploads"
    output_directory: str = "./output"
    database_path: str = "./rag_studio.db"
    cache_directory: str = "./cache"
    logs_directory: str = "./logs"

class SettingsResponse(BaseModel):
    """Complete settings response"""
    ocr: OCRProviderConfig
    llm: LLMProviderConfig
    embedding: EmbeddingProviderConfig
    vector_index: VectorIndexProviderConfig
    chunking: ChunkingConfig
    text_cleaning: TextCleaningConfig
    pipeline_defaults: PipelineDefaultsConfig
    paths: PathConfig
    version: str = "1.0.0"


# ============================================
# In-memory settings storage (replace with DB in production)
# ============================================

_current_settings = SettingsResponse(
    ocr=OCRProviderConfig(),
    llm=LLMProviderConfig(),
    embedding=EmbeddingProviderConfig(),
    vector_index=VectorIndexProviderConfig(),
    chunking=ChunkingConfig(),
    text_cleaning=TextCleaningConfig(),
    pipeline_defaults=PipelineDefaultsConfig(),
    paths=PathConfig()
)


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


def get_provider_schema(provider_type: str, provider_name: str) -> Dict[str, Any]:
    """Get configuration schema for a specific provider"""
    schemas = {
        "ocr": {
            "tesseract": {
                "description": "Open source OCR by Google - Tesseract",
                "config_schema": {
                    "lang": {"type": "string", "default": "eng", "description": "Language code"},
                    "psm": {"type": "integer", "default": 6, "description": "Page segmentation mode"},
                    "oem": {"type": "integer", "default": 3, "description": "OCR Engine Mode"},
                    "timeout": {"type": "integer", "default": 30, "description": "Timeout in seconds"}
                }
            },
            "paddleocr": {
                "description": "PaddlePaddle OCR - Multi-language OCR",
                "config_schema": {
                    "lang": {"type": "string", "default": "en", "description": "Language code"},
                    "use_gpu": {"type": "boolean", "default": False, "description": "Use GPU acceleration"},
                    "show_log": {"type": "boolean", "default": False, "description": "Show logging output"},
                    "det_model_dir": {"type": "string", "nullable": True, "description": "Detection model directory"},
                    "rec_model_dir": {"type": "string", "nullable": True, "description": "Recognition model directory"}
                }
            },
            "easyocr": {
                "description": "EasyOCR - Ready-to-use OCR with 80+ languages",
                "config_schema": {
                    "lang": {"type": "array", "default": ["en"], "description": "List of language codes"},
                    "gpu": {"type": "boolean", "default": False, "description": "Use GPU"},
                    "model_storage_directory": {"type": "string", "nullable": True, "description": "Model storage path"},
                    "download_enabled": {"type": "boolean", "default": True, "description": "Enable model download"}
                }
            }
        },
        "llm": {
            "ollama": {
                "description": "Ollama - Run LLMs locally",
                "config_schema": {
                    "base_url": {"type": "string", "default": "http://localhost:11434", "description": "Ollama server URL"},
                    "model": {"type": "string", "default": "llama3.2", "description": "Model name"},
                    "timeout": {"type": "integer", "default": 120, "description": "Request timeout"},
                    "num_ctx": {"type": "integer", "default": 4096, "description": "Context window size"}
                }
            },
            "openai": {
                "description": "OpenAI GPT Models",
                "config_schema": {
                    "api_key": {"type": "string", "default": "", "description": "OpenAI API key", "sensitive": True},
                    "base_url": {"type": "string", "default": "https://api.openai.com/v1", "description": "API base URL"},
                    "model": {"type": "string", "default": "gpt-4o-mini", "description": "Model name"},
                    "temperature": {"type": "number", "default": 0.7, "description": "Sampling temperature"},
                    "max_tokens": {"type": "integer", "default": 2048, "description": "Max tokens in response"},
                    "timeout": {"type": "integer", "default": 60, "description": "Request timeout"}
                }
            },
            "gemini": {
                "description": "Google Gemini AI",
                "config_schema": {
                    "api_key": {"type": "string", "default": "", "description": "Google API key", "sensitive": True},
                    "model": {"type": "string", "default": "gemini-1.5-flash", "description": "Model name"},
                    "temperature": {"type": "number", "default": 0.7, "description": "Sampling temperature"},
                    "max_output_tokens": {"type": "integer", "default": 2048, "description": "Max output tokens"},
                    "timeout": {"type": "integer", "default": 60, "description": "Request timeout"}
                }
            },
            "anthropic": {
                "description": "Anthropic Claude",
                "config_schema": {
                    "api_key": {"type": "string", "default": "", "description": "Anthropic API key", "sensitive": True},
                    "base_url": {"type": "string", "default": "https://api.anthropic.com", "description": "API base URL"},
                    "model": {"type": "string", "default": "claude-3-5-sonnet-20241022", "description": "Model name"},
                    "temperature": {"type": "number", "default": 0.7, "description": "Sampling temperature"},
                    "max_tokens": {"type": "integer", "default": 2048, "description": "Max tokens in response"},
                    "timeout": {"type": "integer", "default": 60, "description": "Request timeout"}
                }
            }
        },
        "embedding": {
            "sentence_transformers": {
                "description": "HuggingFace Sentence Transformers",
                "config_schema": {
                    "model_name": {"type": "string", "default": "all-MiniLM-L6-v2", "description": "Model name"},
                    "device": {"type": "string", "default": "cpu", "description": "Device (cpu/cuda)"},
                    "max_seq_length": {"type": "integer", "default": 512, "description": "Max sequence length"},
                    "normalize_embeddings": {"type": "boolean", "default": True, "description": "Normalize output vectors"},
                    "batch_size": {"type": "integer", "default": 32, "description": "Batch size for encoding"}
                }
            },
            "openai": {
                "description": "OpenAI Embeddings",
                "config_schema": {
                    "api_key": {"type": "string", "default": "", "description": "OpenAI API key", "sensitive": True},
                    "model": {"type": "string", "default": "text-embedding-3-small", "description": "Model name"},
                    "dimensions": {"type": "integer", "default": 1536, "description": "Embedding dimensions"},
                    "base_url": {"type": "string", "default": "https://api.openai.com/v1", "description": "API base URL"},
                    "timeout": {"type": "integer", "default": 60, "description": "Request timeout"}
                }
            },
            "cohere": {
                "description": "Cohere Embeddings",
                "config_schema": {
                    "api_key": {"type": "string", "default": "", "description": "Cohere API key", "sensitive": True},
                    "model": {"type": "string", "default": "embed-multilingual-v3.0", "description": "Model name"},
                    "input_type": {"type": "string", "default": "search_document", "description": "Input type hint"},
                    "truncate": {"type": "string", "default": "END", "description": "Truncation strategy"},
                    "timeout": {"type": "integer", "default": 60, "description": "Request timeout"}
                }
            },
            "huggingface": {
                "description": "HuggingFace Inference API",
                "config_schema": {
                    "api_token": {"type": "string", "default": "", "description": "HF API token", "sensitive": True},
                    "model": {"type": "string", "default": "sentence-transformers/all-MiniLM-L6-v2", "description": "Model ID"},
                    "task": {"type": "string", "default": "feature-extraction", "description": "Task type"},
                    "wait_for_model": {"type": "boolean", "default": True, "description": "Wait for model to load"},
                    "timeout": {"type": "integer", "default": 60, "description": "Request timeout"}
                }
            }
        },
        "vector_index": {
            "turbovec": {
                "description": "TurboVec - Lightweight in-memory vector index",
                "config_schema": {
                    "dimension": {"type": "integer", "default": 384, "description": "Vector dimension"},
                    "metric": {"type": "string", "default": "cosine", "description": "Distance metric"},
                    "store_metadata": {"type": "boolean", "default": True, "description": "Store metadata with vectors"}
                }
            },
            "faiss": {
                "description": "Facebook AI Similarity Search",
                "config_schema": {
                    "dimension": {"type": "integer", "default": 384, "description": "Vector dimension"},
                    "index_type": {"type": "string", "default": "Flat", "description": "Index type (Flat, IVF, HNSW)"},
                    "metric": {"type": "string", "default": "IP", "description": "Metric (IP, L2)"},
                    "nprobe": {"type": "integer", "default": 10, "description": "Number of probes for IVF"},
                    "ef_search": {"type": "integer", "default": 40, "description": "ef parameter for HNSW"},
                    "use_gpu": {"type": "boolean", "default": False, "description": "Use GPU acceleration"}
                }
            },
            "qdrant": {
                "description": "Qdrant Vector Database",
                "config_schema": {
                    "url": {"type": "string", "default": "http://localhost:6333", "description": "Qdrant server URL"},
                    "api_key": {"type": "string", "default": "", "description": "API key", "sensitive": True},
                    "collection": {"type": "string", "default": "rag_collection", "description": "Collection name"},
                    "vector_size": {"type": "integer", "default": 384, "description": "Vector size"},
                    "distance": {"type": "string", "default": "Cosine", "description": "Distance function"},
                    "recreate_collection": {"type": "boolean", "default": False, "description": "Recreate if exists"},
                    "timeout": {"type": "integer", "default": 30, "description": "Request timeout"}
                }
            },
            "chroma": {
                "description": "Chroma Vector Database",
                "config_schema": {
                    "path": {"type": "string", "default": "./chroma_db", "description": "Database path"},
                    "collection": {"type": "string", "default": "rag_collection", "description": "Collection name"},
                    "tenant": {"type": "string", "default": "default_tenant", "description": "Tenant name"},
                    "database": {"type": "string", "default": "default_database", "description": "Database name"},
                    "metadata": {"type": "object", "default": {}, "description": "Additional metadata"}
                }
            }
        }
    }
    
    return schemas.get(provider_type, {}).get(provider_name, {})


# ============================================
# API Endpoints
# ============================================

@router.get("", response_model=SettingsResponse)
async def get_all_settings():
    """Get complete settings configuration"""
    return _current_settings


@router.get("/providers")
async def get_all_providers():
    """Get all available providers and their configurations"""
    return {
        "available_providers": get_available_providers(),
        "defaults": {
            "ocr": _current_settings.ocr.default_provider,
            "llm": _current_settings.llm.default_provider,
            "embedding": _current_settings.embedding.default_provider,
            "vector_index": _current_settings.vector_index.default_provider
        },
        "configurations": {
            "ocr": _current_settings.ocr.providers,
            "llm": _current_settings.llm.providers,
            "embedding": _current_settings.embedding.providers,
            "vector_index": _current_settings.vector_index.providers
        }
    }


@router.get("/providers/{provider_type}")
async def get_provider_type_config(provider_type: str):
    """Get configuration for a specific provider type"""
    if provider_type not in ["ocr", "llm", "embedding", "vector_index"]:
        raise HTTPException(status_code=404, detail=f"Provider type '{provider_type}' not found")
    
    config_map = {
        "ocr": _current_settings.ocr,
        "llm": _current_settings.llm,
        "embedding": _current_settings.embedding,
        "vector_index": _current_settings.vector_index
    }
    
    return {
        "provider_type": provider_type,
        "enabled": config_map[provider_type].enabled,
        "default_provider": config_map[provider_type].default_provider,
        "providers": config_map[provider_type].providers,
        "schemas": {
            name: get_provider_schema(provider_type, name)
            for name in get_available_providers().get(provider_type, [])
        }
    }


@router.get("/providers/{provider_type}/{provider_name}")
async def get_specific_provider(provider_type: str, provider_name: str):
    """Get configuration for a specific provider"""
    available = get_available_providers()
    
    if provider_type not in available:
        raise HTTPException(status_code=404, detail=f"Provider type '{provider_type}' not found")
    
    if provider_name not in available[provider_type]:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found for type '{provider_type}'")
    
    config_map = {
        "ocr": _current_settings.ocr,
        "llm": _current_settings.llm,
        "embedding": _current_settings.embedding,
        "vector_index": _current_settings.vector_index
    }
    
    provider_config = config_map[provider_type].providers.get(provider_name, {})
    schema = get_provider_schema(provider_type, provider_name)
    
    return {
        "provider_type": provider_type,
        "provider_name": provider_name,
        "is_default": config_map[provider_type].default_provider == provider_name,
        "configuration": provider_config,
        "schema": schema
    }


@router.post("/providers/{provider_type}/default")
async def set_default_provider(
    provider_type: str,
    provider_name: str = Query(..., description="Provider name to set as default")
):
    """Set default provider for a provider type"""
    available = get_available_providers()
    
    if provider_type not in available:
        raise HTTPException(status_code=404, detail=f"Provider type '{provider_type}' not found")
    
    if provider_name not in available[provider_type]:
        raise HTTPException(status_code=400, detail=f"Invalid provider '{provider_name}' for type '{provider_type}'")
    
    config_map = {
        "ocr": _current_settings.ocr,
        "llm": _current_settings.llm,
        "embedding": _current_settings.embedding,
        "vector_index": _current_settings.vector_index
    }
    
    config_map[provider_type].default_provider = provider_name
    
    return {
        "message": f"Default {provider_type} provider set to '{provider_name}'",
        "provider_type": provider_type,
        "default_provider": provider_name
    }


@router.put("/providers/{provider_type}/{provider_name}/config")
async def update_provider_config(
    provider_type: str,
    provider_name: str,
    config: Dict[str, Any]
):
    """Update configuration for a specific provider"""
    available = get_available_providers()
    
    if provider_type not in available:
        raise HTTPException(status_code=404, detail=f"Provider type '{provider_type}' not found")
    
    if provider_name not in available[provider_type]:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    config_map = {
        "ocr": _current_settings.ocr,
        "llm": _current_settings.llm,
        "embedding": _current_settings.embedding,
        "vector_index": _current_settings.vector_index
    }
    
    # Update the provider configuration
    if provider_name in config_map[provider_type].providers:
        config_map[provider_type].providers[provider_name].update(config)
    else:
        config_map[provider_type].providers[provider_name] = config
    
    return {
        "message": f"Configuration updated for {provider_type}/{provider_name}",
        "provider_type": provider_type,
        "provider_name": provider_name,
        "configuration": config_map[provider_type].providers[provider_name]
    }


@router.get("/chunking")
async def get_chunking_config():
    """Get chunking configuration"""
    return _current_settings.chunking


@router.put("/chunking")
async def update_chunking_config(config: ChunkingConfig):
    """Update chunking configuration"""
    _current_settings.chunking = config
    return {
        "message": "Chunking configuration updated",
        "configuration": config.model_dump()
    }


@router.get("/text-cleaning")
async def get_text_cleaning_config():
    """Get text cleaning configuration"""
    return _current_settings.text_cleaning


@router.put("/text-cleaning")
async def update_text_cleaning_config(config: TextCleaningConfig):
    """Update text cleaning configuration"""
    _current_settings.text_cleaning = config
    return {
        "message": "Text cleaning configuration updated",
        "configuration": config.model_dump()
    }


@router.get("/pipeline")
async def get_pipeline_defaults():
    """Get pipeline default configuration"""
    return _current_settings.pipeline_defaults


@router.put("/pipeline")
async def update_pipeline_defaults(config: PipelineDefaultsConfig):
    """Update pipeline default configuration"""
    _current_settings.pipeline_defaults = config
    return {
        "message": "Pipeline defaults updated",
        "configuration": config.model_dump()
    }


@router.get("/paths")
async def get_path_config():
    """Get path configuration"""
    return _current_settings.paths


@router.put("/paths")
async def update_path_config(config: PathConfig):
    """Update path configuration"""
    _current_settings.paths = config
    return {
        "message": "Path configuration updated",
        "configuration": config.model_dump()
    }


@router.post("/reset")
async def reset_to_defaults():
    """Reset all settings to defaults"""
    global _current_settings
    _current_settings = SettingsResponse(
        ocr=OCRProviderConfig(),
        llm=LLMProviderConfig(),
        embedding=EmbeddingProviderConfig(),
        vector_index=VectorIndexProviderConfig(),
        chunking=ChunkingConfig(),
        text_cleaning=TextCleaningConfig(),
        pipeline_defaults=PipelineDefaultsConfig(),
        paths=PathConfig()
    )
    return {"message": "All settings reset to defaults"}


@router.get("/export")
async def export_settings():
    """Export current settings as JSON"""
    return _current_settings.model_dump(mode='json')


@router.post("/import")
async def import_settings(settings_data: Dict[str, Any]):
    """Import settings from JSON"""
    global _current_settings
    try:
        _current_settings = SettingsResponse(**settings_data)
        return {"message": "Settings imported successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid settings format: {str(e)}")
