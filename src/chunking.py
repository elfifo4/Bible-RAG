from abc import ABC, abstractmethod
from typing import List, Dict

class ChunkStrategy(ABC):
    @abstractmethod
    def chunk(self, chapter_data: Dict) -> List[Dict]:
        pass

class SingleVerseChunker(ChunkStrategy):
    def chunk(self, chapter_data: Dict) -> List[Dict]:
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
                    "verse": v["verse"],
                    "ref": v["ref"],
                    "ref_en": v["ref_en"],
                    "chunk_type": "single_verse"
                }
            })
        return chunks

class SlidingWindowChunker(ChunkStrategy):
    def __init__(self, window_size: int = 3, step: int = 1):
        self.window_size = window_size
        self.step = step

    def chunk(self, chapter_data: Dict) -> List[Dict]:
        verses = chapter_data["verses"]
        chunks = []
        for i in range(0, len(verses), self.step):
            window = verses[i:i + self.window_size]
            if not window: break

            chunk_text = " ".join([v["text_plain"] for v in window])
            display_text = " ".join([v["text_original"] for v in window])

            v_start = window[0]
            v_end = window[-1]

            chunks.append({
                "chunk_id": f"{v_start['verse_id']}_{v_end['verse']}",
                "doc_id": chapter_data["chapter_id"],
                "text": chunk_text,
                "display_text": display_text,
                "metadata": {
                    "book": v_start["book"],
                    "book_en": v_start["book_en"],
                    "chapter": v_start["chapter"],
                    "verse_start": v_start["verse"],
                    "verse_end": v_end["verse"],
                    "ref": f"{v_start['ref']}-{v_end['verse']}",
                    "chunk_type": "sliding_window"
                }
            })
            if i + self.window_size >= len(verses): break
        return chunks

def get_chunker(strategy_name: str) -> ChunkStrategy:
    if strategy_name == "single_verse":
        return SingleVerseChunker()
    elif strategy_name == "sliding_window":
        return SlidingWindowChunker()
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")
