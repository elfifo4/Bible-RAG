# Bible-RAG: Advanced RAG System for the Hebrew Tanakh

A professional Retrieval-Augmented Generation (RAG) system specialized for the Hebrew Bible (Tanakh), featuring hybrid search, interactive evaluation, and a polished web interface.

---

Built by **Elad Finish** for the **AI for Developers** course, **Ben-Gurion University of the Negev**. (May 2026)

---

**GitHub Repository**: [https://github.com/elfifo4/Bible-RAG](https://github.com/elfifo4/Bible-RAG)

---

## ⚡ Quick Start
1. **Setup Environment**: 
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # Add your OPENAI_API_KEY and set APP_AUTH_PASSWORD in .env
   ```
2. **Setup UI**:
   ```bash
   cd frontend && npm install && cd ..
   ```
3. **Build Index**: 
   ```bash
   python3 build_index.py
   ```
4. **Launch App**: 
   ```bash
   python3 run_dev.py
   ```
   *Access at [http://localhost:5173](http://localhost:5173)*

---

## 📖 Overview
Bible-RAG is a custom RAG pipeline designed to answer factual, narrative, and genealogical questions about the Hebrew Bible. By combining state-of-the-art semantic embeddings with traditional lexical search, the system provides grounded answers with exact biblical citations (Book, Chapter:Verse), effectively eliminating LLM hallucinations.

### Key Features
- **Hybrid Retrieval Engine**: Uses `multilingual-e5-base` vectors + BM25 keyword matching.
- **Hebrew-First Design**: Specialized tokenization and normalization for Biblical Hebrew.
- **Interactive Evaluation Lab**: real-time strategy comparison and performance metrics.
- **Academic Rigor**: Built-in ablation studies and structured failure analysis.
- **Modern UI**: RTL-optimized React interface with a "parchment" aesthetic.

## 🏗️ Architecture
- **Parser**: Custom ingestion pipeline for 929 chapters of raw Tanakh text.
- **Retrieval**: FAISS (IndexFlatIP) for semantic search; Rank-BM25 for lexical search.
- **Generation**: OpenAI GPT-4o with grounded system prompting.
- **Backend**: FastAPI with JWT authentication and rate limiting.
- **Frontend**: React + Vite + Recharts.

## 🤖 חברותא — Agentic Study Companion (Final Project)
Building on the RAG pipeline above, **חברותא** turns the static system into a conversational **agent** that decides which tools to use, remembers the conversation, and corrects itself — directly closing the three weaknesses documented in the midterm (see [final_report.md](final_report.md)).

- **OpenAI function-calling loop** (`gpt-4o`, `max_iterations=5`, explicit fallback) wrapping the **existing** retriever and GPT client — retrieval/generation logic is untouched, and the already-loaded FAISS index is reused.
- **Four tools**:
  - 🔍 `search_tanakh` — hybrid/dense/lexical verse search (with self-correcting re-search)
  - 📖 `lookup_reference` — exact verse/range fetch by Book Chapter:Verse
  - 📚 `bible_structure` — structural/metadata answers (longest book, #books, #chapters, order) — *the gap the midterm planned to fix*
  - ⚖️ `compare_retrieval_strategies` — dense vs lexical vs hybrid, side by side
- **Agent Trace Visualization**: every answer carries a structured *operational* trace (which tool, args, result summary, confidence) rendered as a collapsible **timeline of step cards**, plus a **presentation mode** for the classroom demo. No internal chain-of-thought is exposed.
- **Access**: open the **"חברותא 🤖"** tab in the web app (alongside Q&A and Performance Metrics).

```bash
# Evaluate the agent (20-question gold set across structural/genealogy/factual/multi-turn)
python3 eval/agent_eval.py
# Deterministic structural-tool check (no OpenAI key required)
python3 eval/agent_eval.py --tools-only
```

## 📊 Evaluation & Reproducibility
The project includes a complete suite for measuring RAG performance:

```bash
# 1. Run all retrieval strategies (Hybrid, Dense, Lexical)
python3 eval/run_eval.py --strategy all

# 2. Run ablation experiments (impact of Top-K, components)
python3 eval/run_eval.py --ablation

# 3. Perform automated error/failure analysis
python3 eval/error_analysis.py

# 4. Generate report-ready assets and draft report
python3 eval/generate_report_assets.py
```
*Evaluation results are displayed visually in the "Performance Metrics" tab of the web app.*

## 📸 Project Gallery
*Refer to `docs/screenshots/` for visual documentation of the following:*
1. **Q&A Interface**: Clean chat layout with interactive references.
2. **Strategy Selector**: Comparative tool demonstrating RAG behavior.
3. **Evaluation Dashboard**: Visual charts for Hit@K and MRR metrics.
4. **Ablation Tables**: Side-by-side comparison of design choices.

## ⚠️ Limitations
- **Metadata Support**: Currently uses heuristics for structural questions; a dedicated metadata agent is planned.
- **Lemmatization**: Semantic search is strong, but lexical matching could be improved with a specialized Hebrew morphological analyzer.
- **Context Boundaries**: Narrative events spanning large chapter sections may require larger sliding windows.

## 🚀 Future Work
- **Reranking**: Integrate a Cross-Encoder (e.g., `dictabert`) for high-precision ranking.
- **Graph-RAG**: Use biblical genealogies to build a knowledge graph for complex relationship queries.
- **Deployment**: Full production containerization and cloud scaling.
