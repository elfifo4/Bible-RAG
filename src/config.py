from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Data Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "index"

# File Paths
CHAPTERS_DIR = PROCESSED_DIR / "chapters"
ALL_VERSES_JSONL = PROCESSED_DIR / "all_verses.jsonl"
ALL_CHUNKS_JSONL = PROCESSED_DIR / "all_chunks.jsonl"
MANIFEST_FILE = DATA_DIR / "MANIFEST.md"

# Model Configurations
# Using a Hebrew-optimized model for embeddings
EMBEDDING_MODEL_NAME = "dicta-il/dictabert"
VECTOR_DB_PATH = INDEX_DIR / "vector_store.faiss"

# RAG Hyperparameters
TOP_K = 5
CHUNK_STRATEGY = "single_verse"  # options: single_verse, sliding_window, paragraph
