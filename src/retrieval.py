import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from .config import (
    ALL_CHUNKS_JSONL,
    EMBEDDING_MODEL_NAME,
    VECTOR_DB_PATH,
    QUERY_PREFIX,
    PASSAGE_PREFIX
)
from .utils import logger, timer

class VectorRetriever:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading embedding model: {model_name}...")
        # device='cpu' or 'cuda' or 'mps' (for Mac M1/M2)
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []
        self._load_chunks()

    def _load_chunks(self):
        if not ALL_CHUNKS_JSONL.exists():
            logger.warning(f"{ALL_CHUNKS_JSONL} not found.")
            return

        logger.info(f"Loading chunks from {ALL_CHUNKS_JSONL}...")
        with open(ALL_CHUNKS_JSONL, 'r', encoding='utf-8') as f:
            for line in f:
                self.chunks.append(json.loads(line))
        logger.info(f"Loaded {len(self.chunks)} chunks.")

    @timer
    def build_index(self):
        import faiss

        if not self.chunks:
            raise ValueError("No chunks loaded to build index.")

        # E5 requires 'passage: ' prefix for documents
        texts = [f"{PASSAGE_PREFIX}{c['text']}" for c in self.chunks]

        logger.info(f"Encoding {len(texts)} chunks (this may take a while)...")
        # SentenceTransformers can do L2 normalization automatically
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization
        )

        dimension = embeddings.shape[1]
        logger.info(f"Embedding dimension: {dimension}")

        # Using IndexFlatIP (Inner Product) for Cosine Similarity with normalized vectors
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype('float32'))

        VECTOR_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(VECTOR_DB_PATH))
        logger.info(f"Index saved to {VECTOR_DB_PATH}")

    def load_index(self):
        import faiss
        if VECTOR_DB_PATH.exists():
            logger.info(f"Loading index from {VECTOR_DB_PATH}...")
            self.index = faiss.read_index(str(VECTOR_DB_PATH))
        else:
            logger.error(f"Index file not found at {VECTOR_DB_PATH}")

    @timer
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.index is None:
            self.load_index()
            if self.index is None:
                return []

        # E5 requires 'query: ' prefix for queries
        query_text = f"{QUERY_PREFIX}{query}"

        query_embedding = self.model.encode(
            [query_text],
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                chunk["score"] = float(score)
                results.append(chunk)

        return results
