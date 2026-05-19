import json
import re
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from .config import (
    ALL_CHUNKS_JSONL, 
    EMBEDDING_MODEL_NAME, 
    VECTOR_DB_PATH, 
    QUERY_PREFIX, 
    PASSAGE_PREFIX
)
from .utils import logger, timer

HEBREW_STOPWORDS = {
    "מי", "מה", "מתי", "איפה", "היכן", "האם", "את", "של", "על", "אל", "עם", "בין", "בהם", "בהן",
    "היה", "הייתה", "היו", "הוא", "היא", "הם", "הן", "לי", "תן", "תני", "נא", "בבקשה"
}

class HebrewTokenizer:
    @staticmethod
    def tokenize(text: str) -> List[str]:
        # Simple Hebrew tokenization: keep only Hebrew letters
        tokens = re.findall(r"[א-ת]+", text)
        # Filter stopwords and short tokens
        return [t for t in tokens if t not in HEBREW_STOPWORDS and len(t) > 1]

    @staticmethod
    def strip_prefixes(token: str) -> str:
        # Common Hebrew prefixes: ו, ב, כ, ל, מ, ה
        if len(token) > 3:
            if token[0] in "ובכלמה":
                return token[1:]
        return token

class VectorRetriever:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        from sentence_transformers import SentenceTransformer
        
        logger.info(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []
        self.bm25 = None
        self._load_chunks()
        self._init_bm25()

    def _load_chunks(self):
        if not ALL_CHUNKS_JSONL.exists():
            logger.warning(f"{ALL_CHUNKS_JSONL} not found.")
            return
        
        logger.info(f"Loading chunks from {ALL_CHUNKS_JSONL}...")
        self.chunks = []
        with open(ALL_CHUNKS_JSONL, 'r', encoding='utf-8') as f:
            for line in f:
                self.chunks.append(json.loads(line))
        logger.info(f"Loaded {len(self.chunks)} chunks.")

    def _init_bm25(self):
        if not self.chunks:
            return
        logger.info("Initializing BM25 index...")
        tokenized_corpus = [HebrewTokenizer.tokenize(c["text"]) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    @timer
    def build_index(self):
        import faiss
        if not self.chunks:
            raise ValueError("No chunks loaded to build index.")

        texts = [f"{PASSAGE_PREFIX}{c['text']}" for c in self.chunks]
        logger.info(f"Encoding {len(texts)} chunks...")
        embeddings = self.model.encode(
            texts, 
            show_progress_bar=True, 
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        dimension = embeddings.shape[1]
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

    def _detect_query_type(self, query: str) -> str:
        query_lower = query.lower()
        if any(w in query_lower for w in ["איפה", "היכן", "תן לי מקומות", "באילו מקומות", "איפה כתוב"]):
            return "enumeration"
        if any(w in query_lower for w in ["מי הוליד", "מי אבא של", "מי אביו של"]):
            return "genealogy"
        return "general"

    @timer
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5, 
        strategy: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        if self.index is None:
            self.load_index()
            if self.index is None: return []

        query_type = self._detect_query_type(query)
        
        # Decide weights based on query type
        dense_weight = 0.65
        lexical_weight = 0.35
        if query_type == "enumeration":
            dense_weight = 0.4
            lexical_weight = 0.6
        elif query_type == "genealogy":
            dense_weight = 0.5
            lexical_weight = 0.5

        if strategy == "dense_only":
            return self._dense_search(query, top_k)
        elif strategy == "lexical_only":
            return self._lexical_search(query, top_k)
        elif strategy == "hybrid":
            return self._hybrid_search(query, top_k, dense_weight, lexical_weight, query_type)
        elif strategy in ["single_verse", "sliding_window"]:
            return self._filtered_search(query, top_k, strategy)
        else:
            return self._hybrid_search(query, top_k, dense_weight, lexical_weight, query_type)

    def _dense_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        query_text = f"{QUERY_PREFIX}{query}"
        query_embedding = self.model.encode([query_text], normalize_embeddings=True, convert_to_numpy=True)
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):
                res = self.chunks[idx].copy()
                res["score"] = float(score)
                res["dense_score"] = float(score)
                res["lexical_score"] = 0.0
                results.append(res)
        return results

    def _lexical_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        if not self.bm25: return []
        tokenized_query = HebrewTokenizer.tokenize(query)
        # BM25 scores can be large, we might want to normalize them later
        bm25_scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(bm25_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = bm25_scores[idx]
            if score > 0:
                res = self.chunks[idx].copy()
                res["score"] = float(score)
                res["lexical_score"] = float(score)
                res["dense_score"] = 0.0
                results.append(res)
        return results

    def _hybrid_search(self, query: str, top_k: int, d_w: float, l_w: float, q_type: str) -> List[Dict[str, Any]]:
        candidate_k = 50
        
        # Get Dense candidates
        query_text = f"{QUERY_PREFIX}{query}"
        query_embedding = self.model.encode([query_text], normalize_embeddings=True, convert_to_numpy=True)
        d_scores, d_indices = self.index.search(query_embedding.astype('float32'), candidate_k)
        
        # Get Lexical candidates
        tokenized_query = HebrewTokenizer.tokenize(query)
        l_scores = self.bm25.get_scores(tokenized_query) if self.bm25 else np.zeros(len(self.chunks))
        
        # Merge by chunk_id
        combined_results = {}
        
        # Add dense candidates
        max_d = np.max(d_scores) if d_scores.size > 0 else 1.0
        for score, idx in zip(d_scores[0], d_indices[0]):
            if idx < len(self.chunks):
                c = self.chunks[idx]
                cid = c["chunk_id"]
                norm_d = score / max_d if max_d > 0 else score
                combined_results[cid] = {
                    "chunk": c,
                    "dense_score": float(norm_d),
                    "lexical_score": 0.0
                }
        
        # Add lexical candidates
        max_l = np.max(l_scores) if np.any(l_scores) else 1.0
        l_top_indices = np.argsort(l_scores)[::-1][:candidate_k]
        for idx in l_top_indices:
            score = l_scores[idx]
            if score <= 0: continue
            c = self.chunks[idx]
            cid = c["chunk_id"]
            norm_l = score / max_l if max_l > 0 else score
            if cid in combined_results:
                combined_results[cid]["lexical_score"] = float(norm_l)
            else:
                combined_results[cid] = {
                    "chunk": c,
                    "dense_score": 0.0,
                    "lexical_score": float(norm_l)
                }
        
        # Calculate final scores
        final_list = []
        for cid, data in combined_results.items():
            final_score = (d_w * data["dense_score"]) + (l_w * data["lexical_score"])
            res = data["chunk"].copy()
            res["score"] = final_score
            res["dense_score"] = data["dense_score"]
            res["lexical_score"] = data["lexical_score"]
            final_list.append(res)
            
        final_list.sort(key=lambda x: x["score"], reverse=True)
        
        # Add debug info to results if needed, but here we just return top_k
        return final_list[:top_k]

    def _filtered_search(self, query: str, top_k: int, strategy: str) -> List[Dict[str, Any]]:
        # This is a naive implementation: search all and filter.
        # For a more production-ready approach, we should have separate indexes.
        results = self._hybrid_search(query, top_k * 4, 0.65, 0.35, "general")
        filtered = [r for r in results if r["metadata"].get("chunk_type") == strategy]
        return filtered[:top_k]
