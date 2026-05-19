import time
from typing import Dict, Any, List, Optional
from .retrieval import VectorRetriever
from .generation import BibleGenerator
from .metadata_retriever import MetadataRetriever
from .config import TOP_K, EMBEDDING_MODEL_NAME
from .utils import logger

class BibleRAG:
    def __init__(self):
        self.retriever = VectorRetriever()
        self.generator = BibleGenerator()
        self.metadata_retriever = MetadataRetriever()

    def answer(
        self, 
        question: str, 
        top_k: Optional[int] = None, 
        retrieval_strategy: str = "hybrid"
    ) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"Answering question: {question} (Strategy: {retrieval_strategy})")
        
        # Check metadata first
        metadata_answer = self.metadata_retriever.retrieve(question)
        if metadata_answer:
            return {
                "answer": metadata_answer,
                "sources": ["Metadata"],
                "retrieved_chunks": [],
                "debug": {
                    "latency_ms": int((time.time() - start_time) * 1000),
                    "retrieval_strategy": "metadata",
                    "query_type": "metadata"
                }
            }

        k = top_k or TOP_K

        # 1. Retrieval
        context_chunks = self.retriever.retrieve(question, top_k=k, strategy=retrieval_strategy)

        # 2. Generation
        answer_text = self.generator.generate(question, context_chunks)
        
        latency_ms = int((time.time() - start_time) * 1000)

        # 3. Format response
        return {
            "answer": answer_text,
            "sources": [c["metadata"]["ref_en"] for c in context_chunks],
            "retrieved_chunks": [
                {
                    "chunk_id": c["chunk_id"],
                    "text": c["text"],
                    "display_text": c["display_text"],
                    "score": c.get("score", 0),
                    "dense_score": c.get("dense_score", 0),
                    "lexical_score": c.get("lexical_score", 0),
                    "metadata": c["metadata"]
                }
                for c in context_chunks
            ],
            "debug": {
                "latency_ms": latency_ms,
                "top_k": k,
                "embedding_model": EMBEDDING_MODEL_NAME,
                "retrieval_strategy": retrieval_strategy,
                "query_type": self.retriever._detect_query_type(question)
            }
        }

if __name__ == "__main__":
    # Quick sanity check
    rag = BibleRAG()
    res = rag.answer("מי היה אבא של אברהם?")
    print(f"\nQ: {res['question']}")
    print(f"A: {res['answer']}")
    print("\nSources:")
    for c in res['context']:
        print(f"[{c['score']:.4f}] {c['ref_en']}")
