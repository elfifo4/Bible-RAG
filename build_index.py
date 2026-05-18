import json
import re
import unicodedata
from pathlib import Path


RAW_DIR = Path("./raw")
OUTPUT_DIR = Path("./processed")
CHAPTERS_DIR = OUTPUT_DIR / "chapters"

ALL_VERSES_JSONL = OUTPUT_DIR / "all_verses.jsonl"
ALL_CHUNKS_JSONL = OUTPUT_DIR / "all_chunks.jsonl"


BIBLE_CATALOG = [
    {"hebrew": "בראשית", "trans": "bereshit", "english": "Genesis", "number_of_chapters": 50},
    {"hebrew": "שמות", "trans": "shemot", "english": "Exodus", "number_of_chapters": 40},
    {"hebrew": "ויקרא", "trans": "vayikra", "english": "Leviticus", "number_of_chapters": 27},
    {"hebrew": "במדבר", "trans": "bamidbar", "english": "Numbers", "number_of_chapters": 36},
    {"hebrew": "דברים", "trans": "devarim", "english": "Deuteronomy", "number_of_chapters": 34},
    {"hebrew": "יהושע", "trans": "yehoshua", "english": "Joshua", "number_of_chapters": 24},
    {"hebrew": "שופטים", "trans": "shoftim", "english": "Judges", "number_of_chapters": 21},
    {"hebrew": "שמואל א", "trans": "shemuel_a", "english": "1 Samuel", "number_of_chapters": 31},
    {"hebrew": "שמואל ב", "trans": "shemuel_b", "english": "2 Samuel", "number_of_chapters": 24},
    {"hebrew": "מלכים א", "trans": "melachim_a", "english": "1 Kings", "number_of_chapters": 22},
    {"hebrew": "מלכים ב", "trans": "melachim_b", "english": "2 Kings", "number_of_chapters": 25},
    {"hebrew": "ישעיהו", "trans": "yeshaaya", "english": "Isaiah", "number_of_chapters": 66},
    {"hebrew": "ירמיהו", "trans": "yirmeyah", "english": "Jeremiah", "number_of_chapters": 52},
    {"hebrew": "יחזקאל", "trans": "yechezkel", "english": "Ezekiel", "number_of_chapters": 48},
    {"hebrew": "הושע", "trans": "hoshea", "english": "Hosea", "number_of_chapters": 14},
    {"hebrew": "יואל", "trans": "yoel", "english": "Joel", "number_of_chapters": 4},
    {"hebrew": "עמוס", "trans": "amos", "english": "Amos", "number_of_chapters": 9},
    {"hebrew": "עובדיה", "trans": "ovadia", "english": "Obadiah", "number_of_chapters": 1},
    {"hebrew": "יונה", "trans": "yona", "english": "Jonah", "number_of_chapters": 4},
    {"hebrew": "מיכה", "trans": "micha", "english": "Micah", "number_of_chapters": 7},
    {"hebrew": "נחום", "trans": "nachum", "english": "Nahum", "number_of_chapters": 3},
    {"hebrew": "חבקוק", "trans": "havakuk", "english": "Habakkuk", "number_of_chapters": 3},
    {"hebrew": "צפניה", "trans": "tzefania", "english": "Zephaniah", "number_of_chapters": 3},
    {"hebrew": "חגי", "trans": "haggai", "english": "Haggai", "number_of_chapters": 2},
    {"hebrew": "זכריה", "trans": "zecharia", "english": "Zechariah", "number_of_chapters": 14},
    {"hebrew": "מלאכי", "trans": "malachi", "english": "Malachi", "number_of_chapters": 3},
    {"hebrew": "תהילים", "trans": "tehilim", "english": "Psalms", "number_of_chapters": 150},
    {"hebrew": "משלי", "trans": "mishley", "english": "Proverbs", "number_of_chapters": 31},
    {"hebrew": "איוב", "trans": "iyov", "english": "Job", "number_of_chapters": 42},
    {"hebrew": "שיר השירים", "trans": "shir_hashirim", "english": "Song of Songs", "number_of_chapters": 8},
    {"hebrew": "רות", "trans": "ruth", "english": "Ruth", "number_of_chapters": 4},
    {"hebrew": "איכה", "trans": "eicha", "english": "Lamentations", "number_of_chapters": 5},
    {"hebrew": "קהלת", "trans": "koheleth", "english": "Ecclesiastes", "number_of_chapters": 12},
    {"hebrew": "אסתר", "trans": "ester", "english": "Esther", "number_of_chapters": 10},
    {"hebrew": "דניאל", "trans": "daniel", "english": "Daniel", "number_of_chapters": 12},
    {"hebrew": "עזרא", "trans": "ezra", "english": "Ezra", "number_of_chapters": 10},
    {"hebrew": "נחמיה", "trans": "nechemia", "english": "Nehemiah", "number_of_chapters": 13},
    {"hebrew": "דברי הימים א", "trans": "divrei_hayamim_a", "english": "1 Chronicles", "number_of_chapters": 29},
    {"hebrew": "דברי הימים ב", "trans": "divrei_hayamim_b", "english": "2 Chronicles", "number_of_chapters": 36},
]

