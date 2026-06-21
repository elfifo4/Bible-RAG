"""
Agent evaluation for the "חברותא" final project.

Two modes:
  --tools-only : DETERMINISTIC. Checks the bible_structure tool against the
                 structural subset of the gold set. Needs NO OpenAI / no
                 embeddings — proves the midterm's documented weakness #1
                 ("structural/metadata questions not supported") is now fixed.
  (default)    : FULL agent eval. Runs the whole function-calling loop on every
                 question, recording the answer, the tools the agent chose, the
                 trace, and simple auto-checks. Needs a working OpenAI key.

Outputs: eval/results/agent_eval.json + eval/results/agent_eval.md
"""

import json
import argparse
import sys
import os
from pathlib import Path
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import BibleAgent

GOLD_PATH = Path(__file__).parent / "agent_gold_set.jsonl"
RESULTS_DIR = Path(__file__).parent / "results"


def load_gold(path: Path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


def _messages_for(item):
    if "messages" in item:
        return item["messages"]
    return [{"role": "user", "content": item["question"]}]


def _label(item):
    return item.get("question") or item["messages"][-1]["content"]


# ------------------------------------------------------------ tools-only mode
def build_agent_tools_only() -> BibleAgent:
    """Minimal agent: only the deterministic catalog/lookup tools (no LLM, no FAISS)."""
    agent = BibleAgent.__new__(BibleAgent)
    agent._verses_by_key = {}
    agent._en_to_he = {}
    agent._build_lookup_maps()
    return agent


def run_tools_only():
    gold = load_gold(GOLD_PATH)
    structural = [it for it in gold if it.get("structure_check")]
    agent = build_agent_tools_only()

    rows, passed = [], 0
    for it in structural:
        chk = it["structure_check"]
        qt = chk["query_type"]
        result = agent._tool_bible_structure(qt, chk.get("book"))
        # Pick the field that holds the answer for this query_type.
        field = {
            "longest_book": "book",
            "shortest_book": "book",
            "book_count": "answer",
            "total_chapters": "answer",
            "book_chapter_count": "chapters",
            "book_order": "position",
        }[qt]
        actual = result.get(field)
        ok = str(chk["expected"]) == str(actual)
        passed += ok
        rows.append({"id": it["id"], "question": _label(it), "expected": chk["expected"], "actual": actual, "pass": ok})
        print(f"  [{'✓' if ok else '✗'}] {_label(it)} -> {actual} (expected {chk['expected']})")

    summary = {"mode": "tools_only", "subset": "structural", "count": len(rows), "passed": passed,
               "accuracy": round(passed / len(rows), 3) if rows else 0.0}
    print(f"\nStructural tool accuracy: {passed}/{len(rows)} = {summary['accuracy']:.0%}")
    _write(summary, rows)
    return summary


# ------------------------------------------------------------------ full mode
def build_agent_full() -> BibleAgent:
    from src.rag_system import BibleRAG
    rag = BibleRAG()
    return BibleAgent(retriever=rag.retriever, client=rag.generator.client)


def _auto_check(item, res):
    trace = res.get("trace", [])
    tools_used = [s["tool"] for s in trace if s["type"] == "tool_call" and s["tool"]]
    expected_tool = item.get("expected_tool")
    used_expected = (expected_tool in tools_used) if expected_tool else None
    answer = res.get("answer", "")
    needles = item.get("expected_answer_contains", [])
    answer_pass = all(n in answer for n in needles) if needles else None
    fallback = any(s["type"] == "fallback" for s in trace)
    return {
        "tools_used": tools_used,
        "used_expected_tool": used_expected,
        "answer_pass": answer_pass,
        "has_sources": len(res.get("sources", [])) > 0,
        "fallback": fallback,
    }


def run_full(limit=None):
    gold = load_gold(GOLD_PATH)
    if limit:
        gold = gold[:limit]
    agent = build_agent_full()

    rows = []
    by_cat = defaultdict(lambda: {"n": 0, "tool_ok": 0, "answer_ok": 0})
    for idx, it in enumerate(gold):
        print(f"[{idx + 1}/{len(gold)}] {_label(it)}")
        try:
            res = agent.chat(_messages_for(it))
        except Exception as e:
            res = {"answer": f"ERROR: {e}", "sources": [], "trace": []}
        checks = _auto_check(it, res)
        cat = it.get("category", "other")
        by_cat[cat]["n"] += 1
        by_cat[cat]["tool_ok"] += 1 if checks["used_expected_tool"] else 0
        by_cat[cat]["answer_ok"] += 1 if checks["answer_pass"] else 0
        rows.append({"id": it["id"], "category": cat, "question": _label(it),
                     "answer": res["answer"], "sources": res.get("sources", []), **checks})

    summary = {
        "mode": "full",
        "count": len(rows),
        "tool_accuracy": round(sum(r["used_expected_tool"] is True for r in rows) / len(rows), 3) if rows else 0,
        "answer_accuracy": round(sum(r["answer_pass"] is True for r in rows) / len(rows), 3) if rows else 0,
        "by_category": {c: dict(v) for c, v in by_cat.items()},
    }
    print(f"\nTool-selection accuracy: {summary['tool_accuracy']:.0%} | Answer accuracy: {summary['answer_accuracy']:.0%}")
    _write(summary, rows)
    return summary


# --------------------------------------------------------------------- output
def _write(summary, rows):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / "agent_eval.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": rows}, f, ensure_ascii=False, indent=2)

    md = ["# Agent Evaluation Results\n", f"Mode: **{summary['mode']}**\n"]
    if summary["mode"] == "tools_only":
        md.append(f"Structural tool accuracy: **{summary['passed']}/{summary['count']} = {summary['accuracy']:.0%}**\n")
        md.append("| Question | Expected | Actual | Pass |\n|---|---|---|:--:|")
        for r in rows:
            md.append(f"| {r['question']} | {r['expected']} | {r['actual']} | {'✓' if r['pass'] else '✗'} |")
    else:
        md.append(f"- Tool-selection accuracy: **{summary['tool_accuracy']:.0%}**")
        md.append(f"- Answer accuracy: **{summary['answer_accuracy']:.0%}**\n")
        md.append("| Question | Tools used | Expected tool ✓ | Answer ✓ | Sources |\n|---|---|:--:|:--:|:--:|")
        for r in rows:
            md.append(f"| {r['question']} | {', '.join(r['tools_used']) or '—'} | "
                      f"{'✓' if r['used_expected_tool'] else '✗'} | {'✓' if r['answer_pass'] else '✗'} | "
                      f"{'✓' if r['has_sources'] else '—'} |")
    with open(RESULTS_DIR / "agent_eval.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"Saved: {RESULTS_DIR / 'agent_eval.json'} and agent_eval.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the חברותא agent")
    parser.add_argument("--tools-only", action="store_true",
                        help="Deterministic structural-tool eval (no OpenAI / no embeddings).")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if args.tools_only:
        run_tools_only()
    else:
        run_full(args.limit)
