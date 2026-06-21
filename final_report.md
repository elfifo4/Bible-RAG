# Bible-RAG → "חברותא": An Agentic Study Companion for the Hebrew Tanakh

**Author:** Elad Finish
**Course:** AI for Developers, Ben-Gurion University of the Negev
**Deliverable:** Final project (builds on the midterm Bible-RAG system)

---

## 1. Motivation — from a static pipeline to an agent

The midterm ([report.md](report.md)) delivered a static RAG pipeline and, importantly,
*documented its own weaknesses*. The final project turns that pipeline into a
conversational **agent** ("חברותא") that decides which tools to use, remembers the
conversation, and corrects itself — directly closing the three documented gaps:

| # | Midterm weakness (documented) | Final-project fix |
|---|---|---|
| 1 | Structural/metadata questions unsupported ("longest book?", "how many books?") — README explicitly planned a *metadata agent* | New `bible_structure` tool over the existing `BIBLE_CATALOG` |
| 2 | 97% of failures were *retrieval miss* — a single, static retrieval pass | Agent **self-correction**: it can reformulate and re-search when scores are low |
| 3 | No multi-step reasoning for complex/follow-up questions | Function-calling **loop** + conversational memory |

## 2. Architecture

An **OpenAI function-calling agent loop** (`gpt-4o`, `temperature=0`) built *on top of*
the existing `VectorRetriever` and GPT client — the midterm's retrieval/generation
logic is **unchanged**; it is only wrapped. The agent reuses the already-loaded
retriever and FAISS index (no double load).

- **Loop control:** `max_iterations=5` (no infinite tool loops); history trimmed to the
  last ~14 messages; explicit **fallback** message when no reliable source is found.
- **Backend:** `src/agent.py` (`BibleAgent`) + a stateless `POST /api/chat` endpoint.
- **Frontend:** a third "חברותא 🤖" tab next to the existing QA and Evaluation tabs.

### Tools

| Tool | Purpose | Closes |
|---|---|---|
| 🔍 `search_tanakh(query, strategy)` | Hybrid/dense/lexical verse search (wraps the existing retriever) | #2 |
| 📖 `lookup_reference(book, chapter, verse)` | Exact verse/range fetch by reference | — |
| 📚 `bible_structure(query_type, book?)` | Structural answers from the catalog (no LLM) | **#1** |
| ⚖️ `compare_retrieval_strategies(query)` | Runs dense vs lexical vs hybrid and compares | analysis |

## 3. Explainability — Agent Trace Visualization

The agent is **not a black box**. Every answer carries a *structured operational trace*
(which tool, with what arguments, the result summary, and a confidence level) — never the
model's internal chain-of-thought. The UI renders it as a vertical **timeline of step
cards** with tool icons and confidence badges, collapsible by default, plus a
**presentation mode** (larger, cleaner cards) for the classroom demo.

## 4. Evaluation

**Structural subset (deterministic, no LLM):** `python3 eval/agent_eval.py --tools-only`

| Metric | Midterm RAG | חברותא agent |
|---|---|---|
| Structural questions (8) — e.g. longest book, #books, #chapters, book order | not supported (0/8) | **8/8 = 100%** |

This is the clearest "before/after": the exact question class the midterm could not handle
is now answered correctly and deterministically via the `bible_structure` tool.

**Full agent eval (20 questions across structural / genealogy / factual / reference /
lexical / strategy / multi-turn):** `python3 eval/agent_eval.py`

| Metric | Result |
|---|---|
| Tool-selection accuracy (right tool chosen) | **90%** (18/20) |
| Answer accuracy (keyword match, where an expected answer exists) | **84%** (16/19) |

The trace shows the agent behaving as intended:
- **Self-correction (#2):** *"מי היה אביו של אברהם?"* → `search_tanakh` ×3 then `lookup_reference` — it reformulated and re-searched before answering.
- **Multi-step:** *"באילו מקומות מוזכרת יריחו?"* → `search_tanakh` → `compare_retrieval_strategies` → `lookup_reference` ×3.
- **Memory:** the follow-up *"וכמה פרקים יש בו?"* was resolved from conversation context.

Remaining misses are honest and explainable — e.g. on *"מה כתוב בבראשית א:א?"* the model
occasionally answered from context without calling `lookup_reference` (a grounding gap, not
a retrieval one).

## 5. Limitations & future work

- **Live LLM cost/quota:** the conversational loop requires an OpenAI key with quota; the
  deterministic tools (structure/lookup) and retrieval run independently.
- **Lemmatization** (carried over from the midterm) would further reduce lexical misses.
- **Reranking** (cross-encoder) on the search candidates would raise grounding precision.
