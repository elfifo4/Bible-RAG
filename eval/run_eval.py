import json
import argparse
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
import numpy as np

# Adjust path to import from src
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.retrieval import VectorRetriever
from src.rag_system import BibleRAG
from src.utils import Gematria
from eval.metrics import calculate_hit_at_k, calculate_reciprocal_rank, calculate_recall_at_k

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Eval")

GOLD_SET_PATH = Path(__file__).parent / "gold_set.jsonl"
RESULTS_DIR = Path(__file__).parent / "results"

def load_gold_set(path: Path) -> List[Dict[str, Any]]:
    gold_set = []
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                gold_set.append(json.loads(line))
    return gold_set

def normalize_chapter(chapter_val: Any) -> int:
    if isinstance(chapter_val, int):
        return chapter_val
    if isinstance(chapter_val, str):
        if chapter_val.isdigit():
            return int(chapter_val)
        try:
            return Gematria.otiot_to_number(chapter_val)
        except Exception:
            return 0
    return 0

def is_chunk_relevant(chunk: Dict[str, Any], gold_item: Dict[str, Any]) -> bool:
    """
    Flexible relevance matching logic.
    1. Check exact chunk_id if available.
    2. Fallback to metadata matching (book and chapter).
    """
    must_cite = gold_item.get("must_cite_chunk_ids", [])
    if must_cite:
        return chunk["chunk_id"] in must_cite
    
    # Fallback to book/chapter metadata
    gold_meta = gold_item.get("metadata", {})
    if not gold_meta:
        return False
    
    chunk_meta = chunk.get("metadata", {})
    
    # Match Book (Hebrew or English)
    book_match = (
        chunk_meta.get("book") == gold_meta.get("book") or 
        chunk_meta.get("book_en") == gold_meta.get("book_en")
    )
    
    # Match Chapter (Gold set has Hebrew, chunks have Int)
    gold_chapter_num = normalize_chapter(gold_meta.get("chapter"))
    chunk_chapter_num = normalize_chapter(chunk_meta.get("chapter"))
    
    chapter_match = (gold_chapter_num > 0 and gold_chapter_num == chunk_chapter_num)
        
    return book_match and chapter_match

