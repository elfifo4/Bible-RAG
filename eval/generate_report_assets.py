import json
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
EVAL_RESULTS_DIR = BASE_DIR / "eval" / "results"
REPORT_DATA_DIR = EVAL_RESULTS_DIR / "report_data"
MANIFEST_PATH = BASE_DIR / "data" / "MANIFEST.md"

def load_json(path):
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_manifest_content():
    if not MANIFEST_PATH.exists():
        return "Corpus information not available."
    return MANIFEST_PATH.read_text(encoding='utf-8')

def generate_evaluation_table(retrieval_summary):
    if not retrieval_summary:
        return "Retrieval evaluation results not found."
    
    strategies = retrieval_summary.get("strategies", {})
    md = "| Strategy | Hit@1 | Hit@3 | Hit@5 | MRR |\n"
    md += "|---|---:|---:|---:|---:|\n"
    for strat, metrics in strategies.items():
        # Use hit_at_1, hit_at_3, etc. to match the actual generated JSON keys
        h1 = metrics.get('hit_at_1', 0)
        h3 = metrics.get('hit_at_3', 0)
        h5 = metrics.get('hit_at_5', 0)
        mrr = metrics.get('mrr', 0)
        md += f"| {strat} | {h1:.3f} | {h3:.3f} | {h5:.3f} | {mrr:.3f} |\n"
    return md

def generate_ablation_table(ablation_results):
    if not ablation_results:
        return "Ablation results not found."
    
    md = "### Retrieval Strategy Ablation\n\n"
    md += "| Variant | Hit@1 | Hit@3 | Hit@5 | MRR |\n"
    md += "|---|---:|---:|---:|---:|\n"
    for r in ablation_results.get("retrieval_strategy_ablation", []):
        md += f"| {r['variant']} | {r['hit_at_1']:.3f} | {r['hit_at_3']:.3f} | {r['hit_at_5']:.3f} | {r['mrr']:.3f} |\n"
    
    md += "\n### Top-K Ablation (Strategy: Hybrid)\n\n"
    md += "| Top-K | Hit@1 | Hit@3 | Hit@5 | MRR |\n"
    md += "|---|---:|---:|---:|---:|\n"
    for r in ablation_results.get("top_k_ablation", []):
        md += f"| {r['top_k']} | {r['hit_at_1']:.3f} | {r['hit_at_3']:.3f} | {r.get('hit_at_5', 0):.3f} | {r['mrr']:.3f} |\n"
    
    return md

def generate_failure_summary(error_analysis):
    if not error_analysis:
        return "Error analysis results not found."
    
    summary = error_analysis.get("summary", {})
    md = f"Total Failures Analyzed: {summary.get('total_failures', 0)}\n\n"
    md += "| Category | Count |\n"
    md += "|---|---:|\n"
    for cat, count in summary.get("by_category", {}).items():
        md += f"| {cat} | {count} |\n"
    return md

def generate_representative_examples(error_analysis):
    if not error_analysis:
        return "Error analysis results not found."
    
    failures = error_analysis.get("failures", [])
    md = "| Question | Category | Reason | Suggested Fix |\n"
    md += "|---|---|---|---|\n"
    for f in failures[:5]:  # Show top 5 examples
        md += f"| {f['question']} | {f['category']} | {f['reason']} | {f['suggested_fix']} |\n"
    return md

