from pathlib import Path
import os


# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "index"

# File Paths
CHAPTERS_DIR = PROCESSED_DIR / "chapters"
ALL_VERSES_JSONL = PROCESSED_DIR / "all_verses.jsonl"
ALL_CHUNKS_JSONL = PROCESSED_DIR / "all_chunks.jsonl"

# Model Configurations
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"
VECTOR_DB_PATH = INDEX_DIR / "vector_store.faiss"

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set. "
        "Run: export OPENAI_API_KEY='your-real-key'"
    )

LLM_MODEL_NAME = "gpt-4o"

# RAG Hyperparameters
TOP_K = 5
CHUNK_STRATEGY = "sliding_window"  # options: "single_verse", "sliding_window"

# Sliding Window Params
WINDOW_SIZE = 5
WINDOW_OVERLAP = 2

# E5 Specific
QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "
