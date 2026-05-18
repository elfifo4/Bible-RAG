from typing import Dict, Any, List
from .retrieval import VectorRetriever
from .generation import BibleGenerator
from .config import TOP_K
from .utils import logger

class BibleRAG:
    def __init__(self):
        self.retriever = VectorRetriever()
        self.generator = BibleGenerator()

    def answer(self, question: str) -> Dict[str, Any]:
        logger.info(f"Answering question: {question}")

        # 1. Retrieval
        context_chunks = self.retriever.retrieve(question, top_k=TOP_K)

        # 2. Generation
        answer_text = self.generator.generate(question, context_chunks)

        # 3. Format response
        return {
            "question": question,
            "answer": answer_text,
            "context": [
                {
                    "ref": c["metadata"]["ref"],
                    "ref_en": c["metadata"]["ref_en"],
                    "text": c["display_text"],
                    "score": c.get("score", 0),
                    "chunk_id": c["chunk_id"]
                }
                for c in context_chunks
            ]
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
