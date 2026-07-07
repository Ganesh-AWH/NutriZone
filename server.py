"""
FastAPI server entry point for the Nutrition AI backend.

Run:   python server.py
  or:  uvicorn server:app --host 0.0.0.0 --port 8001 --reload

The Streamlit frontend (app.py) connects to this server at http://127.0.0.1:8001
The 3D frontend is served at http://127.0.0.1:8001/ (static files)
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routes import router
from api.body_state import body_state_router
from api.simulation import simulation_router

app = FastAPI(
    title="NutriTwin — Nutrition AI API",
    description="Multi-agent nutrition planning backend with LLM explanations + 3D visualization",
    version="4.0.0",
)

# Allow all frontends to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router)
app.include_router(body_state_router)
app.include_router(simulation_router)

# ── Static file serving ──────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

# Serve organ .glb models at /organs/
organs_dir = BASE_DIR / "organs"
if organs_dir.is_dir():
    app.mount("/organs", StaticFiles(directory=str(organs_dir)), name="organs")

# Serve frontend at /frontend/ (for JS modules, CSS)
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.is_dir():
    app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")


# Root → serve the 3D frontend index.html
@app.get("/")
def serve_index():
    index_path = frontend_dir / "index.html"
    if index_path.is_file():
        return FileResponse(str(index_path))
    return {"message": "NutriTwin API is running. 3D frontend not found at /frontend/index.html"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