BOOK_MAPPING = {
    book["hebrew"]: {
        "en": book["english"],
        "slug": book["trans"],
        "number_of_chapters": book["number_of_chapters"],
    }
    for book in BIBLE_CATALOG
}


def read_raw_file(path: Path) -> str:
    data = path.read_bytes()

    if data.startswith(b"\xfe\xff"):
        return data[2:].decode("utf-16-be")

    if data.startswith(b"\xff\xfe"):
        return data[2:].decode("utf-16-le")

    return data.decode("utf-8")


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def remove_cantillation(text: str) -> str:
    result = []

    for char in unicodedata.normalize("NFD", text):
        code = ord(char)

        # Hebrew cantillation marks.
        if 0x0591 <= code <= 0x05AF:
            continue

        # METEG / GAAYA.
        if code == 0x05BD:
            continue

        result.append(char)

    return unicodedata.normalize("NFC", "".join(result))


def remove_niqqud(text: str) -> str:
    result = []

    for char in unicodedata.normalize("NFD", text):
        code = ord(char)

        # Hebrew niqqud.
        if 0x05B0 <= code <= 0x05BC:
            continue

        # Shin/sin dot and qamats qatan.
        if code in (0x05C1, 0x05C2, 0x05C7):
            continue

        result.append(char)

    return unicodedata.normalize("NFC", "".join(result))


def clean_text(text: str) -> str:
    text = re.sub(r"[׃:]", "", text)
    text = text.replace("־", " ")
    text = text.replace("׀", " ")
    return normalize_spaces(text)


def remove_markers(text: str) -> str:
    return normalize_spaces(re.sub(r"\{[^}]+}", "", text))


def extract_markers(text: str) -> list[str]:
    return re.findall(r"\{([^}]+)}", text)


def ahadot(num: int) -> str:
    return {
        1: "א",
        2: "ב",
        3: "ג",
        4: "ד",
        5: "ה",
        6: "ו",
        7: "ז",
        8: "ח",
        9: "ט",
    }.get(num % 10, "")


