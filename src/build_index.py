import argparse
from pathlib import Path
from src.config import (
    RAW_DIR,
    CHAPTERS_DIR,
    ALL_VERSES_JSONL,
    ALL_CHUNKS_JSONL,
    CHUNK_STRATEGY
)
from src.ingestion import BibleParser
from src.chunking import get_chunker
from src.utils import write_json, append_jsonl, logger, timer
from src.retrieval import VectorRetriever
import os
import shutil

def reset_directories():
    logger.info("Resetting output directories...")
    for p in [CHAPTERS_DIR, ALL_VERSES_JSONL, ALL_CHUNKS_JSONL]:
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

@timer
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default=CHUNK_STRATEGY, help="Chunking strategy (single_verse, sliding_window)")
    args = parser.parse_args()

    reset_directories()

    bible_parser = BibleParser()
    chunker = get_chunker(args.strategy)

    raw_files = sorted(RAW_DIR.glob("*.txt"))
    if not raw_files:
        logger.error(f"No raw files found in {RAW_DIR}")
        return

    logger.info(f"Found {len(raw_files)} raw files. Using strategy: {args.strategy}")

    total_chunks = 0
    for raw_file in raw_files:
        logger.debug(f"Parsing {raw_file.name}...")
        try:
            raw_text = bible_parser.read_raw_file(raw_file)
            chapter_data = bible_parser.parse_chapter(raw_text, raw_file.name)

            # Save chapter JSON
            write_json(CHAPTERS_DIR / f"{chapter_data['chapter_id']}.json", chapter_data)

            # Save individual verses
            for v in chapter_data["verses"]:
                append_jsonl(ALL_VERSES_JSONL, v)

            # Create and save chunks using the selected strategy
            chunks = chunker.chunk(chapter_data)
            for chunk in chunks:
                append_jsonl(ALL_CHUNKS_JSONL, chunk)

            total_chunks += len(chunks)
        except Exception as e:
            logger.error(f"Error processing {raw_file.name}: {e}")

    logger.info(f"Ingestion complete. Total chunks created: {total_chunks}")

    logger.info("Building vector index...")
    retriever = VectorRetriever()
    retriever.build_index()

    logger.info("Pipeline complete.")

if __name__ == "__main__":
    main()
