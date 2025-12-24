#!/usr/bin/env python3
"""
MCP Server (STDIO) for querying https://ctseng777.github.io/

Tools:
- fetch_site_map(max_pages: int = 10): Crawl the site and return discovered pages and links.
- query_site(prompt: str, max_pages: int = 12): Crawl and answer prompt with extracted results
  (supports publications and Google Scholar link heuristics).

Notes:
- Logging goes to stderr. Do not print to stdout except via MCP transport.
- Requires: `requests` and `mcp` (Python SDK) installed in the environment.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import json
import logging
import re
import sys
import time
from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests

try:
    # Python MCP SDK
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except Exception:  # pragma: no cover - allow file to be present even if SDK missing
    Server = None  # type: ignore
    stdio_server = None  # type: ignore


BASE_URL = "https://ctseng777.github.io/"
DEFAULT_HEADERS = {
    "User-Agent": "WebpageMCP/1.0 (+https://modelcontextprotocol.io)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


class _TextAndLinksParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_chunks: List[str] = []
        self.links: List[Tuple[str, str]] = []  # (href, text)
        self._in_script_style = False
        self._current_anchor_href: Optional[str] = None
        self._current_anchor_text_chunks: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._in_script_style = True
        if tag == "a":
            href = dict(attrs).get("href")
            self._current_anchor_href = href
            self._current_anchor_text_chunks = []

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._in_script_style = False
        if tag == "a":
            if self._current_anchor_href:
                text = " ".join(t.strip() for t in self._current_anchor_text_chunks if t.strip())
                self.links.append((self._current_anchor_href, text))
            self._current_anchor_href = None
            self._current_anchor_text_chunks = []

    def handle_data(self, data):
        if self._in_script_style:
            return
        if self._current_anchor_href is not None:
            self._current_anchor_text_chunks.append(data)
        # Always collect text
        if data and data.strip():
            self.text_chunks.append(data.strip())

    def get_text(self) -> str:
        return "\n".join(chunk for chunk in self.text_chunks if chunk)


@dataclass
class Page:
    url: str
    text: str
    links: List[Tuple[str, str]]  # (absolute_url, anchor_text)


def fetch_url(url: str, timeout: float = 15.0) -> Optional[str]:
    try:
        logging.info(f"GET {url}")
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code != 200:
            logging.warning(f"Non-200 status {resp.status_code} for {url}")
            return None
        ct = resp.headers.get("Content-Type", "").lower()
        if "text/html" not in ct and "application/xhtml" not in ct and not url.endswith(".html"):
            logging.info(f"Skipping non-HTML content-type for {url}: {ct}")
            return None
        return resp.text
    except requests.RequestException as e:
        logging.error(f"HTTP error for {url}: {e}")
        return None


def parse_html(base_url: str, html: str) -> Tuple[str, List[Tuple[str, str]]]:
    parser = _TextAndLinksParser()
    parser.feed(html)
    text = parser.get_text()
    abs_links: List[Tuple[str, str]] = []
    for href, atext in parser.links:
        if not href:
            continue
        abs_url = urljoin(base_url, href)
        abs_links.append((abs_url, atext or ""))
    return text, abs_links


def same_host(url: str, host: str) -> bool:
    try:
        return urlparse(url).netloc == host
    except Exception:
        return False


def crawl_site(start_url: str, max_pages: int = 10, delay_s: float = 0.25) -> List[Page]:
    max_pages = max(1, min(max_pages, 50))  # bound
    host = urlparse(start_url).netloc
    visited: Set[str] = set()
    q: deque[str] = deque([start_url])
    pages: List[Page] = []

    while q and len(pages) < max_pages:
        url = q.popleft()
        if url in visited:
            continue
        visited.add(url)

        html = fetch_url(url)
        if not html:
            continue
        text, links = parse_html(url, html)
        pages.append(Page(url=url, text=text, links=links))

        # enqueue new links on same host
        for abs_url, _txt in links:
            if same_host(abs_url, host) and abs_url not in visited:
                q.append(abs_url)

        time.sleep(delay_s)

    return pages


def find_google_scholar_link(pages: Iterable[Page]) -> Optional[Tuple[str, str, str]]:
    for page in pages:
        for href, atext in page.links:
            if "scholar.google" in href.lower() or "google scholar" in atext.lower():
                return page.url, href, atext or "Google Scholar"
    # fallback: any link with 'scholar' in text
    for page in pages:
        for href, atext in page.links:
            if "scholar" in atext.lower():
                return page.url, href, atext
    return None


_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def extract_publications(pages: Iterable[Page]) -> List[Tuple[str, str]]:
    results: List[Tuple[str, str]] = []  # (source_url, line)
    for page in pages:
        lines = [ln.strip() for ln in page.text.splitlines() if ln.strip()]
        # Heuristic: look for lines containing a year and at least 2 punctuation marks (authors/titles)
        for ln in lines:
            if _YEAR_RE.search(ln) and sum(1 for c in ln if c in ",.;:") >= 2:
                results.append((page.url, ln))
        # If page has an obvious 'Publications' keyword, also include nearby lines
        if any("publication" in ln.lower() for ln in lines):
            for ln in lines:
                if _YEAR_RE.search(ln):
                    results.append((page.url, ln))
    # Deduplicate by text
    dedup: Dict[str, Tuple[str, str]] = {}
    for src, ln in results:
        key = ln
        if key not in dedup:
            dedup[key] = (src, ln)
    return list(dedup.values())


def summarize_publications(pub_items: List[Tuple[str, str]], limit: int = 20) -> str:
    if not pub_items:
        return "No publications detected via heuristics."
    lines = ["Publications (heuristic extraction):"]
    for i, (src, ln) in enumerate(pub_items[:limit], 1):
        lines.append(f"{i}. {ln}\n   Source: {src}")
    if len(pub_items) > limit:
        lines.append(f"(+{len(pub_items) - limit} more omitted)")
    return "\n".join(lines)


def answer_prompt(pages: List[Page], prompt: str) -> str:
    p = prompt.lower().strip()
    if "scholar" in p:
        found = find_google_scholar_link(pages)
        if found:
            src, href, text = found
            return (
                "Google Scholar link found:\n"
                f"- Link: {href}\n- Anchor Text: {text}\n- Found on: {src}"
            )
        return "No Google Scholar link found within crawled pages."

    if "publication" in p or "paper" in p or "article" in p:
        pubs = extract_publications(pages)
        return summarize_publications(pubs)

    # Generic fallback: return page titles and top snippets
    lines = ["Query not recognized; returning crawled page summaries:"]
    for page in pages[:8]:
        snippet = " ".join(page.text.split())[:200]
        lines.append(f"- {page.url}: {snippet}...")
    return "\n".join(lines)


def ensure_mcp_available():
    if Server is None or stdio_server is None:
        raise RuntimeError(
            "Python MCP SDK not installed. Please `pip install mcp` and retry."
        )


async def run_server():
    ensure_mcp_available()
    server = Server("webpage")

    @server.tool()
    async def fetch_site_map(max_pages: int = 10) -> str:
        """Crawl the site and return discovered pages and links.

        Args:
            max_pages: Maximum pages to crawl (1-50).

        Returns:
            A JSON string containing pages with URLs and their discovered links.
        """
        try:
            pages = crawl_site(BASE_URL, max_pages=max_pages)
            payload = []
            for p in pages:
                payload.append(
                    {
                        "url": p.url,
                        "links": [
                            {"href": href, "text": text} for href, text in p.links
                        ],
                    }
                )
            return json.dumps({"base": BASE_URL, "pages": payload}, indent=2)
        except Exception as e:
            logging.exception("fetch_site_map failed")
            return json.dumps({"error": str(e)})

    @server.tool()
    async def query_site(prompt: str, max_pages: int = 12) -> str:
        """Crawl the site and answer the prompt. Heuristics support:
        - Publications: extracts citation-like lines with years.
        - Google Scholar link: finds a scholar link if present.

        Args:
            prompt: The user request to satisfy.
            max_pages: Maximum pages to crawl (1-50).

        Returns:
            A human-readable answer with sources.
        """
        if not prompt or not prompt.strip():
            return "Invalid prompt (empty)."
        try:
            pages = crawl_site(BASE_URL, max_pages=max_pages)
            answer = answer_prompt(pages, prompt)
            return answer
        except Exception as e:
            logging.exception("query_site failed")
            return f"Error: {e}"

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


def main() -> int:
    setup_logging()
    try:
        asyncio.run(run_server())
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception:
        logging.exception("Server terminated with error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

