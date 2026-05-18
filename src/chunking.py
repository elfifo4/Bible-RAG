from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .config import WINDOW_SIZE, WINDOW_OVERLAP

class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, chapter_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

class SingleVerseChunker(BaseChunker):
    def chunk(self, chapter_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunks = []
        for v in chapter_data["verses"]:
            chunks.append({
                "chunk_id": v["verse_id"],
                "doc_id": chapter_data["chapter_id"],
                "text": v["text_plain"],
                "display_text": v["text_original"],
                "metadata": {
                    "book": v["book"],
                    "book_en": v["book_en"],
                    "chapter": v["chapter"],
                    "verse_start": v["verse"],
                    "verse_end": v["verse"],
                    "ref": v["ref"],
                    "ref_en": v["ref_en"],
                    "chunk_type": "single_verse"
                }
            })
        return chunks

class SlidingWindowChunker(BaseChunker):
    def __init__(self, window_size: int = WINDOW_SIZE, overlap: int = WINDOW_OVERLAP):
        self.window_size = window_size
        self.overlap = overlap

    def chunk(self, chapter_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        verses = chapter_data["verses"]
        chunks = []

        if not verses:
            return []

        step = max(1, self.window_size - self.overlap)

        for i in range(0, len(verses), step):
            window = verses[i : i + self.window_size]
            if not window:
                break

            # Combine plain text for search and original for display
            chunk_text = " ".join([v["text_plain"] for v in window])
            display_text = " ".join([v["text_original"] for v in window])

            v_start = window[0]
            v_end = window[-1]

            # Create a combined reference
            if v_start["verse"] == v_end["verse"]:
                ref = v_start["ref"]
                ref_en = v_start["ref_en"]
            else:
                # Assuming ref is like "בראשית א:א"
                ref_prefix = v_start["ref"].split(":")[0]
                start_v_label = v_start["ref"].split(":")[1]
                end_v_label = v_end["ref"].split(":")[1]
                ref = f"{ref_prefix}:{start_v_label}-{end_v_label}"

                ref_en_prefix = v_start["ref_en"].split(":")[0]
                ref_en = f"{ref_en_prefix}:{v_start['verse']}-{v_end['verse']}"

            chunks.append({
                "chunk_id": f"{v_start['verse_id']}_w{self.window_size}",
                "doc_id": chapter_data["chapter_id"],
                "text": chunk_text,
                "display_text": display_text,
                "metadata": {
                    "book": v_start["book"],
                    "book_en": v_start["book_en"],
                    "chapter": v_start["chapter"],
                    "verse_start": v_start["verse"],
                    "verse_end": v_end["verse"],
                    "ref": ref,
                    "ref_en": ref_en,
                    "chunk_type": "sliding_window",
                    "window_size": len(window)
                }
            })

            # Exit if we've processed the end of the verses
            if i + self.window_size >= len(verses):
                break

        return chunks

def get_chunker(strategy_name: str) -> BaseChunker:
    if strategy_name == "single_verse":
        return SingleVerseChunker()
    elif strategy_name == "sliding_window":
        return SlidingWindowChunker()
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")