def run_retrieval_evaluation(
    strategy: str, 
    top_k: int = 5, 
    verbose: bool = False, 
    retriever: Optional[VectorRetriever] = None,
    gold_set: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    if gold_set is None:
        gold_set = load_gold_set(GOLD_SET_PATH)

    logger.info(f"\n" + "="*50)
    logger.info(f" RETRIEVAL EVALUATION — {strategy.upper()}")
    logger.info("="*50)

    if retriever is None:
        retriever = VectorRetriever()
    
    results = []
    all_metrics = {
        "hit@1": [], "hit@3": [], "hit@5": [], "recall@5": [], "mrr": []
    }

    for idx, item in enumerate(gold_set):
        question = item["question"]
        retrieved_chunks = retriever.retrieve(question, top_k=max(top_k, 5), strategy=strategy)
        relevant_indices = [i for i, chunk in enumerate(retrieved_chunks) if is_chunk_relevant(chunk, item)]
        
        retrieved_ids = list(range(len(retrieved_chunks)))
        relevant_ids_set = set(relevant_indices)
        
        found = len(relevant_ids_set) > 0
        first_rank = (relevant_indices[0] + 1) if found else None
        
        h1 = calculate_hit_at_k(retrieved_ids, relevant_ids_set, 1)
        h3 = calculate_hit_at_k(retrieved_ids, relevant_ids_set, 3)
        h5 = calculate_hit_at_k(retrieved_ids, relevant_ids_set, 5)
        r5 = calculate_recall_at_k(retrieved_ids, relevant_ids_set, 5)
        mrr = calculate_reciprocal_rank(retrieved_ids, relevant_ids_set)

        all_metrics["hit@1"].append(h1); all_metrics["hit@3"].append(h3)
        all_metrics["hit@5"].append(h5); all_metrics["recall@5"].append(r5)
        all_metrics["mrr"].append(mrr)

        results.append({
            "question": question, "strategy": strategy, "relevant_found": found,
            "first_relevant_rank": first_rank, "hit@1": h1, "hit@3": h3, "hit@5": h5,
            "recall@5": r5, "mrr": mrr,
            "retrieved_refs": [c["metadata"].get("ref_en", "N/A") for c in retrieved_chunks[:top_k]]
        })

        if verbose:
            status = "✓" if found else "✗"
            logger.info(f"[{idx+1}] {status} {question}{f' (Rank: {first_rank})' if found else ''}")

    summary = {
        "strategy": strategy, "questions_count": len(gold_set),
        "hit@1": float(np.mean(all_metrics["hit@1"])),
        "hit@3": float(np.mean(all_metrics["hit@3"])),
        "hit@5": float(np.mean(all_metrics["hit@5"])),
        "recall@5": float(np.mean(all_metrics["recall@5"])),
        "mrr": float(np.mean(all_metrics["mrr"]))
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / f"retrieval_eval_{strategy}.json", 'w', encoding='utf-8') as f:
        json.dump({"summary": summary, "detailed_results": results}, f, ensure_ascii=False, indent=2)

    return summary

def run_generation_evaluation(
    strategy: str, 
    limit: Optional[int] = None,
    gold_set: Optional[List[Dict[str, Any]]] = None
):
    logger.info(f"\n" + "="*50)
    logger.info(f" ANSWER EVALUATION — {strategy.upper()}")
    logger.info("="*50)

    if gold_set is None:
        gold_set = load_gold_set(GOLD_SET_PATH)
    
    if limit:
        gold_set = gold_set[:limit]

    rag = BibleRAG()
    results = []
    
    for idx, item in enumerate(gold_set):
        question = item["question"]
        ref_answer = item.get("reference_answer", "")
        
        logger.info(f"[{idx+1}/{len(gold_set)}] Answering: {question}")
        res = rag.answer(question, retrieval_strategy=strategy)
        
        gen_answer = res["answer"]
        sources = res["sources"]
        retrieved_refs = [c["metadata"]["ref_en"] for c in res["retrieved_chunks"]]
        
        # Simple auto checks
        contains_ref = False
        if ref_answer and ref_answer.lower() in gen_answer.lower():
            contains_ref = True
            
        has_sources = len(sources) > 0
        
        results.append({
            "question": question,
            "reference_answer": ref_answer,
            "generated_answer": gen_answer,
            "sources": sources,
            "retrieved_refs": retrieved_refs,
            "strategy": strategy,
            "contains_reference_answer": contains_ref,
            "has_sources": has_sources,
            "manual_score": "",
            "manual_notes": ""
        })

    # Save JSON
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS_DIR / f"answer_eval_{strategy}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Save CSV Template
    csv_path = RESULTS_DIR / "manual_eval_template.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["question", "reference_answer", "generated_answer", "sources", "retrieved_refs", "manual_score", "citation_quality", "notes"])
        for r in results:
            writer.writerow([
                r["question"], r["reference_answer"], r["generated_answer"], 
                ", ".join(r["sources"]), ", ".join(r["retrieved_refs"]),
                "", "", ""
            ])

    logger.info(f"\nGeneration evaluation complete.")
    logger.info(f"JSON results: {json_path}")
    logger.info(f"CSV Template for manual review: {csv_path}")

def run_all_evaluations(top_k: int, verbose: bool):
    logger.info("Starting All Retrieval Evaluations...")
    gold_set = load_gold_set(GOLD_SET_PATH)
    retriever = VectorRetriever()
    strategies = ["hybrid", "dense_only", "lexical_only"]
    all_summaries = {}

    for strat in strategies:
        summary = run_retrieval_evaluation(strat, top_k, verbose, retriever, gold_set)
        all_summaries[strat] = summary

    with open(RESULTS_DIR / "retrieval_eval_summary.json", 'w', encoding='utf-8') as f:
        json.dump({"strategies": all_summaries}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Bible-RAG Performance")
    parser.add_argument("--strategy", default="hybrid", choices=["hybrid", "dense_only", "lexical_only", "all"])
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--include-generation", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    
    args = parser.parse_args()
    
    if args.strategy == "all":
        run_all_evaluations(args.top_k, args.verbose)
    else:
        run_retrieval_evaluation(args.strategy, args.top_k, args.verbose)
        
    if args.include_generation:
        run_generation_evaluation(args.strategy, args.limit)
