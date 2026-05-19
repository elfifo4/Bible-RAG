import openai
from typing import List, Dict, Any
from .config import OPENAI_API_KEY, LLM_MODEL_NAME
from .utils import logger

class BibleGenerator:
    def __init__(self, api_key: str = OPENAI_API_KEY, model_name: str = LLM_MODEL_NAME):
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name

    def _build_prompt(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        # Sort by score just in case, though retrieval usually does it
        sorted_chunks = sorted(context_chunks, key=lambda x: x.get("score", 0), reverse=True)

        context_parts = []
        for i, chunk in enumerate(sorted_chunks):
            ref = chunk['metadata']['ref_en']
            text = chunk['display_text']
            score = chunk.get('score', 0)
            context_parts.append(f"[{i+1}] Source: {ref} (Score: {score:.4f})\nText: {text}")

        context_text = "\n\n".join(context_parts)

        prompt = f"""You are an expert biblical scholar and a helpful assistant.
Your goal is to answer questions about the Hebrew Bible (Tanakh) based ONLY on the provided context.

RULES:
1. Answer the question accurately using the provided context.
2. If the answer is not contained in the context, state clearly that you do not have enough information in the provided context to answer.
3. DO NOT use outside knowledge or hallucinate facts.
4. Always cite your sources by referencing the Book, Chapter, and Verse in Hebrew (e.g., תהילים נג:ו).
5. Provide the answer in the same language as the question (Hebrew or English).
6. When citing or referring to chapters and verses in Hebrew, use ONLY Hebrew letters WITHOUT any quotation marks (") or apostrophes ('). For example, use 'נג:ו' instead of 'נ"ג:ו' or 'נ'ג:ו' or '53:6'.
7. When quoting a full verse in Hebrew, always append the Hebrew 'Sof Pasuk' symbol (׃) to the end of the verse text (before the citation).

Context:
{context_text}

Question: {question}

Answer:"""
        return prompt

    def generate(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        if not context_chunks:
            return "אני מצטער, לא נמצא מידע רלוונטי בטקסט כדי לענות על השאלה הזו." if any('\u0590' <= c <= '\u05FF' for c in question) else "I'm sorry, no relevant context was found to answer this question."

        prompt = self._build_prompt(question, context_chunks)

        logger.info(f"Generating answer using {self.model_name}...")
        logger.debug(f"Prompt size: {len(prompt)} characters")

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful and precise biblical scholar."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0, # Deterministic answers
            )
            answer = response.choices[0].message.content
            return answer
        except Exception as e:
            logger.error(f"Error during LLM generation: {e}")
            return f"Error: {str(e)}"
