# Bible-RAG: Advanced Retrieval-Augmented Generation for the Hebrew Tanakh

**Author:** Elad Finish  
**Course:** AI for Developers, Ben-Gurion University of the Negev  
**Date:** May 2026  

---

## Executive Summary

This project implements a custom RAG (Retrieval-Augmented Generation) pipeline specifically optimized for the Hebrew Bible (Tanakh). By combining dense semantic search (`multilingual-e5-base`) with lexical keyword matching (BM25), the system provides grounded answers to biblical questions with precise book/chapter/verse citations. The pipeline includes an interactive evaluation dashboard, automated ablation studies, and a failure analysis framework to ensure academic rigor and explainability.

## 1. Corpus Description

The corpus consists of the full Hebrew Tanakh, structured into 39 books and 929 chapters.
- **Size:** 23,202 individual verses and approximately 30,600 chunks.
- **Suitability for RAG:** The Tanakh is highly factual and dense with names, locations, and genealogies. Citation accuracy is paramount in biblical scholarship, making it an ideal candidate for RAG over baseline LLMs, which frequently hallucinate specific references.
- **Preprocessing:** Raw UTF-16 files were normalized by removing cantillation (teamim) while optionally preserving niqqud for display. Deterministic IDs (e.g., `_01_bereshit_001_001`) ensure stability across indexing and evaluation.

## 2. System Architecture

The system utilizes a modular RAG architecture:
1.  **Ingestion & Normalization:** Python-based parser handles Hebrew text cleaning and structural marker extraction (e.g., `{פ}`).
2.  **Chunking:** Supports both single-verse and sliding-window (5 verses with 2-verse overlap) strategies.
3.  **Indexing:** High-dimensional embeddings stored in a **FAISS IndexFlatIP** for optimized cosine similarity search.
4.  **Retrieval:** A hybrid engine combining dense vector search and BM25 lexical matching.
5.  **Generation:** OpenAI’s GPT-4o model, driven by a system prompt enforcing grounding and citation rules.
6.  **Interface:** A full-stack web demo (FastAPI + React) featuring a comparative retrieval lab.

## 3. Preprocessing and Chunking Strategy

To optimize for different query types, the system implements:
-   **Single Verse Chunks:** Ideal for specific factual lookups and exact citations.
-   **Sliding Window (Size: 5, Overlap: 2):** Preserves narrative context, allowing the LLM to understand events that span across verse boundaries (e.g., narrative sequences in Exodus or Judges).
-   **Normalization:** We generate a `text_plain` version (no niqqud/teamim) for embeddings to minimize noise, while maintaining `display_text` for high-quality user output.

## 4. Embedding and Vector Index Choice

-   **Model:** `intfloat/multilingual-e5-base`. We chose this over generic BERT models because it is explicitly trained for retrieval tasks and supports Hebrew effectively using `query:` and `passage:` prefixes.
-   **Index:** **FAISS IndexFlatIP**. By L2-normalizing vectors and using Inner Product, we achieve efficient Cosine Similarity search, which is superior to Euclidean distance for semantic similarity in high-dimensional spaces.

## 5. Retrieval & Query Routing

The system supports interactive switching between retrieval modes:
-   **Dense Only:** Pure semantic similarity.
-   **Lexical Only:** BM25 matching (vital for specific biblical names like "Terah" or "Jericho").
-   **Hybrid (Default):** A weighted merge (65% Semantic / 35% Lexical). 
-   **Query Routing:** The system detects "Enumeration" (איפה מוזכר...) vs. "Genealogy" (מי הוליד...) queries and dynamically boosts lexical weights to 60% for higher precision on specific terms.

## 6. Prompt Design

The generation prompt is strictly grounded:
-   **Constraint:** "Answer ONLY from the provided context."
-   **Citation:** "Always cite your sources using the Hebrew Book Chapter:Verse format."
-   **Punt:** "If the answer is not in the context, say so clearly."
-   **Formatting:** When quoting Hebrew, the model is instructed to append the traditional *Sof Pasuk* (׃) symbol.

## 7. Evaluation Results

The system was evaluated against a **Gold Set of 50 questions** covering factual, temporal, and narrative domains.

| Strategy | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| **Hybrid** | **0.100** | **0.120** | **0.160** | **0.116** |
| Lexical Only | 0.080 | 0.100 | 0.140 | 0.095 |
| Dense Only | 0.060 | 0.080 | 0.100 | 0.071 |

*Note: The Hit@5 of 16% highlights the extreme difficulty of Biblical Hebrew retrieval and the need for further fine-tuning of the embedding model.*

## 8. Ablation Study

We analyzed the impact of Top-K values on the Hybrid strategy:

| Top-K | Hit@1 | Hit@3 | Hit@5 | MRR |
|---:|---:|---:|---:|---:|
| 3 | 0.100 | 0.120 | - | 0.116 |
| 5 | 0.100 | 0.120 | 0.160 | 0.116 |
| 10 | 0.100 | 0.120 | 0.160 | 0.125 |

Increasing Top-K from 5 to 10 improved the MRR, suggesting that relevant verses are often present but ranked lower in the initial semantic pass.

## 9. Failure Analysis

Total Failures Analyzed: 43. Key failure modes included:
1.  **Retrieval Miss (97% of failures):** The ancient Hebrew phrasing in the query often differed significantly from the text (Lexical Mismatch), or the semantic model drifted toward unrelated war/prayer themes (Semantic Drift).
2.  **Metadata Limitations:** Questions about book counts or book order were not handled by verse retrieval (Metadata Question Not Supported).

### Representative Failures:
-   **Question:** "מי אמר למי: 'הַמְצָאתַנִי אֹיְבִי'?"
-   **Failure:** `retrieval_miss`. The system retrieved other mentions of "enemies" but missed the specific 1 Kings 21 context due to the brevity of the phrase.
-   **Fix:** Use a specialized Hebrew lemmatizer to match word roots.

## 10. Future Improvements

1.  **Reranking Layer:** Implement a second-stage Cross-Encoder (e.g., `dictabert`) to re-score the Top-50 candidates.
2.  **Metadata Retriever:** Add a structured agent to answer structural questions (e.g., "Which is the longest book?").
3.  **Hebrew Lemmatization:** Improve BM25 accuracy by stripping Hebrew prefixes and suffixes more aggressively.
