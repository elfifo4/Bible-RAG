import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

RESULTS_DIR = Path(__file__).parent / "results"
REPORT_DATA_DIR = RESULTS_DIR / "report_data"

METADATA_KEYWORDS = ["כמה ספרים", "מספר הספרים", "החומש", "כמה פרקים", "איזה ספר", "מה הספר", "סדר הספרים"]

def categorize_failure(q_res: Dict[str, Any], ans_res: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    question = q_res["question"].lower()
    
    # 1. Metadata check
    if any(kw in question for kw in METADATA_KEYWORDS):
        return {
            "category": "metadata_question_not_supported",
            "reason": "The question is about corpus structure/metadata which is not currently indexed in the vector store.",
            "suggested_fix": "Implement a metadata retriever or index structural properties."
        }
    
    # 2. Retrieval checks
    if not q_res.get("relevant_found", False):
        return {
            "category": "retrieval_miss",
            "reason": "No relevant chunks were found in the top retrieved results.",
            "suggested_fix": "Improve embedding model or add lexical/keyword boost."
        }
    
    rank = q_res.get("first_relevant_rank")
    if rank and rank > 5:
        return {
            "category": "low_rank_relevant_chunk",
            "reason": f"Relevant chunk found but ranked at position {rank} (outside Top-5).",
            "suggested_fix": "Improve ranking algorithm or use a re-ranker."
        }

    # 3. Generation checks (if answer evaluation exists)
    if ans_res:
        if q_res.get("relevant_found") and not ans_res.get("contains_reference_answer"):
            return {
                "category": "generation_error",
                "reason": "Correct context was retrieved, but the LLM failed to extract the correct answer.",
                "suggested_fix": "Refine the generation prompt or use a more capable LLM."
            }
        
        if not ans_res.get("has_sources"):
            return {
                "category": "missing_citation",
                "reason": "The answer was generated but no sources were cited.",
                "suggested_fix": "Enforce citation rules in the system prompt."
            }

    return {
        "category": "unknown",
        "reason": "Failure cause not explicitly identified by heuristics.",
        "suggested_fix": "Manual inspection required."
    }

def run_error_analysis():
    print("Starting Error Analysis...")
    
    # Load retrieval results (default to hybrid)
    ret_path = RESULTS_DIR / "retrieval_eval_hybrid.json"
    if not ret_path.exists():
        # Try finding any retrieval result
        ret_files = list(RESULTS_DIR.glob("retrieval_eval_*.json"))
        if not ret_files:
            print("Error: No retrieval results found. Run eval/run_eval.py first.")
            return
        ret_path = ret_files[0]
    
    with open(ret_path, 'r', encoding='utf-8') as f:
        ret_data = json.load(f)
        
    # Load answer results if available
    ans_data = {}
    ans_path = RESULTS_DIR / "answer_eval_hybrid.json"
    if ans_path.exists():
        with open(ans_path, 'r', encoding='utf-8') as f:
            ans_list = json.load(f)
            ans_data = {a["question"]: a for a in ans_list}

    failures = []
    category_counts = {}

    for q_res in ret_data["detailed_results"]:
        # A failure is either a retrieval miss (hit@5) or an answer miss
        ans_res = ans_data.get(q_res["question"])
        
        is_ret_failure = not q_res.get("hit@5", False)
        is_ans_failure = ans_res and not ans_res.get("contains_reference_answer", False)
        
        if is_ret_failure or is_ans_failure:
            analysis = categorize_failure(q_res, ans_res)
            cat = analysis["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1
            
            failures.append({
                "question": q_res["question"],
                "strategy": q_res["strategy"],
                "category": cat,
                "reason": analysis["reason"],
                "suggested_fix": analysis["suggested_fix"],
                "retrieved_refs": q_res["retrieved_refs"],
                "first_relevant_rank": q_res.get("first_relevant_rank")
            })

    summary = {
        "total_failures": len(failures),
        "by_category": category_counts
    }

    results = {
        "summary": summary,
        "failures": failures
    }

    # 1. Save JSON
    with open(RESULTS_DIR / "error_analysis.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 2. Save Markdown
    md_content = "# Error Analysis Report\n\n"
    md_content += "## Summary\n\n"
    md_content += "| Category | Count |\n|---|---:|\n"
    for cat, count in category_counts.items():
        md_content += f"| {cat} | {count} |\n"
    md_content += f"| **Total** | **{len(failures)}** |\n\n"
    
    md_content += "## Representative Failures\n\n"
    md_content += "| Question | Category | Reason | Suggested Fix |\n|---|---|---|---|\n"
    for f in failures[:15]: # Show first 15 examples
        md_content += f"| {f['question']} | {f['category']} | {f['reason']} | {f['suggested_fix']} |\n"

    with open(RESULTS_DIR / "error_analysis.md", 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 3. Save CSV for Report
    REPORT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_DATA_DIR / "failure_examples.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Question", "Category", "Reason", "Suggested Fix"])
        for f in failures:
            writer.writerow([f["question"], f["category"], f["reason"], f["suggested_fix"]])

    print(f"Error analysis complete. Analyzed {len(failures)} failures.")
    print(f"Results saved to {RESULTS_DIR}")

if __name__ == "__main__":
    run_error_analysis()
