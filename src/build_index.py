import argparse
from pathlib import Path
from src.config import RAW_DIR, CHAPTERS_DIR, ALL_VERSES_JSONL, ALL_CHUNKS_JSONL, CHUNK_STRATEGY, VECTOR_DB_PATH
from src.ingestion import BibleParser
from src.chunking import get_chunker
from src.utils import write_json, append_jsonl
import os

def reset_directories():
    for p in [CHAPTERS_DIR, ALL_VERSES_JSONL, ALL_CHUNKS_JSONL]:
        if p.is_dir():
            import shutil
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default=CHUNK_STRATEGY)
    args = parser.parse_args()

    reset_directories()

    bible_parser = BibleParser()
    chunker = get_chunker(args.strategy)

    raw_files = sorted(RAW_DIR.glob("*.txt"))
    print(f"Found {len(raw_files)} raw files.")

    for raw_file in raw_files:
        print(f"Processing {raw_file.name}...")
        raw_text = bible_parser.read_raw_file(raw_file)
        chapter_data = bible_parser.parse_chapter(raw_text, raw_file.name)

        # Save chapter JSON
        write_json(CHAPTERS_DIR / f"{chapter_data['chapter_id']}.json", chapter_data)

        # Save verses
        for v in chapter_data["verses"]:
            append_jsonl(ALL_VERSES_JSONL, v)

        # Create and save chunks
        chunks = chunker.chunk(chapter_data)
        for chunk in chunks:
            append_jsonl(ALL_CHUNKS_JSONL, chunk)

    print("Ingestion complete. Now building vector index...")
    # build_vector_index() # To be implemented in retrieval.py or here

if __name__ == "__main__":
    main()