def generate_report_draft(manifest, eval_table, ablation_table, failure_summary, examples):
    draft = f"""# Bible-RAG: Custom RAG Pipeline over the Hebrew Tanakh

## 1. Corpus

The corpus used in this project is the full Hebrew Tanakh (Bible), consisting of 929 chapters.
The data is structured hierarchically by book, chapter, and verse.
Tanakh is highly suitable for RAG due to its fact-dense nature (genealogy, history, geography) and the critical importance of exact citations in biblical scholarship.

Key Statistics:
- 929 Chapters
- 23,202 Verses
- Over 30,000 Chunks

## 2. System Architecture

The system follows a modular RAG architecture:
1. **Ingestion**: Processes raw UTF-16 text files into structured JSON.
2. **Preprocessing**: Normalizes Hebrew text, removing cantillation (teamim) for better embedding quality while preserving original text for display.
3. **Indexing**: Uses `intfloat/multilingual-e5-base` embeddings stored in a FAISS vector index (IndexFlatIP for cosine similarity).
4. **Retrieval**: Supports hybrid search combining semantic (Dense) and keyword-based (BM25) retrieval.
5. **Generation**: Uses OpenAI's GPT-4o model with a strict system prompt to ensure grounding and accurate citations.
6. **Interface**: A FastAPI backend serves a React-based web demo with interactive strategy comparison.

## 3. Preprocessing and Chunking

We implement several preprocessing steps:
- `text_plain`: Hebrew text without niqqud or teamim (used for embeddings).
- `display_text`: Original text with niqqud preserved.
- Structural marker extraction (e.g., {{פ}}, {{ס}}).

Chunking Strategies:
- **Single Verse**: Each verse is a standalone chunk.
- **Sliding Window**: Overlapping windows of 5 verses to provide broader narrative context.

## 4. Embedding and Indexing

We chose `intfloat/multilingual-e5-base` as the embedding model due to its strong performance in multilingual retrieval tasks. Embeddings are L2-normalized and indexed using **FAISS IndexFlatIP**, enabling efficient and accurate semantic similarity searches.

## 5. Retrieval

The system supports multiple retrieval modes:
- **Dense Only**: Pure vector search.
- **Lexical Only**: BM25 keyword matching (vital for names and specific terms).
- **Hybrid**: A weighted combination of both, optimized for biblical Hebrew.
- **Query Routing**: Detects query types (e.g., genealogy vs. enumeration) to adjust retrieval weights dynamically.

## 6. Answer Generation

The generation engine receives the retrieved chunks and is instructed to:
1. Answer ONLY based on the provided context.
2. Provide exact Book:Chapter:Verse citations.
3. State clearly if the information is missing from the context.

## 7. Evaluation Results

The following table summarizes the retrieval performance of the baseline strategies:

{eval_table}

## 8. Ablation Study

We conducted ablation experiments to measure the impact of different retrieval and indexing choices.

{ablation_table}

## 9. Failure Analysis

Common failure modes identified during evaluation:

{failure_summary}

### Representative Failure Examples:

{examples}

## 10. Future Improvements

1. **Enhanced Metadata Retrieval**: Implementing specialized handlers for structural questions (e.g., book counts).
2. **Reranking Layer**: Adding a second-stage cross-encoder to improve precision.
3. **Better Hebrew Normalization**: Advanced lemmatization to handle complex biblical morphology.
4. **Gold Set Refinement**: Expanding the evaluation set with more granular 'must-cite' identifiers.

"""
    return draft

def main():
    print("Generating report assets...")
    REPORT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    retrieval_summary = load_json(EVAL_RESULTS_DIR / "retrieval_eval_summary.json")
    ablation_results = load_json(EVAL_RESULTS_DIR / "ablation_results.json")
    error_analysis = load_json(EVAL_RESULTS_DIR / "error_analysis.json")
    manifest_content = get_manifest_content()
    
    # Generate individual assets
    eval_table = generate_evaluation_table(retrieval_summary)
    ablation_table = generate_ablation_table(ablation_results)
    failure_summary = generate_failure_summary(error_analysis)
    examples = generate_representative_examples(error_analysis)
    
    # Save assets
    (REPORT_DATA_DIR / "evaluation_table.md").write_text(eval_table, encoding='utf-8')
    (REPORT_DATA_DIR / "ablation_table.md").write_text(ablation_table, encoding='utf-8')
    (REPORT_DATA_DIR / "failure_analysis_summary.md").write_text(failure_summary, encoding='utf-8')
    (REPORT_DATA_DIR / "representative_examples.md").write_text(examples, encoding='utf-8')
    
    # Generate and save final report draft
    report_draft = generate_report_draft(manifest_content, eval_table, ablation_table, failure_summary, examples)
    (REPORT_DATA_DIR / "report_draft.md").write_text(report_draft, encoding='utf-8')
    
    print(f"Report assets generated in: {REPORT_DATA_DIR}")
    print(f"Draft report ready at: {REPORT_DATA_DIR / 'report_draft.md'}")

if __name__ == "__main__":
    main()
