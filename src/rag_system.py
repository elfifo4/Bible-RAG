import time
from typing import Dict, Any, List, Optional
from .retrieval import VectorRetriever
from .generation import BibleGenerator
from .config import TOP_K, EMBEDDING_MODEL_NAME
from .utils import logger

class BibleRAG:
    def __init__(self):
        self.retriever = VectorRetriever()
        self.generator = BibleGenerator()

    def answer(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"Answering question: {question}")

        k = top_k or TOP_K

        # 1. Retrieval
        context_chunks = self.retriever.retrieve(question, top_k=k)

        # 2. Generation
        answer_text = self.generator.generate(question, context_chunks)

        latency_ms = int((time.time() - start_time) * 1000)

        # 3. Format response
        return {
            "question": question,
            "answer": answer_text,
            "context": [
                {
                    "ref": c["metadata"]["ref"],
                    "ref_en": c["metadata"]["ref_en"],
                    "book": c["metadata"].get("book"),
                    "book_en": c["metadata"].get("book_en"),
                    "chapter": c["metadata"].get("chapter"),
                    "verse_start": c["metadata"].get("verse_start"),
                    "verse_end": c["metadata"].get("verse_end"),
                    "text": c["display_text"],
                    "score": c.get("score", 0),
                    "chunk_id": c["chunk_id"],
                    "chunk_type": c["metadata"].get("chunk_type")
                }
                for c in context_chunks
            ],
            "debug": {
                "latency_ms": latency_ms,
                "top_k": k,
                "embedding_model": EMBEDDING_MODEL_NAME,
                "retrieval_strategy": "semantic"
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
