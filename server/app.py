"""FastAPI application entry point — serves API + Vue frontend static files."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes.auth import router as auth_router
from .routes.chat import router as chat_router
from .routes.memory import router as memory_router

app = FastAPI(title="胃病智能问答系统")

# CORS: allow Vue dev server (port 5173) and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(memory_router)

# Serve Vue build output (after npm run build → frontend/dist/)
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount(
        "/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets"
    )

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        """Fallback: serve index.html for Vue router history mode."""
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
