"""Server Security Scanner - FastAPI application."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import api_router

app = FastAPI(
    title="Server Security Scanner",
    version="2.0.0",
    description="Web-based security scanner with PDF reports",
)

# Mount API routes first
app.include_router(api_router)

# React build directory - mount /assets BEFORE catch-all so JS/CSS load correctly
STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
assets_dir = STATIC_DIR / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/", response_model=None)
def serve_index():
    """Serve React SPA index."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Server Security Scanner API", "docs": "/docs"}
