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
import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional

from .config import ALL_VERSES_JSONL, LLM_MODEL_NAME, OPENAI_API_KEY
from .constants import BIBLE_CATALOG, BOOK_MAPPING
from .dicta import search_number as dicta_search_number
from .utils import logger, Gematria

# How much conversation history to keep (last N messages). Keeps context tight
# and cost/latency reasonable. (Plan: 10-15.)
MAX_HISTORY_MESSAGES = 14

# Hard ceiling on tool-calling rounds to prevent infinite loops. Set high enough
# to let the agent binary-search (e.g. for the longest verse by word count).
MAX_ITERATIONS = 12

# Hebrew explanations for each tool (surfaced in the UI trace).
TOOL_LABELS = {
    "search_tanakh": "חיפוש בתנ״ך",
    "lookup_reference": "שליפת מראה מקום",
    "bible_structure": "מבנה וסטטיסטיקה",
    "compare_retrieval_strategies": "השוואת אסטרטגיות",
    "search_number": "חיפוש מספר (Dicta)",
    "find_longest_verse": "חיפוש בינארי",
}

FALLBACK_MESSAGE = (
    "לא נמצא מקור מספיק מהימן בתנ״ך כדי לענות על השאלה הזו."
)

# Appended to answers that came from the model's general knowledge (no tool used),
# to stay transparent and point the user elsewhere for a fuller explanation.
GENERAL_KNOWLEDGE_NOTE = (
    "\n\n(זו אינה שאלה על טקסט התנ״ך, אז השבתי בקצרה. "
    "להרחבה מלאה מומלץ לפנות לכלי AI כללי כמו ChatGPT.)"
)

SYSTEM_PROMPT = """You are "חברותא", an expert, careful study companion for the Hebrew Bible (Tanakh).
You answer questions by USING TOOLS — you never rely on outside knowledge or invent verses.

You have these tools:
- search_tanakh: semantic / lexical / hybrid search over the Tanakh verses. Use it for content questions ("who/what/where/when did...").
- lookup_reference: fetch the exact text of a specific Book Chapter:Verse (or a small range). Use it to verify or quote a verse precisely.
- bible_structure: answer STRUCTURAL and corpus-statistic questions about the Tanakh (longest/shortest book, number of chapters in a book, order of books, number of books, total chapters, total number of verses/words/letters, the most frequent word, the most frequent letter, how many times a given word appears (word_frequency), the longest WORD, the word with the highest GEMATRIA value, the longest VERSE by word count, and example verses with an exact number of words). Use this — do NOT search verses — for "how many books / how many verses / how many words / how many letters / what is the most common word / which letter is most frequent / how many times does the word X appear / what is the middle letter (or word/verse) of the Torah / which book is longest / what is the order / what is the longest word / which word has the highest gematria / what is the longest verse / give me a verse with N words" style questions.
- compare_retrieval_strategies: run dense, lexical and hybrid retrieval on the same query and compare, when it is useful to understand which strategy fits.
- find_longest_verse: find the verse with the most words via a binary search. Use it for "what is the longest verse in the Tanakh" questions.

RULES:
1. Decide which tool fits the question. Prefer bible_structure for structural questions.
2. If search results look irrelevant or low-scoring, REFORMULATE the query and search again (you may search a few times).
3. Ground every factual claim in tool results. Cite sources as Hebrew "Book Chapter:Verse" using ONLY Hebrew letters, WITHOUT any quotation marks (") or apostrophes (').
4. When quoting a full Hebrew verse, append the Sof Pasuk (׃) at the end of the quoted text.
5. Answer in the same language as the question (Hebrew or English).
6. If after searching you still cannot find a reliable source, say so clearly — respond with: "{fallback}". Do NOT fabricate. BUT: when a deterministic tool (bible_structure) gives a definitive result — including that ZERO verses match (e.g. there is no verse with exactly 2 words) — that IS the grounded answer. State it plainly (e.g. "אין בתנ״ך פסוק עם 2 מילים בלבד") and do NOT add the "{fallback}" sentence.
7. If the question is NOT about the Tanakh text (a general concept, your capabilities, or off-topic small-talk), answer in AT MOST 1–2 short sentences. Do NOT write a long explanation or essay.
8. For ANY question about verses with a specific number of words — including whether such a verse exists — you MUST call bible_structure(verse_by_word_count) and answer from its result. Even if you are CERTAIN you know the answer (e.g. that no verse has only 2 words), you must still call the tool to confirm before answering. Never answer such a question from memory.
9. To find the verse with the MOST words (the longest verse by word count), call find_longest_verse once. It performs the search and returns the answer; report the resulting verse.
""".format(fallback=FALLBACK_MESSAGE)


