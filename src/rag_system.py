from src.retrieval import VectorRetriever
from src.generation import BibleGenerator
from src.config import TOP_K

class BibleRAG:
    def __init__(self):
        self.retriever = VectorRetriever()
        self.generator = BibleGenerator()

    def answer(self, question: str) -> dict:
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
                    "text": c["display_text"]
                }
                for c in context_chunks
            ]
        }

if __name__ == "__main__":
    rag = BibleRAG()
    res = rag.answer("How was the world created?")
    print(res["answer"])
    for src in res["context"]:
        print(f"- {src['ref_en']}")
