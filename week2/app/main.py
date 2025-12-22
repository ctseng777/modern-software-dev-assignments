"""
Main FastAPI application module.

This module initializes the FastAPI app, sets up routes, and handles
application lifecycle events.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routers import action_items, notes


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Action Item Extractor",
        description="A FastAPI application for extracting action items from notes using heuristics or LLM",
        version="1.0.0",
    )
    
    # Initialize database on startup
    @app.on_event("startup")
    def startup_event() -> None:
        """Initialize database on application startup."""
        init_db()
    
    # Register routes
    app.include_router(notes.router)
    app.include_router(action_items.router)
    
    # Serve static files
    static_dir = Path(__file__).resolve().parents[1] / "frontend"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        """Serve the main HTML page."""
        html_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
        return html_path.read_text(encoding="utf-8")
    
    return app


# Create the app instance
app = create_app()