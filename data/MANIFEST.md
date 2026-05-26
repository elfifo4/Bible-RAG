# Corpus Manifest: Hebrew Tanakh / Bible

**Generated on:** 2026-05-18

## 1. Corpus Name
Hebrew Tanakh / Bible Corpus

## 2. Domain
Biblical Hebrew text; religious, literary, and historical corpus.

## 3. Source of Documents
The raw corpus consists of chapter-level text files located under `data/raw/`. These files serve as the ground truth for all downstream processing, indexing, and retrieval.

## 4. Number of Documents
- **Raw Documents:** 929 `.txt` files (one per chapter).
- **Processed Documents:** 929 `.json` files (structured chapter data).
- **Tabular Data:** 
  - `all_verses.jsonl`: 23,202 individual verses.
  - `all_chunks.jsonl`: 30,617 chunks (includes multiple chunking strategies).

## 5. Approximate Size
- **Books:** 39
- **Chapters:** 929
- **Verses:** 23,202
- **Chunks:** ~30,600
- **Approximate Tokens:** ~300,000 - 400,000 words (Biblical Hebrew).

## 6. File Types
- **Raw:** `.txt` (UTF-16 encoded text files).
- **Processed:** `.json` (Structured metadata and verse content per chapter).
- **Interchange:** `.jsonl` (Line-delimited JSON for bulk verse and chunk access).
- **Index:** `.faiss` (Binary vector index for semantic search).

## 7. License / Permission
The corpus is used strictly for academic and course purposes as part of an AI development assignment. The raw text is sourced from public domain or academic repositories. Users should verify exact licensing before any public distribution or commercial use.

## 8. Why this Corpus is Suitable for RAG
- **Rich Structure:** The book/chapter/verse hierarchy allows for precise retrieval and granular citations.
- **Fact-Dense Content:** The Tanakh contains extensive genealogical records, geographical markers, historical narratives, and specific numerical data that are ideal for testing retrieval accuracy.
- **Evidence-Based QA:** While baseline LLMs often have "memorized" parts of the Bible, they frequently hallucinate details or provide vague answers. RAG ensures that every answer is backed by the specific retrieved verse, providing verifiable evidence and exact citations.
- **Complexity:** Biblical Hebrew presents unique challenges for embeddings (morphology, ancient syntax), making it an excellent domain for advanced NLP experimentation.

## 9. Supported Questions
The system is designed to handle various query types:
- **Genealogy:** "מי הוליד את אברם?" (Who begot Abram?)
- **Location-Based:** "מה קרה ביריחו?" (What happened in Jericho?)
- **Enumeration:** "תן לי מקומות שבהם מוזכר שופר" (Give me places where a shofar is mentioned).
- **Narrative:** "מי הייתה אמו של שמואל?" (Who was Samuel's mother?)
- **Thematic/Semantic:** "מה התנ״ך אומר על פחד?" (What does the Bible say about fear?)
- **Structural:** "מה החומש החמישי?" (What is the fifth book of the Pentateuch?) — supported via metadata retrieval.

## 10. Privacy / Sensitive Information
No private personal data or PII is included in this corpus. The dataset consists entirely of public, ancient religious and literary texts.

## 11. Preprocessing Summary
The pipeline performs several critical normalization steps:
- **Loading:** Handles UTF-16BE/LE and UTF-8 encoding detection.
- **Cleaning:** Removes cantillation (טעמים) and optionally niqqud (ניקוד) for the embedding "text" field to improve semantic matching.
- **Normalization:** Standardizes spaces, handles special characters (e.g., maqaf, paseq), and preserves original formatting for display.
- **Marker Extraction:** Identifies and preserves structural markers such as `{פ}` (Petuha), `{ס}` (Setuma), and Aliyah markers.
- **Identifiers:** Generates stable, deterministic IDs for every verse (e.g., `_01_bereshit_001_001`).

## 12. Chunking Summary
The system supports multiple strategies to optimize retrieval context:
- **Single Verse:** Each verse is an independent chunk. Best for exact citations.
- **Sliding Window:** Groups of verses (e.g., 5 verses with overlap) to preserve narrative flow and broader context.
- **Metadata:** Each chunk carries rich metadata: Book (Heb/En), Chapter, Verse Range, Reference Strings, and Chunk Type.
