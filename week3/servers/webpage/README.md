# Webpage MCP Server

This MCP server crawls and queries the website `https://ctseng777.github.io/` to answer prompts like:

- "Find out the publications listed in this site"
- "Find the Google Scholar link listed"

It runs as a local STDIO MCP server and exposes two tools:

- `fetch_site_map` — Crawl the site (bounded) and return discovered pages and links.
- `query_site` — Crawl and answer a user prompt with extracted results (e.g., publications, Google Scholar link).

## Prerequisites

- Python 3.10+
- Install dependencies:
  - `poetry install` (recommended) or `pip install requests`
  - If using an MCP client (e.g., Claude Desktop), install the Python MCP SDK in your environment: `pip install mcp`.

## Run (local STDIO)

- Option A (SDK Server):
  - From repo root: `python -m week3.servers.webpage.main`
  - Or directly: `python week3/servers/webpage/main.py`
- Option B (FastMCP, like the docs example):
  - From repo root: `python -m week3.servers.webpage.main_fastmcp`
  - Or directly: `python week3/servers/webpage/main_fastmcp.py`

## Integrate with Claude Desktop (example)

1. Add to Claude Desktop config (Servers → Add New):
   - Type: STDIO
   - Command: `python`
   - Args (Option A): `["-m", "week3.servers.webpage.main"]`
   - Args (Option B): `["-m", "week3.servers.webpage.main_fastmcp"`]
   - Working directory: repo root
2. Start the server in Claude; it should register tools `fetch_site_map` and `query_site`.
3. Example prompts:
   - "Use query_site to find the publications listed on the site."
   - "Use query_site to find the Google Scholar link on the site."

### Use MCP Inspector (local debugging)

The MCP Inspector helps verify that the server starts and the tools respond before
connecting a client.

1. Install the inspector (if needed):
   - `pip install mcp`
2. Run the inspector and point it at the STDIO server:
   - `npx @modelcontextprotocol/inspector`
3. In the inspector UI, you should see `fetch_site_map` and `query_site`. Try:
   - `query_site` with prompt "Find the Google Scholar link listed"

Notes
- The inspector launches the server directly. Avoid login shells or wrappers that
  print to stdout, since that can break the MCP handshake.
- If you see "handshaking failed," confirm the Python environment has `mcp`
  installed and the working directory is the repo root.

## Integrate with Codex (MCP client)

Add a server entry in Codex that launches the STDIO server using the same Python
environment where `mcp` is installed.

Example config values:
- Name: `my-site`
- Type/Transport: `stdio`
- Command: `python`
- Args: `["-m", "week3.servers.webpage.main"]`
- Working directory: repo root

Edit ~/.codex/config.toml
```
[mcp_servers.my-site]
command = "python"
args = ["-m", "week3.servers.webpage.main_fastmcp"]
env = {}
```


After starting, the server should expose `fetch_site_map` and `query_site` tools.
If startup fails, check for any stdout output before MCP messages (shell startup
noise is a common cause).

### Codex sample usage
`Find out Google Scholar link`


## HTTP mode (non‑MCP)

- Start HTTP server: `python -m week3.servers.webpage.http_app` (defaults to 127.0.0.1:8000)
- Or: `uvicorn week3.servers.webpage.http_app:app --port 8000 --reload`

Example curl commands

- Health check:
  - `curl -s http://127.0.0.1:8000/health`
- Fetch site map (first 5 pages):
  - `curl -s "http://127.0.0.1:8000/site-map?max_pages=5" | jq .`
- Find Google Scholar link:
  - `curl -s -X POST http://127.0.0.1:8000/query -H 'Content-Type: application/json' -d '{"prompt":"Find the Google Scholar link on the site","max_pages":12}' | jq .`
- List publications:
  - `curl -s -X POST http://127.0.0.1:8000/query -H 'Content-Type: application/json' -d '{"prompt":"List the publications on the site","max_pages":20}' | jq .`
