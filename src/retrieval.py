import json
import numpy as np
from pathlib import Path
from typing import List, Dict
from src.config import ALL_CHUNKS_JSONL, EMBEDDING_MODEL_NAME, VECTOR_DB_PATH

class VectorRetriever:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        from sentence_transformers import SentenceTransformer
        import faiss

        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []
        self._load_chunks()

    def _load_chunks(self):
        if not ALL_CHUNKS_JSONL.exists():
            print(f"Warning: {ALL_CHUNKS_JSONL} not found. Did you run build_index?")
            return
        print(f"Loading chunks from {ALL_CHUNKS_JSONL}...")
        with open(ALL_CHUNKS_JSONL, 'r', encoding='utf-8') as f:
            for line in f:
                self.chunks.append(json.loads(line))
        print(f"Loaded {len(self.chunks)} chunks.")

    def build_index(self):
        import faiss
        texts = [c["text"] for c in self.chunks]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))

        # Save index
        faiss.write_index(self.index, str(VECTOR_DB_PATH))

    def load_index(self):
        import faiss
        if VECTOR_DB_PATH.exists():
            self.index = faiss.read_index(str(VECTOR_DB_PATH))

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.index is None:
            self.load_index()

        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), top_k)

        results = []
        for idx in indices[0]:
            if idx < len(self.chunks):
                results.append(self.chunks[idx])
        return results
