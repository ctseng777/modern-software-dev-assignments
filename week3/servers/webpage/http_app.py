#!/usr/bin/env python3
"""
HTTP wrapper (FastAPI) for testing without MCP.

Endpoints:
- GET /health -> {status:"ok"}
- GET /site-map?max_pages=10 -> Crawled pages and links (JSON)
- POST /query {prompt, max_pages} -> Answer string (publications, scholar link)

Run:
- python -m week3.servers.webpage.http_app
- or: uvicorn week3.servers.webpage.http_app:app --port 8000 --reload
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .main import BASE_URL, setup_logging, crawl_site, answer_prompt


setup_logging()
app = FastAPI(title="Webpage Crawler API", version="0.1.0")


class QueryRequest(BaseModel):
    prompt: str = Field(..., description="User prompt to answer")
    max_pages: int = Field(12, ge=1, le=50, description="Max pages to crawl")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/site-map")
def site_map(max_pages: int = Query(10, ge=1, le=50)) -> Dict[str, Any]:
    try:
        pages = crawl_site(BASE_URL, max_pages=max_pages)
        payload: List[Dict[str, Any]] = []
        for p in pages:
            payload.append(
                {
                    "url": p.url,
                    "links": [{"href": href, "text": text} for href, text in p.links],
                }
            )
        return {"base": BASE_URL, "pages": payload}
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
def query(req: QueryRequest) -> Dict[str, str]:
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt must not be empty")
    try:
        pages = crawl_site(BASE_URL, max_pages=req.max_pages)
        answer = answer_prompt(pages, prompt)
        return {"answer": answer}
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(e))


def main() -> int:
    # Lazy import uvicorn to avoid dependency at import-time
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("week3.servers.webpage.http_app:app", host="127.0.0.1", port=port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

