import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Set
import numpy as np

# Adjust path to import from src
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.retrieval import VectorRetriever
from src.utils import Gematria
from eval.metrics import calculate_hit_at_k, calculate_reciprocal_rank, calculate_recall_at_k

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Eval")

GOLD_SET_PATH = Path(__file__).parent / "gold_set.jsonl"
RESULTS_DIR = Path(__file__).parent / "results"

def load_gold_set(path: Path) -> List[Dict[str, Any]]:
    gold_set = []
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

def run_evaluation(strategy: str, top_k: int, verbose: bool):
    logger.info(f"Starting Retrieval Evaluation (Strategy: {strategy}, Top-K: {top_k})")
    
    if not GOLD_SET_PATH.exists():
        logger.error(f"Gold set not found at {GOLD_SET_PATH}")
        return

    gold_set = load_gold_set(GOLD_SET_PATH)
    logger.info(f"Loaded {len(gold_set)} questions from gold set.")

    # Initialize Retriever once
    retriever = VectorRetriever()
    
    results = []
    all_metrics = {
        "hit@1": [],
        "hit@3": [],
        "hit@5": [],
        "recall@5": [],
        "mrr": []
    }

    for idx, item in enumerate(gold_set):
        question = item["question"]
        retrieved_chunks = retriever.retrieve(question, top_k=max(top_k, 5), strategy=strategy)
        
        # Determine which of the retrieved chunks are actually relevant
        relevant_indices = [i for i, chunk in enumerate(retrieved_chunks) if is_chunk_relevant(chunk, item)]
        
        # For metrics, we need a unique identifier list and a set of relevant identifiers
        retrieved_ids = list(range(len(retrieved_chunks)))
        relevant_ids_set = set(relevant_indices)
        
        found = len(relevant_ids_set) > 0
        first_rank = (relevant_indices[0] + 1) if found else None
        
        # Calculate Metrics
        h1 = calculate_hit_at_k(retrieved_ids, relevant_ids_set, 1)
        h3 = calculate_hit_at_k(retrieved_ids, relevant_ids_set, 3)
        h5 = calculate_hit_at_k(retrieved_ids, relevant_ids_set, 5)
        r5 = calculate_recall_at_k(retrieved_ids, relevant_ids_set, 5)
        mrr = calculate_reciprocal_rank(retrieved_ids, relevant_ids_set)

        all_metrics["hit@1"].append(h1)
        all_metrics["hit@3"].append(h3)
        all_metrics["hit@5"].append(h5)
        all_metrics["recall@5"].append(r5)
        all_metrics["mrr"].append(mrr)

        q_result = {
            "question": question,
            "strategy": strategy,
            "relevant_found": found,
            "first_relevant_rank": first_rank,
            "hit@1": h1,
            "hit@3": h3,
            "hit@5": h5,
            "recall@5": r5,
            "mrr": mrr,
            "retrieved_refs": [c["metadata"].get("ref_en", "N/A") for c in retrieved_chunks[:top_k]]
        }
        results.append(q_result)

        if verbose:
            status = "✓" if found else "✗"
            rank_str = f" (Rank: {first_rank})" if found else ""
            logger.info(f"[{idx+1}] {status} {question}{rank_str}")
            if not found:
                logger.info(f"    Expected: {item.get('metadata')}")
                logger.info(f"    Top retrieved: {q_result['retrieved_refs'][0] if q_result['retrieved_refs'] else 'None'}")

    # Summary
    summary = {
        "strategy": strategy,
        "questions_count": len(gold_set),
        "hit@1": float(np.mean(all_metrics["hit@1"])),
        "hit@3": float(np.mean(all_metrics["hit@3"])),
        "hit@5": float(np.mean(all_metrics["hit@5"])),
        "recall@5": float(np.mean(all_metrics["recall@5"])),
        "mrr": float(np.mean(all_metrics["mrr"]))
    }

    # Save Results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"retrieval_eval_{strategy}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"summary": summary, "detailed_results": results}, f, ensure_ascii=False, indent=2)

    # Print Table
    print("\n" + "="*40)
    print(f" RETRIEVAL EVALUATION — {strategy.upper()}")
    print("="*40)
    print(f"Questions evaluated: {summary['questions_count']}")
    print(f"Hit@1:    {summary['hit@1']:.3f}")
    print(f"Hit@3:    {summary['hit@3']:.3f}")
    print(f"Hit@5:    {summary['hit@5']:.3f}")
    print(f"Recall@5: {summary['recall@5']:.3f}")
    print(f"MRR:      {summary['mrr']:.3f}")
    print("="*40)
    print(f"Full results saved to: {output_path}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Bible-RAG Retrieval Performance")
    parser.add_argument("--strategy", default="hybrid", choices=["hybrid", "dense_only", "lexical_only"], help="Retrieval strategy to evaluate")
    parser.add_argument("--top-k", type=int, default=5, help="Top K results to consider")
    parser.add_argument("--verbose", action="store_true", help="Print per-question status")
    
    args = parser.parse_args()
    run_evaluation(args.strategy, args.top_k, args.verbose)
