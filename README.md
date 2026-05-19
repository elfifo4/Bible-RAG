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
- `backend/`: FastAPI web server with JWT authentication.
- `frontend/`: React + Vite web interface (RTL support).
- `eval/`: Evaluation scripts and gold standard sets.

## Getting Started

### 1. Installation
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OpenAI API Key and desired password
```

### 2. Build the Index
```bash
python3 -m src.build_index
```

### 3. Run the Web App

**Backend:**
```bash
uvicorn backend.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to ask questions!

## Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key.
- `APP_AUTH_PASSWORD`: The password required to log in to the web app.
- `JWT_SECRET`: A secret string for signing authentication tokens.
- `ALLOWED_ORIGINS`: Comma-separated list of origins for CORS.

## Deployment
1. **Backend**: Deploy the Docker container to Render, Fly.io, or Railway. Set environment variables in their dashboards.
2. **Frontend**: Deploy the `dist` folder to Vercel or Netlify. Set `VITE_API_URL` to your backend URL.

## Design Principles

- **Separation of Concerns**: Ingestion, Chunking, Retrieval, and Generation are decoupled.
- **Reproducibility**: Configuration is centralized in `src/config.py`.
- **Security**: OpenAI key is hidden on the backend; JWT authentication protects the API.
- **Citation-Aware**: Every answer is backed by specific biblical references.
