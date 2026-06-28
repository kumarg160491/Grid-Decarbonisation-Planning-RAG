# api.py
import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from ingest import ingest_single, ingest_all
from rag_chain import run_query, run_report, run_feeder, get_collection_stats
from config import cfg

app = FastAPI(
    title      = "Grid Decarbonisation Planning RAG API",
    description= "RAG API for grid decarbonisation planning powered by LangChain + Ollama",
    version    = "1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins    = ["*"],
    allow_methods    = ["*"],
    allow_headers    = ["*"],
)


# -- Request Models -----------------------------------------------------------

class QueryRequest(BaseModel):
    question       : str
    category_filter: Optional[str] = None


class ReportRequest(BaseModel):
    planning_request: str
    category_filter : Optional[str] = None


class FeederRequest(BaseModel):
    feeder_id      : str
    load_type      : str
    capacity_kw    : float
    voltage_level  : str
    category_filter: Optional[str] = None


# -- Health Check -------------------------------------------------------------

@app.get("/api/health")
def health_check():
    import requests as req
    try:
        resp   = req.get(f"{cfg.ollama.base_url}/api/tags", timeout=3)
        ollama = "running" if resp.status_code == 200 else "unreachable"
    except Exception:
        ollama = "unreachable"

    stats = get_collection_stats()
    return {
        "status"      : "ok",
        "ollama"      : ollama,
        "llm_model"   : cfg.ollama.model,
        "embed_model" : cfg.ollama.embedding,
        "chromadb"    : "connected",
        "total_chunks": stats["total_chunks"],
    }


# -- Categories ---------------------------------------------------------------

@app.get("/api/categories")
def get_categories():
    return {"categories": list(cfg.categories)}


# -- Documents ----------------------------------------------------------------

@app.get("/api/documents")
def list_documents():
    stats = get_collection_stats()
    return {
        "total_chunks"   : stats["total_chunks"],
        "category_counts": stats["category_counts"],
    }


# -- Ingest -------------------------------------------------------------------

@app.post("/api/ingest")
async def ingest_document(
    file    : UploadFile = File(...),
    category: str        = Form(...)
):
    if category not in cfg.categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Choose from: {list(cfg.categories)}"
        )

    category_dir = os.path.join("data", category)
    os.makedirs(category_dir, exist_ok=True)

    filepath = os.path.join(category_dir, file.filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    chunks_stored = ingest_single(filepath, category)

    return {
        "status"       : "success",
        "filename"     : file.filename,
        "category"     : category,
        "chunks_stored": chunks_stored,
    }


@app.post("/api/ingest/all")
def ingest_all_documents():
    total_chunks = ingest_all()
    return {
        "status"      : "success",
        "total_chunks": total_chunks,
    }


# -- QnA ----------------------------------------------------------------------

@app.post("/api/query")
def query_knowledge_base(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    result = run_query(request.question, request.category_filter)
    return {
        "question"       : request.question,
        "answer"         : result["answer"],
        "sources"        : result["sources"],
        "category_filter": request.category_filter or "all",
    }


# -- Planning Report ----------------------------------------------------------

@app.post("/api/report")
def generate_planning_report(request: ReportRequest):
    if not request.planning_request.strip():
        raise HTTPException(status_code=400, detail="Planning request cannot be empty.")
    result = run_report(request.planning_request, request.category_filter)
    return {
        "planning_request": request.planning_request,
        "report"          : result["answer"],
        "sources"         : result["sources"],
        "category_filter" : request.category_filter or "all",
    }


# -- Feeder Recommendations ---------------------------------------------------

@app.post("/api/feeder")
def feeder_recommendations(request: FeederRequest):
    question = (
        f"Feeder ID: {request.feeder_id}. "
        f"Load type: {request.load_type}. "
        f"New capacity addition: {request.capacity_kw} kW. "
        f"Voltage level: {request.voltage_level}. "
        f"Analyse this feeder for decarbonisation upgrade requirements, "
        f"voltage violations, protection changes, and EcoStruxure integration."
    )
    result = run_feeder(question, request.category_filter)
    return {
        "feeder_id"      : request.feeder_id,
        "load_type"      : request.load_type,
        "capacity_kw"    : request.capacity_kw,
        "voltage_level"  : request.voltage_level,
        "recommendations": result["answer"],
        "sources"        : result["sources"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=cfg.api.host, port=cfg.api.port)