def _is_hebrew(text: str) -> bool:
    return any("֐" <= c <= "׿" for c in text)


def _hebrew_letter_count(token: str) -> int:
    return sum(1 for ch in token if "א" <= ch <= "ת")


# Standard gematria (mispar hechrachi); final letters equal their regular form.
_GEMATRIA = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ך": 20, "ל": 30, "מ": 40, "ם": 40, "נ": 50, "ן": 50,
    "ס": 60, "ע": 70, "פ": 80, "ף": 80, "צ": 90, "ץ": 90,
    "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}


def _gematria_value(token: str) -> int:
    return sum(_GEMATRIA.get(ch, 0) for ch in token)


def _clean_display_word(word: str) -> str:
    # Drop surrounding punctuation (parens/brackets for qere-ketiv, sof pasuk, maqaf).
    return word.strip("()[]׃־ ").strip()


def _resolve_keri_ketiv(text: str) -> str:
    """Collapse a ketiv/qere pair to ONE word: drop the bare ketiv (no niqqud) and
    keep the qere (the parenthesized, vocalized form), unwrapped — e.g.
    'ויצוהו (וַיְצַוֶּה) המלך' -> 'וַיְצַוֶּה המלך'. The qere may itself be several
    words (e.g. 'בגד (בָּא גָד)' -> 'בָּא גָד'). Used for verse word counting."""
    return re.sub(r"[^\s־]+\s+\(([^)]+)\)", r"\1", text)


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
        """Build a (book, chapter, verse) -> verse dict map for lookup_reference,
        and — in the same single pass — compute corpus statistics once (longest
        word, highest-gematria word), cached and never recomputed per request."""
        for he, info in BOOK_MAPPING.items():
            self._en_to_he[info["en"].lower()] = he
        self._longest_word: Optional[Dict[str, Any]] = None
        self._highest_gematria: Optional[Dict[str, Any]] = None
        self._verses_by_word_count: Dict[int, List[str]] = {}  # word count -> verse keys (canonical order)
        self._longest_verse: Optional[Dict[str, Any]] = None
        self._torah_middle: Optional[Dict[str, Any]] = None  # lazy-computed on first request
        self._word_freq: Counter = Counter()    # normalized word (letters only) -> occurrences
        self._letter_freq: Counter = Counter()  # Hebrew letter -> occurrences
        if not ALL_VERSES_JSONL.exists():
            logger.warning(f"{ALL_VERSES_JSONL} not found — lookup_reference disabled.")
            return
        max_len = 0
        longest: Dict[str, str] = {}  # display word (niqqud) -> first ref at max_len
        max_gem = 0
        highest_gem: Dict[str, tuple] = {}  # plain word -> (display niqqud, first ref) at max_gem
        with open(ALL_VERSES_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                v = json.loads(line)
                key = f"{v['book']}|{v['chapter']}|{v['verse']}"
                self._verses_by_key[key] = v

                # Resolve ketiv/qere once; reuse for the word-count index AND the
                # word/letter frequency counters (so all counts are consistent).
                resolved = _resolve_keri_ketiv(v["text_plain"])
                resolved_tokens = resolved.split()
                # Index verses by word count (maqaf (־)/paseq (׀) are spaces in
                # text_plain, so maqaf-joined words count SEPARATELY).
                self._verses_by_word_count.setdefault(len(resolved_tokens), []).append(key)
                for tok in resolved_tokens:
                    w = "".join(ch for ch in tok if "א" <= ch <= "ת")  # letters only (drop ׃ etc.)
                    if w:
                        self._word_freq[w] += 1
                for ch in resolved:
                    if "א" <= ch <= "ת":
                        self._letter_freq[ch] += 1

                # Longest-word scan (same pass): count Hebrew letters per plain token,
                # keep the parallel niqqud form for display.
                plain = v["text_plain"].split()
                niq = v["text_with_niqqud"].split()
                if len(plain) != len(niq):
                    continue
                for pw, nw in zip(plain, niq):
                    disp = None
                    # Longest word — by Hebrew-letter count.
                    L = _hebrew_letter_count(pw)
                    if L >= max_len and L > 0:
                        disp = _clean_display_word(nw)
                        if L > max_len:
                            max_len, longest = L, {disp: v["ref"]}
                        elif disp not in longest:
                            longest[disp] = v["ref"]
                    # Highest gematria — by summed letter value (dedupe by consonants).
                    g = _gematria_value(pw)
                    if g >= max_gem and g > 0:
                        if disp is None:
                            disp = _clean_display_word(nw)
                        if g > max_gem:
                            max_gem, highest_gem = g, {pw: (disp, v["ref"])}
                        elif pw not in highest_gem:
                            highest_gem[pw] = (disp, v["ref"])

        if max_len > 0:
            self._longest_word = {
                "length": max_len,
                "words": [{"word": w, "ref": r} for w, r in list(longest.items())[:5]],
            }
        if max_gem > 0:
            self._highest_gematria = {
                "value": max_gem,
                "words": [{"word": d, "ref": r} for (d, r) in list(highest_gem.values())[:5]],
            }
        # Longest verse by word count — deterministic (reliable, unlike an LLM
        # binary search). Same shape as verse_by_word_count so it reuses downstream.
        if self._verses_by_word_count:
            mx = max(self._verses_by_word_count)
            keys = self._verses_by_word_count[mx]
            verses = []
            for k in keys[:3]:
                e = self._verses_by_key.get(k)
                if e:
                    verses.append({"ref": e["ref"], "ref_en": e["ref_en"],
                                   "text": _resolve_keri_ketiv(e["text_original"])})
            self._longest_verse = {"word_count": mx, "total": len(keys), "verses": verses}
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
                    "description": "Answer structural and corpus-statistic questions about the Tanakh deterministically (no verse search): longest/shortest book, chapters in a book, book order, number of books, total chapters, total number of verses, total number of words, total number of letters, the most frequent word, the most frequent letter, how many times a given word appears, the middle of the Torah (middle letter/word/verse — query_type torah_middle), the longest word, the word with the highest gematria value, and example verses that contain an exact number of words. (For the longest VERSE by word count, use the find_longest_verse tool instead.)",
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
                                    "total_verses",
                                    "total_words",
                                    "total_letters",
                                    "most_frequent_word",
                                    "most_frequent_letter",
                                    "word_frequency",
                                    "torah_middle",
                                    "longest_word",
                                    "highest_gematria",
                                    "verse_by_word_count",
                                ],
                            },
                            "book": {"type": "string", "description": "Book name (needed for book_chapter_count / book_order)."},
                            "word_count": {"type": "integer", "description": "Exact number of words a verse should contain (for verse_by_word_count)."},
                            "word": {"type": "string", "description": "The word to count (for word_frequency), in Hebrew."},
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
            {
                "type": "function",
                "function": {
                    "name": "search_number",
                    "description": "Find verses that contain a NUMBER (spelled out in Hebrew words, e.g. 26 -> 'עשרים ושש') via Dicta's Tanakh search. Use for queries about a specific number.",
                    "parameters": {
                        "type": "object",
                        "properties": {"number": {"type": "string", "description": "The number to search for, digits only."}},
                        "required": ["number"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "find_longest_verse",
                    "description": "Find the verse with the MOST words by running a binary search over word counts (you do NOT know the maximum in advance — this tool searches for it). Use for 'what is the longest verse in the Tanakh' questions. Returns the search probes and the answer.",
                    "parameters": {"type": "object", "properties": {}},
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

    def _tool_bible_structure(self, query_type: str, book: Optional[str] = None,
                              word_count: Optional[int] = None, word: Optional[str] = None) -> Dict[str, Any]:
        catalog = BIBLE_CATALOG
        if query_type == "book_count":
            return {"answer": len(catalog), "detail": "מספר הספרים בתנ״ך"}
        if query_type == "total_chapters":
            total = sum(b["number_of_chapters"] for b in catalog)
            return {"answer": total, "detail": "סך כל הפרקים בתנ״ך"}
        if query_type == "total_verses":
            n = len(getattr(self, "_verses_by_key", {}))
            if not n:
                return {"error": "נתוני הפסוקים אינם זמינים לספירת הפסוקים."}
            return {"answer": n, "detail": "מספר הפסוקים בתנ״ך"}
        if query_type == "total_words":
            wf = getattr(self, "_word_freq", None)
            if not wf:
                return {"error": "נתוני הפסוקים אינם זמינים לספירת המילים."}
            return {"answer": sum(wf.values()), "detail": "סך כל המילים בתנ״ך"}
        if query_type == "total_letters":
            lf = getattr(self, "_letter_freq", None)
            if not lf:
                return {"error": "נתוני הפסוקים אינם זמינים לספירת האותיות."}
            return {"answer": sum(lf.values()), "detail": "סך כל האותיות בתנ״ך"}
        if query_type == "most_frequent_word":
            wf = getattr(self, "_word_freq", None)
            if not wf:
                return {"error": "נתוני הפסוקים אינם זמינים לחישוב תדירות המילים."}
            top = wf.most_common(3)
            return {"word": top[0][0], "count": top[0][1],
                    "top": [{"word": w, "count": c} for w, c in top]}
        if query_type == "most_frequent_letter":
            lf = getattr(self, "_letter_freq", None)
            if not lf:
                return {"error": "נתוני הפסוקים אינם זמינים לחישוב תדירות האותיות."}
            letter, count = lf.most_common(1)[0]
            return {"letter": letter, "count": count}
        if query_type == "word_frequency":
            wf = getattr(self, "_word_freq", None)
            if wf is None:
                return {"error": "נתוני הפסוקים אינם זמינים לחישוב תדירות המילים."}
            w = "".join(ch for ch in (word or "") if "א" <= ch <= "ת")  # normalize to letters
            if not w:
                return {"error": "יש לציין מילה בעברית."}
            return {"word": w, "count": wf.get(w, 0), "queried": True}
        if query_type == "torah_middle":
            return self._compute_torah_middle()
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
        if query_type == "longest_word":
            if not getattr(self, "_longest_word", None):
                return {"error": "נתוני הפסוקים אינם זמינים לחישוב המילה הארוכה ביותר."}
            return dict(self._longest_word)
        if query_type == "highest_gematria":
            if not getattr(self, "_highest_gematria", None):
                return {"error": "נתוני הפסוקים אינם זמינים לחישוב הערך הגימטרי הגבוה ביותר."}
            return dict(self._highest_gematria)
        if query_type == "verse_by_word_count":
            if word_count is None:
                return {"error": "יש לציין מספר מילים (word_count)."}
            n = int(word_count)
            by_count = getattr(self, "_verses_by_word_count", {})
            keys = by_count.get(n, [])
            # Monotonic signal for binary-searching the longest verse: how many
            # verses have AT LEAST n words (>0 ⇒ the max is ≥ n; 0 ⇒ the max is < n).
            at_least = sum(len(ks) for m, ks in by_count.items() if m >= n)
            examples = []
            for k in keys[:3]:
                e = self._verses_by_key.get(k)
                if e:
                    # Resolve ketiv/qere so the displayed (and numbered) words match
                    # the count: show the qere (niqqud) form, drop the bare ketiv.
                    examples.append({"ref": e["ref"], "ref_en": e["ref_en"],
                                     "text": _resolve_keri_ketiv(e["text_original"])})
            return {"word_count": n, "total": len(keys), "at_least": at_least, "verses": examples}
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

    def _tool_search_number(self, number: str, size: int = 5) -> Dict[str, Any]:
        return dicta_search_number(number, size=size)

    def _compute_torah_middle(self) -> Dict[str, Any]:
        """The middle letter / word / verse of the Torah (first 5 books), computed
        deterministically over the read (qere) text with ketiv/qere collapsed.
        Cached after first use. NOTE: a literal count differs from the traditional
        Masoretic markers (ו of גחון / דרש דרש) due to plene/defective spelling."""
        if self._torah_middle is not None:
            return self._torah_middle
        if not self._verses_by_key:
            return {"error": "נתוני הפסוקים אינם זמינים לחישוב אמצע התורה."}

        torah_books = {b["hebrew"] for b in BIBLE_CATALOG[:5]}  # בראשית..דברים
        rows = [v for v in self._verses_by_key.values() if v["book"] in torah_books]
        rows.sort(key=lambda v: (BOOK_MAPPING[v["book"]]["index"], v["chapter"], v["verse"]))

        verse_refs: List[str] = []
        words: List[tuple] = []    # (display_word, ref)
        letters: List[tuple] = []  # (letter, display_word, ref)
        for v in rows:
            verse_refs.append(v["ref"])
            pt = _resolve_keri_ketiv(v["text_plain"]).split()
            nt = _resolve_keri_ketiv(v["text_with_niqqud"]).split()
            if len(pt) != len(nt):
                nt = pt
            for pw, nw in zip(pt, nt):
                disp = _clean_display_word(nw)
                words.append((disp, v["ref"]))
                for ch in pw:
                    if "א" <= ch <= "ת":
                        letters.append((ch, disp, v["ref"]))

        def middles(seq: list) -> list:
            n = len(seq)
            return [seq[n // 2]] if n % 2 else [seq[n // 2 - 1], seq[n // 2]]

        self._torah_middle = {
            "torah_middle": True,
            "verses": [{"ref": r} for r in middles(verse_refs)],
            "words": [{"word": w, "ref": r} for (w, r) in middles(words)],
            "letters": [{"letter": l, "word": w, "ref": r} for (l, w, r) in middles(letters)],
            "counts": {"verses": len(verse_refs), "words": len(words), "letters": len(letters)},
            "note": ("ספירה ממוחשבת מדויקת על הטקסט. המסורת המקובלת מציינת את האות ו' של "
                     "'גָּחוֹן' (ויקרא יא:מב) כאמצעית ואת 'דָּרֹשׁ דָּרַשׁ' (ויקרא י:טז) כמילים "
                     "האמצעיות; ההבדל נובע מהבדלי כתיב מלא/חסר בספירה המסורתית."),
        }
        return self._torah_middle

    def _tool_find_longest_verse(self) -> Dict[str, Any]:
        """Find the longest verse by word count via a DETERMINISTIC binary search.
        Returns the probe sequence (for a step-by-step trace) plus the answer.
        The answer comes from the precomputed _longest_verse, so it's always correct;
        the probes are a real binary search that converges to the same number."""
        by = getattr(self, "_verses_by_word_count", {})
        if not by or not getattr(self, "_longest_verse", None):
            return {"error": "נתוני הפסוקים אינם זמינים לחישוב הפסוק הארוך ביותר."}

        def at_least(n: int) -> int:
            return sum(len(ks) for m, ks in by.items() if m >= n)

        probes: List[Dict[str, int]] = []
        seen = set()

        def probe(n: int) -> int:
            al = at_least(n)
            if n not in seen:
                seen.add(n)
                probes.append({"word_count": n, "at_least": al})
            return al

        # Start high (100) and double until we have an upper bound with no verses.
        hi = 100
        while probe(hi) > 0:
            hi *= 2
        # Binary search for the largest N with at_least(N) > 0.
        lo_b, hi_b, ans = 1, hi, 1
        while lo_b <= hi_b:
            mid = (lo_b + hi_b) // 2
            if probe(mid) > 0:
                ans = mid
                lo_b = mid + 1
            else:
                hi_b = mid - 1

        result = dict(self._longest_verse)  # {word_count, total, verses}
        result["probes"] = probes
        result["found"] = ans
        return result

    def _dispatch(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "search_tanakh":
            return self._tool_search_tanakh(**args)
        if name == "lookup_reference":
            return self._tool_lookup_reference(**args)
        if name == "bible_structure":
            return self._tool_bible_structure(**args)
        if name == "compare_retrieval_strategies":
            return self._tool_compare_retrieval_strategies(**args)
        if name == "search_number":
            return self._tool_search_number(**args)
        if name == "find_longest_verse":
            return self._tool_find_longest_verse(**args)
        return {"error": f"Unknown tool: {name}"}

    # ------------------------------------------------------ trace summaries
    def _summarize(self, name: str, result: Dict[str, Any]) -> Dict[str, str]:
        """Build an operational summary + confidence for a tool result."""
        if name == "search_tanakh":
            if not result.get("count"):
                return {"summary": "לא נמצאו מקורות.", "confidence": "low"}
            score = result.get("top_score", 0.0)
            conf = "high" if score >= 0.6 else "medium" if score >= 0.3 else "low"
            found = "נמצא מקור אחד" if result["count"] == 1 else f"נמצאו {result['count']} מקורות"
            return {
                "summary": f"{found} (אסטרטגיה: {result['strategy']}). מוביל: {result['top_ref']} (score {score:.2f}).",
                "confidence": conf,
            }
        if name == "lookup_reference":
            if not result.get("found"):
                return {"summary": result.get("error", "לא נמצא הפסוק."), "confidence": "low"}
            refs = ", ".join(v["ref"] for v in result["verses"])
            n = len(result["verses"])
            pulled = "נשלף פסוק אחד" if n == 1 else f"נשלפו {n} פסוקים"
            return {"summary": f"{pulled}: {refs}.", "confidence": "high"}
        if name == "bible_structure":
            if result.get("error"):
                return {"summary": result["error"], "confidence": "low"}
            if "length" in result:  # longest_word
                k = len(result.get("words", []))
                cnt = "מילה אחת" if k == 1 else f"{k} מילים"
                return {"summary": f"המילה הארוכה ביותר: {result['length']} אותיות ({cnt}).", "confidence": "high"}
            if "value" in result:  # highest_gematria
                k = len(result.get("words", []))
                cnt = "מילה אחת" if k == 1 else f"{k} מילים"
                return {"summary": f"הערך הגימטרי הגבוה ביותר: {result['value']} ({cnt}).", "confidence": "high"}
            if result.get("torah_middle"):  # middle of the Torah
                ltr = "/".join(x["letter"] for x in result.get("letters", []))
                lref = result["letters"][0]["ref"] if result.get("letters") else "—"
                wlist = "/".join(x["word"] for x in result.get("words", []))
                vlist = "–".join(x["ref"] for x in result.get("verses", []))
                return {"summary": f"אמצע התורה — אות: {ltr} ({lref}); מילים: {wlist}; פסוקים: {vlist}.",
                        "confidence": "high"}
            if "letter" in result:  # most_frequent_letter
                return {"summary": f"האות הנפוצה ביותר: '{result['letter']}' ({result['count']} פעמים).", "confidence": "high"}
            if "word" in result and "count" in result:  # most_frequent_word / word_frequency
                c = result["count"]
                times = "פעם אחת" if c == 1 else f"{c} פעמים"
                if result.get("queried"):
                    if c == 0:
                        return {"summary": f"המילה '{result['word']}' (בצורתה המדויקת) אינה מופיעה בתנ״ך.", "confidence": "medium"}
                    return {"summary": f"המילה '{result['word']}' מופיעה {times}.", "confidence": "high"}
                return {"summary": f"המילה הנפוצה ביותר: '{result['word']}' ({times}).", "confidence": "high"}
            if "word_count" in result:  # verse_by_word_count
                n = result["word_count"]
                total = result.get("total", 0)
                if total == 0:
                    if result.get("at_least", 0) > 0:
                        return {"summary": f"אין פסוק עם בדיוק {n} מילים, אך קיימים פסוקים ארוכים יותר.", "confidence": "medium"}
                    return {"summary": f"אין פסוק עם {n} מילים או יותר.", "confidence": "medium"}
                ex = result["verses"][0]["ref"] if result.get("verses") else "—"
                found = "נמצא פסוק אחד" if total == 1 else f"נמצאו {total} פסוקים"
                return {"summary": f"{found} עם {n} מילים. דוגמה: {ex}.", "confidence": "high"}
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
        if name == "search_number":
            if result.get("error") or not result.get("total"):
                return {"summary": f"Dicta: לא נמצאו פסוקים עם המספר {result.get('number', '')}.", "confidence": "low"}
            if result["total"] == 1:
                return {"summary": f"נמצא פסוק אחד עם המספר {result['number']}.", "confidence": "high"}
            top = result["results"][0]["ref"] if result.get("results") else "—"
            return {"summary": f"Dicta: נמצאו {result['total']} פסוקים עם המספר {result['number']}. מוביל: {top}.", "confidence": "high"}
        return {"summary": "", "confidence": "medium"}

    # ----------------------------------------------------- number short-circuit
    def _number_shortcircuit(self, number: str, size: int = 5) -> Dict[str, Any]:
        """Pure-number input -> Dicta number search, answered deterministically (no LLM)."""
        result = self._tool_search_number(number, size=size)
        meta = self._summarize("search_number", result)
        total = result.get("total", 0)
        results = result.get("results", [])

        if result.get("error") or total == 0:
            answer = f"לא נמצאו פסוקים בתנ״ך שבהם מופיע המספר {number} (בכתיב מילולי)."
            trace = [
                {"step": 1, "type": "tool_call", "tool": "search_number", "label": TOOL_LABELS["search_number"],
                 "args": {"number": number}, "summary": meta["summary"], "confidence": "low"},
                {"step": 2, "type": "fallback", "tool": None, "label": "אין תוצאה",
                 "args": None, "summary": "חיפוש המספר ב-Dicta לא החזיר פסוקים.", "confidence": "low"},
            ]
            return {"answer": answer, "sources": [], "trace": trace}

        # Use Dicta's highlighted verse (keeps <b> around the number words) when present.
        lines = "\n".join(f"• {r['ref']}: {r.get('highlight') or r['text']}" for r in results)
        if total == 1:
            header = (f"נמצא פסוק אחד בתנ״ך שבו מופיע המספר {number} (בכתיב מילולי). "
                      f"הנה הוא (מקור: Dicta):")
        else:
            header = (f"נמצאו {total} פסוקים בתנ״ך שבהם מופיע המספר {number} (בכתיב מילולי). "
                      f"הנה {len(results)} הראשונים (מקור: Dicta):")
        answer = f"{header}\n{lines}"
        trace = [
            {"step": 1, "type": "tool_call", "tool": "search_number", "label": TOOL_LABELS["search_number"],
             "args": {"number": number}, "summary": meta["summary"], "confidence": "high"},
            {"step": 2, "type": "final_answer", "tool": None, "label": "תשובה סופית",
             "args": None, "summary": "התשובה נבנתה ישירות מתוצאות Dicta (ללא LLM).", "confidence": "high"},
        ]
        return {"answer": answer, "sources": [r["ref"] for r in results], "trace": trace}

    # ------------------------------------------------------------------ loop
    def chat(self, messages: List[Dict[str, str]], strategy_hint: Optional[str] = None) -> Dict[str, Any]:
        """Run the agent and return the full {answer, sources, trace, verses}.
        Implemented by draining stream() so behavior matches the streaming path."""
        trace: List[Dict[str, Any]] = []
        done: Dict[str, Any] = {"answer": "", "sources": [], "verses": []}
        for ev in self.stream(messages):
            if ev["type"] == "step":
                trace.append(ev["step"])
            elif ev["type"] == "done":
                done = ev
        return {"answer": done["answer"], "sources": done["sources"], "trace": trace, "verses": done.get("verses", [])}

    def stream(self, messages: List[Dict[str, str]], step_delay: float = 0.0):
        """Generator that yields the agent's progress as it happens:
          {"type": "step", "step": <trace step>}   — one per step, in order
          {"type": "done", "answer", "sources", "verses"}  — final result
        Used by the /api/chat/stream endpoint to show steps live; chat() drains it.
        step_delay (seconds) paces instant server-side steps (e.g. the binary-search
        probes) so they appear one-by-one like a chain being built; 0 = no pacing.
        """
        # Keep only the last N turns of plain chat history.
        history = [m for m in messages if m.get("role") in ("user", "assistant")][-MAX_HISTORY_MESSAGES:]
        last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")

        # Deterministic short-circuit: a PURE NUMBER goes straight to Dicta number
        # search — no LLM call (saves tokens), still produces a trace for the UI.
        if last_user.strip().isdigit():
            result = self._number_shortcircuit(last_user.strip())
            for s in result["trace"]:
                yield {"type": "step", "step": s}
            yield {"type": "done", "answer": result["answer"],
                   "sources": result["sources"], "verses": result.get("verses", [])}
            return

        convo: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        trace: List[Dict[str, Any]] = []
        collected_sources: List[str] = []
        wordcount_verses: List[Dict[str, Any]] = []  # verses to show with word numbering (UI)
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
                used_tool = any(s["type"] == "tool_call" for s in trace)
                # The "לא נמצא" heuristic only signals a punt when NO tool was used;
                # a deterministic tool answering "there are none" is a valid result.
                is_fallback = (FALLBACK_MESSAGE[:20] in answer) or (not used_tool and "לא נמצא" in answer)
                step += 1
                if is_fallback:
                    trace_step = {"type": "fallback", "label": "אין מקור מהימן",
                                  "summary": "הסוכן לא מצא מקור מספיק מהימן.", "confidence": "low"}
                elif used_tool:
                    trace_step = {"type": "final_answer", "label": "תשובה סופית",
                                  "summary": "התשובה נבנתה על בסיס הכלים והמקורות שנאספו.", "confidence": "high"}
                else:
                    # The model answered from its own general knowledge — be transparent.
                    answer += GENERAL_KNOWLEDGE_NOTE
                    trace_step = {"type": "final_answer", "label": "תשובה כללית (ללא מקור מהתנ״ך)",
                                  "summary": "נענה ממידע כללי של המודל — לא מטקסט התנ״ך.", "confidence": "medium"}
                final_step = {"step": step, "tool": None, "args": None, **trace_step}
                trace.append(final_step)
                yield {"type": "step", "step": final_step}
                yield {"type": "done", "answer": answer,
                       "sources": _dedupe(collected_sources), "verses": wordcount_verses}
                return

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
                elif name == "search_number":
                    collected_sources.extend(r["ref"] for r in result.get("results", []) if r.get("ref"))

                # Capture verses for the word-count visualization (last successful
                # verse_by_word_count call wins — e.g. the max N in a binary search).
                if name == "bible_structure" and result.get("word_count") is not None and result.get("verses"):
                    wordcount_verses = [
                        {"ref": v["ref"], "text": v["text"], "word_count": result["word_count"]}
                        for v in result["verses"]
                    ]

                # find_longest_verse runs a deterministic binary search; surface each
                # probe as its own trace step so the search is visible step-by-step.
                if name == "find_longest_verse" and not result.get("error"):
                    found = result.get("found", result.get("word_count"))
                    for p in result.get("probes", []):
                        n, al = p["word_count"], p["at_least"]
                        if al > 0:
                            psum = f"ניסיתי {n} מילים → קיימים פסוקים עם לפחות {n} מילים. מחפש גבוה יותר."
                            conf = "high"
                        else:
                            psum = f"ניסיתי {n} מילים → אין פסוק כה ארוך. מחפש נמוך יותר."
                            conf = "medium"
                        step += 1
                        ts = {"step": step, "type": "tool_call", "tool": name,
                              "label": TOOL_LABELS.get(name, name), "args": {"word_count": n},
                              "summary": psum, "confidence": conf}
                        trace.append(ts)
                        if step_delay:
                            time.sleep(step_delay)
                        yield {"type": "step", "step": ts}
                    # Concluding step: the search converged.
                    ref0 = result["verses"][0]["ref"] if result.get("verses") else ""
                    step += 1
                    if step_delay:
                        time.sleep(step_delay)
                    ts = {"step": step, "type": "tool_call", "tool": name,
                          "label": TOOL_LABELS.get(name, name), "args": None,
                          "summary": f"החיפוש התכנס: הפסוק הארוך ביותר מכיל {found} מילים ({ref0}).",
                          "confidence": "high"}
                    trace.append(ts)
                    yield {"type": "step", "step": ts}
                    wordcount_verses = [
                        {"ref": v["ref"], "text": v["text"], "word_count": found}
                        for v in result.get("verses", [])
                    ]
                    # Give the model a concise result (no probe noise) to synthesize from.
                    convo.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(
                        {"word_count": found, "total": result.get("total"), "verses": result.get("verses", [])},
                        ensure_ascii=False)})
                    continue

                meta = self._summarize(name, result)
                step += 1
                ts = {
                    "step": step,
                    "type": "tool_call",
                    "tool": name,
                    "label": TOOL_LABELS.get(name, name),
                    "args": args,
                    "summary": meta["summary"],
                    "confidence": meta["confidence"],
                }
                trace.append(ts)
                yield {"type": "step", "step": ts}

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
        final_step = {
            "step": step,
            "type": "fallback" if is_fallback else "final_answer",
            "tool": None,
            "label": "תשובה סופית (לאחר מגבלת צעדים)" if not is_fallback else "אין מקור מהימן",
            "args": None,
            "summary": "התשובה נבנתה לאחר שהסוכן הגיע למספר הצעדים המרבי." if not is_fallback else "הסוכן לא מצא מקור מספיק מהימן.",
            "confidence": "medium" if not is_fallback else "low",
        }
        trace.append(final_step)
        yield {"type": "step", "step": final_step}
        yield {"type": "done", "answer": answer,
               "sources": _dedupe(collected_sources), "verses": wordcount_verses}


def _dedupe(items: List[str]) -> List[str]:
    seen, out = set(), []
    for it in items:
        if it and it not in seen:
            seen.add(it)
            out.append(it)
    return out