def asarot(num: int) -> str:
    return {
        1: "י",
        2: "כ",
        3: "ל",
        4: "מ",
        5: "נ",
        6: "ס",
        7: "ע",
        8: "פ",
        9: "צ",
    }.get((num % 100) // 10, "")


def meot(num: int) -> str:
    return {
        1: "ק",
        2: "ר",
        3: "ש",
        4: "ת",
    }.get(num // 100, "")


def to_otiot(num: int) -> str:
    result = meot(num) + asarot(num) + ahadot(num)

    if num % 100 == 15:
        return meot(num) + "טו"

    if num % 100 == 16:
        return meot(num) + "טז"

    return result


def otiot_to_number(value: str) -> int:
    for number in range(1, 500):
        if to_otiot(number) == value:
            return number

    raise ValueError(f"Unsupported Hebrew number: {value}")


def verse_label(num: int) -> str:
    return to_otiot(num)


def parse_title(title_line: str) -> tuple[str, int]:
    match = re.match(r"(.+?)\s+פרק\s+(.+)", title_line.strip())

    if not match:
        raise ValueError(f"Could not parse title line: {title_line}")

    book = match.group(1).strip()
    chapter_he = match.group(2).strip()
    chapter = otiot_to_number(chapter_he)

    return book, chapter


def get_book_info(book: str) -> dict:
    book_info = BOOK_MAPPING.get(book)

    if book_info is None:
        raise ValueError(f"Unknown book: {book}")

    return book_info


def parse_chapter(raw_text: str, source_file: str) -> dict:
    lines = [
        line.strip()
        for line in raw_text.splitlines()
        if line.strip()
    ]

    if not lines:
        raise ValueError(f"Empty file: {source_file}")

    title_line = lines[0]
    body = "\n".join(lines[1:]).strip()

    book, chapter = parse_title(title_line)
    book_info = get_book_info(book)

    verses = []
    cursor = 0
    current_verse = 1

    while current_verse <= 200:
        current_label = verse_label(current_verse)

        current_match = re.search(
            rf"(?<!\S){re.escape(current_label)}(?!\S)",
            body[cursor:],
        )

        if not current_match:
            break

        current_start = cursor + current_match.start()
        text_start = cursor + current_match.end()

        before_text = body[cursor:current_start]
        markers_before = extract_markers(before_text)

        next_verse = current_verse + 1
        next_label = verse_label(next_verse)

        next_match = re.search(
            rf"(?<!\S){re.escape(next_label)}(?!\S)",
            body[text_start:],
        )

        text_end = (
            text_start + next_match.start()
            if next_match
            else len(body)
        )

        verse_text_with_markers = body[text_start:text_end].strip()

        markers_after = extract_markers(verse_text_with_markers)

        text_original = remove_markers(verse_text_with_markers)
        text_with_niqqud = clean_text(remove_cantillation(text_original))
        text_plain = clean_text(remove_niqqud(text_with_niqqud))

        verse_id = (
            f"{book_info['slug']}_"
            f"{chapter:03d}_"
            f"{current_verse:03d}"
        )

        verses.append(
            {
                "verse_id": verse_id,
                "book": book,
                "book_en": book_info["en"],
                "book_slug": book_info["slug"],
                "chapter": chapter,
                "verse": current_verse,
                "ref": (
                    f"{book} "
                    f"{to_otiot(chapter)}:"
                    f"{to_otiot(current_verse)}"
                ),
                "ref_en": (
                    f"{book_info['en']} "
                    f"{chapter}:"
                    f"{current_verse}"
                ),
                "text_original": text_original,
                "text_with_niqqud": text_with_niqqud,
                "text_plain": text_plain,
                "markers": {
                    "before": markers_before,
                    "after": markers_after,
                },
                "source_file": source_file,
            }
        )

        cursor = text_end
        current_verse += 1

    return {
        "book": book,
        "book_en": book_info["en"],
        "book_slug": book_info["slug"],
        "chapter": chapter,
        "chapter_id": f"{book_info['slug']}_{chapter:03d}",
        "ref": f"{book} {to_otiot(chapter)}",
        "ref_en": f"{book_info['en']} {chapter}",
        "source_file": source_file,
        "verses": verses,
    }


def build_single_verse_chunks(chapter_data: dict) -> list[dict]:
    chunks = []

    for verse in chapter_data["verses"]:
        chunks.append(
            {
                "chunk_id": verse["verse_id"],
                "doc_id": chapter_data["chapter_id"],
                "text": verse["text_plain"],
                "display_text": verse["text_original"],
                "metadata": {
                    "book": verse["book"],
                    "book_en": verse["book_en"],
                    "book_slug": verse["book_slug"],
                    "chapter": verse["chapter"],
                    "verse_start": verse["verse"],
                    "verse_end": verse["verse"],
                    "ref": verse["ref"],
                    "ref_en": verse["ref_en"],
                    "markers_before": verse["markers"]["before"],
                    "markers_after": verse["markers"]["after"],
                    "source_file": verse["source_file"],
                    "chunk_type": "single_verse",
                },
            }
        )

    return chunks


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def append_jsonl(path: Path, item: dict) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                item,
                ensure_ascii=False,
            )
            + "\n"
        )


def reset_outputs() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    CHAPTERS_DIR.mkdir(exist_ok=True)

    if ALL_VERSES_JSONL.exists():
        ALL_VERSES_JSONL.unlink()

    if ALL_CHUNKS_JSONL.exists():
        ALL_CHUNKS_JSONL.unlink()


def process_file(raw_file: Path) -> tuple[dict, list[dict]]:
    raw_text = read_raw_file(raw_file)

    chapter_data = parse_chapter(
        raw_text=raw_text,
        source_file=raw_file.name,
    )

    chunks = build_single_verse_chunks(chapter_data)

    chapter_path = (
        CHAPTERS_DIR
        / f"{chapter_data['chapter_id']}.json"
    )

    write_json(chapter_path, chapter_data)

    for verse in chapter_data["verses"]:
        append_jsonl(ALL_VERSES_JSONL, verse)

    for chunk in chunks:
        append_jsonl(ALL_CHUNKS_JSONL, chunk)

    return chapter_data, chunks


def main() -> None:
    reset_outputs()

    raw_files = sorted(RAW_DIR.glob("*.txt"))

    if not raw_files:
        raise FileNotFoundError(
            f"No .txt files found under: {RAW_DIR}"
        )

    total_chapters = 0
    total_verses = 0
    total_chunks = 0

    for raw_file in raw_files:
        print(f"Processing: {raw_file}")

        chapter_data, chunks = process_file(raw_file)

        total_chapters += 1
        total_verses += len(chapter_data["verses"])
        total_chunks += len(chunks)

        print(
            f"  Parsed {chapter_data['ref']} "
            f"({chapter_data['ref_en']}): "
            f"{len(chapter_data['verses'])} verses"
        )

    print()
    print("Done.")
    print(f"Chapters: {total_chapters}")
    print(f"Verses: {total_verses}")
    print(f"Chunks: {total_chunks}")
    print(f"Wrote chapters to: {CHAPTERS_DIR}")
    print(f"Wrote verses to: {ALL_VERSES_JSONL}")
    print(f"Wrote chunks to: {ALL_CHUNKS_JSONL}")


if __name__ == "__main__":
    main()