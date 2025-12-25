# CoinGecko MCP Server

This MCP server queries CoinGecko prices to answer prompts like:

- "Check the BTC price today"
- "What's the price of Ethereum?"

It runs as a local STDIO MCP server and exposes two tools:

- `get_coin_price` — Fetch one coin price.
- `get_prices` — Fetch multiple coin prices.

## Prerequisites

- Python 3.10+
- Install dependencies:
  - `poetry install` (recommended) or `pip install requests`
  - If using an MCP client (e.g., Claude Desktop), install the Python MCP SDK: `pip install mcp`
  - If using HTTP mode: `pip install fastapi uvicorn`

## Environment

- `COINGECKO_API_KEY`: CoinGecko API key (required for upstream requests).
- `COINGECKO_MCP_AUTH_TOKEN`: Required token for MCP authentication.

Example:

```
export COINGECKO_API_KEY="CG-..."
export COINGECKO_MCP_AUTH_TOKEN="local-dev-token"
```

## Run (local STDIO)

- Option A (SDK Server):
  - From repo root: `python -m week3.servers.coingecko.main`
  - Or directly: `python week3/servers/coingecko/main.py`
- Option B (FastMCP):
  - From repo root: `python -m week3.servers.coingecko.main_fastmcp`
  - Or directly: `python week3/servers/coingecko/main_fastmcp.py`

## Integrate with Claude Desktop (example)

1. Add to Claude Desktop config (Servers → Add New):
   - Type: STDIO
   - Command: `python`
   - Args (Option A): `["-m", "week3.servers.coingecko.main"]`
   - Args (Option B): `["-m", "week3.servers.coingecko.main_fastmcp"]`
   - Working directory: repo root
2. Set environment variables for `COINGECKO_API_KEY` and `COINGECKO_MCP_AUTH_TOKEN`.
3. Example prompts:
   - "Use get_coin_price to check BTC price today."
   - "Use get_coin_price for Ethereum in USD."

## HTTP mode (non‑MCP)

- Start HTTP server: `python -m week3.servers.coingecko.http_app` (defaults to 127.0.0.1:8000)
- Or: `uvicorn week3.servers.coingecko.http_app:app --port 8000 --reload`

Example curl commands:

- Health check:
  - `curl -s http://127.0.0.1:8000/health`
- Single price:
  - `curl -s -X POST http://127.0.0.1:8000/price -H 'Content-Type: application/json' -d '{"coin":"bitcoin","vs_currency":"usd","auth_token":"local-dev-token"}' | jq .`
- Multiple prices:
  - `curl -s -X POST http://127.0.0.1:8000/prices -H 'Content-Type: application/json' -d '{"coins":["bitcoin","ethereum"],"vs_currency":"usd","auth_token":"local-dev-token"}' | jq .`

## Tool reference

### `get_coin_price`

Parameters:

- `coin` (string): Coin id, name, or symbol (e.g., `bitcoin`, `BTC`, `ethereum`).
- `vs_currency` (string, default: `usd`)
- `auth_token` (string): Must match `COINGECKO_MCP_AUTH_TOKEN`.

Example result:

```
{
  "coin_id": "bitcoin",
  "vs_currency": "usd",
  "price": 64000
}
```

### `get_prices`

Parameters:

- `coins` (list[string]): Coin ids, names, or symbols.
- `vs_currency` (string, default: `usd`)
- `auth_token` (string): Must match `COINGECKO_MCP_AUTH_TOKEN`.

Example result:

```
{
  "results": [
    {"coin_id": "bitcoin", "vs_currency": "usd", "price": 64000},
    {"coin_id": "ethereum", "vs_currency": "usd", "price": 3200}
  ]
}
```

Notes

- Coin symbols are normalized for common aliases (BTC→bitcoin, ETH→ethereum, etc.).
- If you see rate-limit errors, wait and retry; the server retries a few times.
