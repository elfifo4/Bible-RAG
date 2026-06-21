"""
Dicta number search — when the user types a PURE NUMBER (digits only), we query
Dicta's Tanakh search engine, which interprets the number as its Hebrew word form
(e.g. 26 -> "עשרים ושש") and returns verses that contain it.

Reverse-engineered from https://search.dicta.org.il/ (its SPA posts to this host):
  POST https://tanach-search-3-4c.loadbalancer.dicta.org.il/search
  body: {"query": "<number>", "from": 0, "size": N}
  resp: {"total": <int>, "hits": [{hebrewPath, englishPath, xmlId,
                                    highlight:[{text}], ...}]}

We collect `total` and each hit's reference (from hebrewPath) + verse text
(from highlight[].text). Stdlib only — no extra dependency.
"""

import json
import re
import urllib.request
import urllib.error
from typing import Any, Dict, List

DICTA_SEARCH_URL = "https://tanach-search-3-4c.loadbalancer.dicta.org.il/search"
_TIMEOUT = 8  # seconds


def _parse_hebrew_path(path: str) -> str:
    """'תנ"ך/נביאים/ספר מלכים א/פרק טז/פסוק ח' -> 'מלכים א טז:ח'."""
    book = chapter = verse = ""
    for seg in path.split("/"):
        seg = seg.strip()
        if seg.startswith("ספר "):
            book = seg[len("ספר "):].strip()
        elif seg.startswith("פרק "):
            chapter = seg[len("פרק "):].strip()
        elif seg.startswith("פסוק "):
            verse = seg[len("פסוק "):].strip()
    if book and chapter and verse:
        return f"{book} {chapter}:{verse}"
    if book and chapter:
        return f"{book} {chapter}"
    return book or path


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def search_number(number: str, size: int = 5) -> Dict[str, Any]:
    """
    Query Dicta for verses containing `number` (spelled out in Hebrew).
    Returns {number, total, results:[{ref, path_he, xml_id, text}], error?}.
    """
    number = str(number).strip()
    payload = json.dumps({"query": number, "from": 0, "size": size}).encode("utf-8")
    req = urllib.request.Request(
        DICTA_SEARCH_URL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Bible-RAG/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as e:
        return {"number": number, "total": 0, "results": [], "error": str(e)}

    results: List[Dict[str, Any]] = []
    for hit in data.get("hits", []):
        highlight = hit.get("highlight") or []
        text = _strip_tags(highlight[0]["text"]) if highlight else ""
        results.append({
            "ref": _parse_hebrew_path(hit.get("hebrewPath", "")),
            "path_he": hit.get("hebrewPath", ""),
            "xml_id": hit.get("xmlId", ""),
            "text": text,
        })
    return {"number": number, "total": int(data.get("total", 0)), "results": results}


if __name__ == "__main__":
    import sys
    n = sys.argv[1] if len(sys.argv) > 1 else "26"
    res = search_number(n)
    print(f"number={res['number']} total={res['total']}")
    for r in res["results"]:
        print(f"  {r['ref']}: {r['text'][:70]}")
