#!/usr/bin/env python3
"""
FastMCP-based STDIO server for https://ctseng777.github.io/

Exposes the same tools as the SDK variant, but using FastMCP
as shown in the MCP docs (useful for Claude Desktop testing).
"""
from __future__ import annotations

import logging
import sys

try:
    from mcp.server.fastmcp import FastMCP
except Exception as e:  # pragma: no cover
    raise SystemExit(
        "FastMCP not available. Please `pip install mcp` (with fastmcp) and retry."
    )

from .main import (
    BASE_URL,
    setup_logging,
    crawl_site,
    answer_prompt,
)


server = FastMCP("webpage")


@server.tool()
def fetch_site_map(max_pages: int = 10) -> str:
    """Crawl the site and return discovered pages and links (JSON)."""
    pages = crawl_site(BASE_URL, max_pages=max_pages)
    payload = []
    for p in pages:
        payload.append(
            {
                "url": p.url,
                "links": [{"href": href, "text": text} for href, text in p.links],
            }
        )
    import json

    return json.dumps({"base": BASE_URL, "pages": payload}, indent=2)


@server.tool()
def query_site(prompt: str, max_pages: int = 12) -> str:
    """Crawl the site and answer the prompt (publications, scholar link)."""
    if not prompt or not prompt.strip():
        return "Invalid prompt (empty)."
    pages = crawl_site(BASE_URL, max_pages=max_pages)
    return answer_prompt(pages, prompt)


def main() -> int:
    setup_logging()
    try:
        # FastMCP manages the STDIO transport internally
        server.run()
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception:
        logging.exception("FastMCP server terminated with error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

