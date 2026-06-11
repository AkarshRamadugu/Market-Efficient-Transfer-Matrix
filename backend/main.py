"""
main.py
-------
FastAPI backend for the Market-Efficient Transfer Matrix.
Exposes three endpoints the frontend consumes:
  GET /players              → all players for search dropdown
  GET /player/{player_id}   → single player stat card
  GET /match                → PCA + cosine similarity + financial filter
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from ml.similarity import get_top_matches, get_player_detail, get_all_players
from ml.financial import apply_financial_filter, build_match_response

app = FastAPI(title="Transfer Matrix API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/players")
def players():
    return get_all_players()

@app.get("/player/{player_id:path}")
def player(player_id: str):
    try:
        return get_player_detail(player_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/match")
def match(
    player_id: str = Query(...),
    budget: float = Query(default=30.0),
    n: int = Query(default=5),
):
    try:
        target   = get_player_detail(player_id)
        raw      = get_top_matches(player_id, n=n * 4)
        filtered = apply_financial_filter(raw, target, budget, n=n)
        return build_match_response(target, raw, filtered, budget)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Mount frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def serve_frontend():
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend not found."}
