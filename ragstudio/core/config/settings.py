"""
Configuration settings for RAG Studio
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = BASE_DIR.parent  # ragstudio/ parent

# Core directories
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
DB_DIR = BASE_DIR / "db"

# Production feature directories
CACHE_DIR = PROJECT_ROOT / "cache"
CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
LOGS_DIR = PROJECT_ROOT / "logs"
INDEXES_DIR = PROJECT_ROOT / "indexes"
TEMP_DIR = PROJECT_ROOT / "temp"
PLUGINS_DIR = PROJECT_ROOT / "plugins"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
CHECKPOINT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
INDEXES_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
PLUGINS_DIR.mkdir(exist_ok=True)

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

# Cache settings
CACHE_DEFAULT_TTL_HOURS = 24
CACHE_MAX_SIZE_MB = 1000

# Checkpoint settings
CHECKPOINT_ENABLED = True
CHECKPOINT_INTERVAL_SECONDS = 30

# Retry settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 1.0
DEFAULT_RETRY_MAX_DELAY = 60.0

# Job settings
JOB_TIMEOUT_SECONDS = 3600  # 1 hour default timeout
MAX_CONCURRENT_JOBS = 5
