import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .schemas import (
    AskRequest, AskResponse, LoginRequest, Token, ConfigResponse,
    CompareRequest, CompareResponse, EvalSummaryResponse, EvalQuestionsResponse,
    EvalAnswersResponse, ChatRequest, ChatResponse
)
from .auth import create_access_token, get_current_user, verify_password
import time
import json
from pathlib import Path
from src.rag_system import BibleRAG
from src.agent import BibleAgent
from src.config import TOP_K, CHUNK_STRATEGY, PROJECT_ROOT

# Evaluation Results Path
EVAL_RESULTS_DIR = PROJECT_ROOT / "eval" / "results"

# Global instance
rag_app = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the RAG system once at startup
    print("Loading Bible RAG system...")
    rag = BibleRAG()
    rag_app["rag"] = rag
    # Build the agent ON TOP of the already-loaded retriever + client
    # (reuse — do NOT reload the embedding model or FAISS index).
    print("Initializing agent (חברותא)...")
    rag_app["agent"] = BibleAgent(retriever=rag.retriever, client=rag.generator.client)
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
    rag_loaded = "rag" in rag_app
    return {
        "status": "ok",
        "rag_engine": "initialized" if rag_loaded else "loading",
        "index_ready": rag_app["rag"].retriever.index is not None if rag_loaded else False
    }

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

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user_id: str = Depends(get_current_user)):
    try:
        agent: BibleAgent = rag_app["agent"]
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        result = agent.chat(messages, strategy_hint=request.strategy)
        return result
    except Exception as e:
        print(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/eval/summary", response_model=EvalSummaryResponse)
async def get_eval_summary(user_id: str = Depends(get_current_user)):
    strategies = ["hybrid", "dense_only", "lexical_only"]
    summary = {}
    
    for strategy in strategies:
        file_path = EVAL_RESULTS_DIR / f"retrieval_eval_{strategy}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                summary[strategy] = {
                    "strategy": strategy,
                    "questions_count": data["summary"]["questions_count"],
                    "hit_at_1": data["summary"]["hit@1"],
                    "hit_at_3": data["summary"]["hit@3"],
                    "hit_at_5": data["summary"]["hit@5"],
                    "recall_at_5": data["summary"]["recall@5"],
                    "mrr": data["summary"]["mrr"]
                }
    
    if not summary:
        raise HTTPException(
            status_code=404, 
            detail="No evaluation results found. Please run 'python eval/run_eval.py' first."
        )
    
    return {"strategies": summary}

@app.get("/api/eval/questions", response_model=EvalQuestionsResponse)
async def get_eval_questions(strategy: str = "hybrid", user_id: str = Depends(get_current_user)):
    file_path = EVAL_RESULTS_DIR / f"retrieval_eval_{strategy}.json"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Evaluation results for {strategy} not found."
        )
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        results = []
        for r in data["detailed_results"]:
            results.append({
                "question": r["question"],
                "strategy": strategy,
                "relevant_found": r["relevant_found"],
                "first_relevant_rank": r.get("first_relevant_rank"),
                "hit_at_1": r.get("hit@1", False),
                "hit_at_3": r.get("hit@3", False),
                "hit_at_5": r.get("hit@5", False),
                "recall_at_5": r.get("recall@5", 0.0),
                "mrr": r.get("mrr", 0.0),
                "retrieved_refs": r["retrieved_refs"],
                "expected": None # We could load from gold_set if needed
            })
        return {"results": results}

@app.get("/api/eval/answers", response_model=EvalAnswersResponse)
async def get_eval_answers(strategy: str = "hybrid", user_id: str = Depends(get_current_user)):
    file_path = EVAL_RESULTS_DIR / f"answer_eval_{strategy}.json"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Answer evaluation results for {strategy} not found. Run eval with --include-generation."
        )
        
    with open(file_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
        return {"results": results}

@app.get("/api/eval/ablation")
async def get_eval_ablation(user_id: str = Depends(get_current_user)):
    file_path = EVAL_RESULTS_DIR / "ablation_results.json"
    
    if not file_path.exists():
        return {
            "available": False,
            "message": "Ablation results not found. Run 'python eval/run_eval.py --ablation' first."
        }
        
    with open(file_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
        return {
            "available": True,
            "results": results
        }

@app.get("/api/eval/errors")
async def get_eval_errors(user_id: str = Depends(get_current_user)):
    file_path = EVAL_RESULTS_DIR / "error_analysis.json"
    
    if not file_path.exists():
        return {
            "available": False,
            "message": "Error analysis results not found. Run 'python eval/error_analysis.py' first."
        }
        
    with open(file_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
        return {
            "available": True,
            "results": results
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
