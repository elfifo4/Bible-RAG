import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .schemas import AskRequest, AskResponse, LoginRequest, Token, ConfigResponse, CompareRequest, CompareResponse
from .auth import create_access_token, get_current_user, verify_password
import time
from src.rag_system import BibleRAG
from src.config import TOP_K, CHUNK_STRATEGY

# Global instance
rag_app = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the RAG system once at startup
    print("Loading Bible RAG system...")
    rag_app["rag"] = BibleRAG()
    yield
    # Clean up if needed
    rag_app.clear()

app = FastAPI(title="Bible RAG API", lifespan=lifespan)

# CORS configuration
# Note: allow_origins=["*"] cannot be used with allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https?://.*", # Robustly allow all origins for dev/debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/login", response_model=Token)
async def login(request: LoginRequest):
    if not verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": "demo-user"})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/config", response_model=ConfigResponse)
async def get_config(user_id: str = Depends(get_current_user)):
    return {
        "available_chunk_strategies": ["single_verse", "sliding_window"],
        "default_top_k": TOP_K,
        "supported_languages": ["he", "en"]
    }

@app.post("/api/ask", response_model=AskResponse)
async def ask(request: AskRequest, user_id: str = Depends(get_current_user)):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        rag: BibleRAG = rag_app["rag"]
        result = rag.answer(
            question=request.question, 
            top_k=request.top_k,
            retrieval_strategy=str(request.retrieval_strategy)
        )

        # In a real app, you might want to filter debug info based on request.debug
        if not request.debug:
            result.pop("debug", None)

        return result
    except Exception as e:
        print(f"Error in ask: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare", response_model=CompareResponse)
async def compare(request: CompareRequest, user_id: str = Depends(get_current_user)):
    start_time = time.time()
    results = {}
    
    try:
        rag: BibleRAG = rag_app["rag"]
        for strategy in request.strategies:
            # We run each strategy. To save time/cost in a real scenario, 
            # we might only do the retrieval part, but the user wants "three answer columns".
            results[strategy] = rag.answer(
                question=request.question,
                top_k=request.top_k,
                retrieval_strategy=str(strategy)
            )
        
        return {
            "question": request.question,
            "results": results,
            "total_latency_ms": int((time.time() - start_time) * 1000)
        }
    except Exception as e:
        print(f"Error in compare: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
