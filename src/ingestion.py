import re
from pathlib import Path
from .utils import HebrewProcessor, Gematria
from .constants import BOOK_MAPPING

class BibleParser:
    def __init__(self):
        self.processor = HebrewProcessor()
        self.gematria = Gematria()

    def read_raw_file(self, path: Path) -> str:
        data = path.read_bytes()
        if data.startswith(b"\xfe\xff"): return data[2:].decode("utf-16-be")
        if data.startswith(b"\xff\xfe"): return data[2:].decode("utf-16-le")
        return data.decode("utf-8")

    def parse_title(self, title_line: str) -> tuple[str, int]:
        match = re.match(r"(.+?)\s+פרק\s+(.+)", title_line.strip())
        if not match: raise ValueError(f"Could not parse title line: {title_line}")
        book = match.group(1).strip()
        chapter_he = match.group(2).strip()
        chapter = self.gematria.otiot_to_number(chapter_he)
        return book, chapter

    def parse_chapter(self, raw_text: str, source_file: str) -> dict:
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        if not lines: raise ValueError(f"Empty file: {source_file}")

        book_name, chapter_num = self.parse_title(lines[0])
        body = "\n".join(lines[1:]).strip()
        book_info = BOOK_MAPPING.get(book_name)
        if not book_info: raise ValueError(f"Unknown book: {book_name}")

        verses = []
        cursor = 0
        current_v = 1

        while True:
            label = self.gematria.to_otiot(current_v)
            match = re.search(rf"(?<!\S){re.escape(label)}(?!\S)", body[cursor:])
            if not match: break

            start_pos = cursor + match.start()
            text_start = cursor + match.end()

            markers_before = re.findall(r"\{([^}]+)}", body[cursor:start_pos])

            next_label = self.gematria.to_otiot(current_v + 1)
            next_match = re.search(rf"(?<!\S){re.escape(next_label)}(?!\S)", body[text_start:])
            end_pos = text_start + next_match.start() if next_match else len(body)

            verse_raw = body[text_start:end_pos].strip()
            markers_after = re.findall(r"\{([^}]+)}", verse_raw)

            text_orig = re.sub(r"\{[^}]+}", "", verse_raw).strip()
            text_niqqud = self.processor.clean_text(self.processor.remove_cantillation(text_orig))
            text_plain = self.processor.clean_text(self.processor.remove_niqqud(text_niqqud))

            verses.append({
                "verse_id": f"_{book_info['index']:02d}_{book_info['slug']}_{chapter_num:03d}_{current_v:03d}",
                "book": book_name,
                "book_en": book_info["en"],
                "chapter": chapter_num,
                "verse": current_v,
                "ref": f"{book_name} {self.gematria.to_otiot(chapter_num)}:{label}",
                "ref_en": f"{book_info['en']} {chapter_num}:{current_v}",
                "text_original": text_orig,
                "text_with_niqqud": text_niqqud,
                "text_plain": text_plain,
                "markers": {"before": markers_before, "after": markers_after},
                "source_file": source_file
            })
            cursor = end_pos
            current_v += 1

        return {
            "book": book_name,
            "book_en": book_info["en"],
            "chapter": chapter_num,
            "chapter_id": f"_{book_info['index']:02d}_{book_info['slug']}_{chapter_num:03d}",
            "ref": f"{book_name} {self.gematria.to_otiot(chapter_num)}",
            "verses": verses,
            "source_file": source_file
        }
