"""
Configuration settings for RAG Studio
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
DB_DIR = BASE_DIR / "db"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# Database settings
DATABASE_PATH = DB_DIR / "rag_studio.db"

# Pipeline settings
PIPELINE_STATUS_DIR = OUTPUT_DIR / "pipeline_status"
PIPELINE_STATUS_DIR.mkdir(exist_ok=True)

# Default providers
DEFAULT_OCR_PROVIDER = "tesseract"
DEFAULT_LLM_PROVIDER = "ollama"
DEFAULT_EMBEDDING_PROVIDER = "sentence_transformers"
DEFAULT_VECTOR_INDEX_PROVIDER = "turbovec"

# Model settings
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_EMBEDDING_DIMENSION = 384

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# File validation
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_MB = 100

