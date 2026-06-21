"""
BibleAgent — an OpenAI function-calling agent loop built ON TOP of the existing
RAG stack (VectorRetriever + GPT). It does NOT modify retrieval/generation logic;
it only wraps them as tools and lets the model decide which to use.

Design goals (final project):
 - Close the three documented weaknesses of the midterm (see report.md):
     1. Structural/metadata questions  -> `bible_structure` tool
     2. Single static retrieval (97% misses) -> agent self-correction (re-search)
     3. No multi-step reasoning -> tool-calling loop + conversational memory
 - Return a STRUCTURED, operational trace (which tool, args, result summary,
   confidence) for the Agent Trace Visualization in the UI. We never expose the
   model's internal chain-of-thought — only what it did.
"""

import json
from typing import Any, Dict, List, Optional

from .config import ALL_VERSES_JSONL, LLM_MODEL_NAME, OPENAI_API_KEY
from .constants import BIBLE_CATALOG, BOOK_MAPPING
from .utils import logger, Gematria

# How much conversation history to keep (last N messages). Keeps context tight
# and cost/latency reasonable. (Plan: 10-15.)
MAX_HISTORY_MESSAGES = 14

# Hard ceiling on tool-calling rounds to prevent infinite loops.
MAX_ITERATIONS = 5

# Hebrew explanations for each tool (surfaced in the UI trace).
TOOL_LABELS = {
    "search_tanakh": "חיפוש בתנ״ך",
    "lookup_reference": "שליפת מראה מקום",
    "bible_structure": "שאלת מבנה",
    "compare_retrieval_strategies": "השוואת אסטרטגיות",
}

FALLBACK_MESSAGE = (
    "לא נמצא מקור מספיק מהימן בתנ״ך כדי לענות על השאלה הזו."
)

SYSTEM_PROMPT = """You are "חברותא", an expert, careful study companion for the Hebrew Bible (Tanakh).
You answer questions by USING TOOLS — you never rely on outside knowledge or invent verses.

You have these tools:
- search_tanakh: semantic / lexical / hybrid search over the Tanakh verses. Use it for content questions ("who/what/where/when did...").
- lookup_reference: fetch the exact text of a specific Book Chapter:Verse (or a small range). Use it to verify or quote a verse precisely.
- bible_structure: answer STRUCTURAL questions about the Tanakh from its catalog (longest/shortest book, number of chapters in a book, order of books, number of books, total chapters). Use this — do NOT search verses — for "how many books / which book is longest / what is the order" style questions.
- compare_retrieval_strategies: run dense, lexical and hybrid retrieval on the same query and compare, when it is useful to understand which strategy fits.

RULES:
1. Decide which tool fits the question. Prefer bible_structure for structural questions.
2. If search results look irrelevant or low-scoring, REFORMULATE the query and search again (you may search a few times).
3. Ground every factual claim in tool results. Cite sources as Hebrew "Book Chapter:Verse" using ONLY Hebrew letters, WITHOUT any quotation marks (") or apostrophes (').
4. When quoting a full Hebrew verse, append the Sof Pasuk (׃) at the end of the quoted text.
5. Answer in the same language as the question (Hebrew or English).
6. If after searching you still cannot find a reliable source, say so clearly — respond with: "{fallback}". Do NOT fabricate.
""".format(fallback=FALLBACK_MESSAGE)


def _is_hebrew(text: str) -> bool:
    return any("֐" <= c <= "׿" for c in text)


