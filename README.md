# Bible-RAG

A Retrieval-Augmented Generation system for the Hebrew Bible (Tanakh).

## Project Structure

- `data/`: Contains raw texts, processed JSONs, and the vector index.
- `src/`: Core logic.
    - `ingestion.py`: Parses raw biblical texts.
    - `chunking.py`: Strategies for splitting text (Verse-level, Sliding Window).
    - `retrieval.py`: Vector search using FAISS and Hebrew-optimized embeddings.
    - `generation.py`: LLM prompt engineering and citation handling.
    - `rag_system.py`: Main entry point.
- `eval/`: Evaluation scripts and gold standard sets.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Build the index:
   ```bash
   python -m src.build_index
   ```

3. Run the RAG system:
   ```bash
   python -m src.rag_system
   ```

## Design Principles

- **Separation of Concerns**: Ingestion, Chunking, Retrieval, and Generation are decoupled.
- **Reproducibility**: Configuration is centralized in `src/config.py`.
- **Extensibility**: Easily add new chunking strategies or embedding models.
- **Citation-Aware**: Every answer is backed by specific biblical references.
