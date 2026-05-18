from typing import List, Dict

class BibleGenerator:
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name

    def _build_prompt(self, question: str, context_chunks: List[Dict]) -> str:
        context_text = "\n\n".join([
            f"Source: {c['metadata']['ref_en']} ({c['metadata']['ref']})\nText: {c['display_text']}"
            for c in context_chunks
        ])

        prompt = f"""You are an expert biblical scholar. Answer the question based ONLY on the provided biblical context.
If the answer is not in the context, say you don't know.
Always cite the Book, Chapter, and Verse in your answer.

Context:
{context_text}

Question: {question}
Answer:"""
        return prompt

    def generate(self, question: str, context_chunks: List[Dict]) -> str:
        # In a real system, you'd call an LLM API here.
        # For now, we'll return a placeholder or the prompt for debugging.
        prompt = self._build_prompt(question, context_chunks)

        # mock_llom_call(prompt)
        return f"[Generated answer for: {question} using {len(context_chunks)} sources]"