class BibleAgent:
    def __init__(self, retriever, client=None):
        """
        retriever: an ALREADY-LOADED VectorRetriever (reused from BibleRAG —
                   we must not reload the embedding model or FAISS index).
        client:    an OpenAI client (reused from BibleGenerator). If None, one
                   is created from config.
        """
        self.retriever = retriever
        if client is None:
            import openai
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.client = client
        self.model_name = LLM_MODEL_NAME

        self._verses_by_key: Dict[str, Dict[str, Any]] = {}
        self._en_to_he: Dict[str, str] = {}
        self._build_lookup_maps()
        self.tools_schema = self._build_tools_schema()

    # ------------------------------------------------------------------ setup
    def _build_lookup_maps(self):
        """Build a (book, chapter, verse) -> verse dict map for lookup_reference."""
        for he, info in BOOK_MAPPING.items():
            self._en_to_he[info["en"].lower()] = he
        if not ALL_VERSES_JSONL.exists():
            logger.warning(f"{ALL_VERSES_JSONL} not found — lookup_reference disabled.")
            return
        with open(ALL_VERSES_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                v = json.loads(line)
                key = f"{v['book']}|{v['chapter']}|{v['verse']}"
                self._verses_by_key[key] = v
        logger.info(f"Agent lookup map: {len(self._verses_by_key)} verses indexed.")

    def _normalize_book(self, book: str) -> Optional[str]:
        if not book:
            return None
        book = book.strip()
        if book in BOOK_MAPPING:
            return book
        return self._en_to_he.get(book.lower())

    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_tanakh",
                    "description": "Search Tanakh verses semantically/lexically/hybrid. Returns top matching verses with references and scores.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query, ideally in Hebrew."},
                            "strategy": {
                                "type": "string",
                                "enum": ["hybrid", "dense_only", "lexical_only"],
                                "description": "Retrieval strategy. Default hybrid.",
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lookup_reference",
                    "description": "Fetch the exact text of a specific verse or small range by Book Chapter:Verse.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "book": {"type": "string", "description": "Book name in Hebrew (e.g. בראשית) or English."},
                            "chapter": {"type": "integer"},
                            "verse_start": {"type": "integer"},
                            "verse_end": {"type": "integer", "description": "Optional end of range."},
                        },
                        "required": ["book", "chapter", "verse_start"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "bible_structure",
                    "description": "Answer structural questions about the Tanakh from its catalog (no verse search).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_type": {
                                "type": "string",
                                "enum": [
                                    "longest_book",
                                    "shortest_book",
                                    "book_chapter_count",
                                    "book_order",
                                    "book_count",
                                    "total_chapters",
                                ],
                            },
                            "book": {"type": "string", "description": "Book name (needed for book_chapter_count / book_order)."},
                        },
                        "required": ["query_type"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_retrieval_strategies",
                    "description": "Run dense, lexical and hybrid retrieval on the same query and compare their top results.",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                },
            },
        ]

    # ------------------------------------------------------------------ tools
    def _tool_search_tanakh(self, query: str, strategy: str = "hybrid") -> Dict[str, Any]:
        if strategy not in ("hybrid", "dense_only", "lexical_only"):
            strategy = "hybrid"
        chunks = self.retriever.retrieve(query, top_k=5, strategy=strategy)
        results = [
            {
                "ref": c["metadata"].get("ref"),
                "ref_en": c["metadata"].get("ref_en"),
                "text": c.get("display_text", ""),
                "score": round(float(c.get("score", 0)), 4),
            }
            for c in chunks
        ]
        top = results[0] if results else None
        return {
            "strategy": strategy,
            "count": len(results),
            "top_ref": top["ref"] if top else None,
            "top_score": top["score"] if top else 0.0,
            "results": results,
        }

    def _tool_lookup_reference(self, book: str, chapter: int, verse_start: int, verse_end: Optional[int] = None) -> Dict[str, Any]:
        he_book = self._normalize_book(book)
        if not he_book:
            return {"found": False, "error": f"Unknown book: {book}"}
        end = verse_end or verse_start
        verses = []
        for v in range(int(verse_start), int(end) + 1):
            entry = self._verses_by_key.get(f"{he_book}|{int(chapter)}|{v}")
            if entry:
                verses.append({"ref": entry["ref"], "ref_en": entry["ref_en"], "text": entry["text_original"]})
        if not verses:
            return {"found": False, "error": f"No verse at {he_book} {chapter}:{verse_start}"}
        return {"found": True, "book": he_book, "chapter": int(chapter), "verses": verses}

    def _tool_bible_structure(self, query_type: str, book: Optional[str] = None) -> Dict[str, Any]:
        catalog = BIBLE_CATALOG
        if query_type == "book_count":
            return {"answer": len(catalog), "detail": "מספר הספרים בתנ״ך"}
        if query_type == "total_chapters":
            total = sum(b["number_of_chapters"] for b in catalog)
            return {"answer": total, "detail": "סך כל הפרקים בתנ״ך"}
        if query_type == "longest_book":
            b = max(catalog, key=lambda x: x["number_of_chapters"])
            return {"book": b["hebrew"], "book_en": b["english"], "chapters": b["number_of_chapters"]}
        if query_type == "shortest_book":
            b = min(catalog, key=lambda x: x["number_of_chapters"])
            return {"book": b["hebrew"], "book_en": b["english"], "chapters": b["number_of_chapters"]}
        if query_type == "book_chapter_count":
            he = self._normalize_book(book or "")
            info = BOOK_MAPPING.get(he) if he else None
            if not info:
                return {"error": f"Unknown book: {book}"}
            return {"book": he, "book_en": info["en"], "chapters": info["number_of_chapters"]}
        if query_type == "book_order":
            he = self._normalize_book(book or "")
            info = BOOK_MAPPING.get(he) if he else None
            if he and info:
                return {"book": he, "position": info["index"], "of": len(catalog)}
            return {"order": [b["hebrew"] for b in catalog]}
        return {"error": f"Unknown query_type: {query_type}"}

    def _tool_compare_retrieval_strategies(self, query: str) -> Dict[str, Any]:
        comparison = {}
        for strat in ("dense_only", "lexical_only", "hybrid"):
            chunks = self.retriever.retrieve(query, top_k=3, strategy=strat)
            comparison[strat] = [
                {"ref": c["metadata"].get("ref"), "score": round(float(c.get("score", 0)), 4)}
                for c in chunks
            ]
        return {"query": query, "comparison": comparison}

    def _dispatch(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "search_tanakh":
            return self._tool_search_tanakh(**args)
        if name == "lookup_reference":
            return self._tool_lookup_reference(**args)
        if name == "bible_structure":
            return self._tool_bible_structure(**args)
        if name == "compare_retrieval_strategies":
            return self._tool_compare_retrieval_strategies(**args)
        return {"error": f"Unknown tool: {name}"}

    # ------------------------------------------------------ trace summaries
    def _summarize(self, name: str, result: Dict[str, Any]) -> Dict[str, str]:
        """Build an operational summary + confidence for a tool result."""
        if name == "search_tanakh":
            if not result.get("count"):
                return {"summary": "לא נמצאו מקורות.", "confidence": "low"}
            score = result.get("top_score", 0.0)
            conf = "high" if score >= 0.6 else "medium" if score >= 0.3 else "low"
            return {
                "summary": f"נמצאו {result['count']} מקורות (אסטרטגיה: {result['strategy']}). מוביל: {result['top_ref']} (score {score:.2f}).",
                "confidence": conf,
            }
        if name == "lookup_reference":
            if not result.get("found"):
                return {"summary": result.get("error", "לא נמצא הפסוק."), "confidence": "low"}
            refs = ", ".join(v["ref"] for v in result["verses"])
            return {"summary": f"נשלפו {len(result['verses'])} פסוקים: {refs}.", "confidence": "high"}
        if name == "bible_structure":
            if result.get("error"):
                return {"summary": result["error"], "confidence": "low"}
            if "chapters" in result:
                return {"summary": f"{result.get('book', '')}: {result['chapters']} פרקים.", "confidence": "high"}
            if "answer" in result:
                return {"summary": f"{result.get('detail', '')}: {result['answer']}.", "confidence": "high"}
            if "position" in result:
                return {"summary": f"{result['book']} — ספר מספר {result['position']} מתוך {result['of']}.", "confidence": "high"}
            return {"summary": "סדר ספרי התנ״ך הוחזר.", "confidence": "high"}
        if name == "compare_retrieval_strategies":
            tops = {s: (lst[0]["ref"] if lst else "—") for s, lst in result.get("comparison", {}).items()}
            return {
                "summary": "מוביל לכל אסטרטגיה — " + ", ".join(f"{s}: {r}" for s, r in tops.items()) + ".",
                "confidence": "medium",
            }
        return {"summary": "", "confidence": "medium"}

    # ------------------------------------------------------------------ loop
    def chat(self, messages: List[Dict[str, str]], strategy_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        messages: conversation history [{role, content}, ...].
        Returns {answer, sources, trace}.
        """
        # Keep only the last N turns of plain chat history.
        history = [m for m in messages if m.get("role") in ("user", "assistant")][-MAX_HISTORY_MESSAGES:]
        last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")

        convo: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        trace: List[Dict[str, Any]] = []
        collected_sources: List[str] = []
        step = 0

        for _ in range(MAX_ITERATIONS):
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=convo,
                tools=self.tools_schema,
                tool_choice="auto",
                temperature=0,
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                # Final answer from the model.
                answer = msg.content or ""
                is_fallback = (FALLBACK_MESSAGE[:20] in answer) or (not collected_sources and "לא נמצא" in answer)
                step += 1
                trace.append({
                    "step": step,
                    "type": "fallback" if is_fallback else "final_answer",
                    "tool": None,
                    "label": "תשובה סופית" if not is_fallback else "אין מקור מהימן",
                    "args": None,
                    "summary": "התשובה נבנתה על בסיס המקורות שנשלפו." if not is_fallback else "הסוכן לא מצא מקור מספיק מהימן.",
                    "confidence": "high" if not is_fallback else "low",
                })
                return {"answer": answer, "sources": _dedupe(collected_sources), "trace": trace}

            # Append the assistant turn that requested tools.
            convo.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = self._dispatch(name, args)

                # Collect sources for the response.
                if name == "search_tanakh":
                    collected_sources.extend(r["ref_en"] for r in result.get("results", []) if r.get("ref_en"))
                elif name == "lookup_reference" and result.get("found"):
                    collected_sources.extend(v["ref_en"] for v in result["verses"])

                meta = self._summarize(name, result)
                step += 1
                trace.append({
                    "step": step,
                    "type": "tool_call",
                    "tool": name,
                    "label": TOOL_LABELS.get(name, name),
                    "args": args,
                    "summary": meta["summary"],
                    "confidence": meta["confidence"],
                })

                convo.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        # Hit the iteration ceiling — force a final summarization without tools.
        convo.append({
            "role": "system",
            "content": "Reached the tool-call limit. Now answer the user's question using ONLY the information gathered above. If it is insufficient, reply with the fallback message.",
        })
        final = self.client.chat.completions.create(
            model=self.model_name,
            messages=convo,
            temperature=0,
        )
        answer = final.choices[0].message.content or FALLBACK_MESSAGE
        is_fallback = (FALLBACK_MESSAGE[:20] in answer) or not collected_sources
        step += 1
        trace.append({
            "step": step,
            "type": "fallback" if is_fallback else "final_answer",
            "tool": None,
            "label": "תשובה סופית (לאחר מגבלת צעדים)" if not is_fallback else "אין מקור מהימן",
            "args": None,
            "summary": "התשובה נבנתה לאחר שהסוכן הגיע למספר הצעדים המרבי." if not is_fallback else "הסוכן לא מצא מקור מספיק מהימן.",
            "confidence": "medium" if not is_fallback else "low",
        })
        return {"answer": answer, "sources": _dedupe(collected_sources), "trace": trace}


def _dedupe(items: List[str]) -> List[str]:
    seen, out = set(), []
    for it in items:
        if it and it not in seen:
            seen.add(it)
            out.append(it)
    return out
