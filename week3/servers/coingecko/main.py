#!/usr/bin/env python3
"""
MCP Server (STDIO) for CoinGecko price queries.

Tools:
- get_coin_price(coin: str, vs_currency: str = "usd", auth_token: str): Get one coin price.
- get_prices(coins: list[str], vs_currency: str = "usd", auth_token: str): Get multiple prices.

Notes:
- Logging goes to stderr. Do not print to stdout except via MCP transport.
- Requires: `requests` and `mcp` (Python SDK) installed in the environment.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional

import requests

try:
    # Python MCP SDK
    from mcp import types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except Exception:  # pragma: no cover - allow file to be present even if SDK missing
    Server = None  # type: ignore
    stdio_server = None  # type: ignore
    types = None  # type: ignore


API_BASE_URL = "https://api.coingecko.com/api/v3"
API_KEY_ENV = "COINGECKO_API_KEY"
AUTH_TOKEN_ENV = "COINGECKO_MCP_AUTH_TOKEN"
DEFAULT_HEADERS = {
    "User-Agent": "CoinGeckoMCP/1.0 (+https://modelcontextprotocol.io)",
    "Accept": "application/json",
}

COIN_ALIASES = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "ada": "cardano",
    "cardano": "cardano",
    "xrp": "ripple",
    "ripple": "ripple",
    "doge": "dogecoin",
    "dogecoin": "dogecoin",
    "ltc": "litecoin",
    "litecoin": "litecoin",
}


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def normalize_coin_id(raw: str) -> str:
    if not raw or not raw.strip():
        raise ValueError("coin is required")
    key = raw.strip().lower()
    return COIN_ALIASES.get(key, key)


def get_api_key() -> str:
    api_key = os.getenv(API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError(
            f"Missing {API_KEY_ENV}. Set it to your CoinGecko API key."
        )
    return api_key


def get_auth_token() -> str:
    token = os.getenv(AUTH_TOKEN_ENV, "").strip()
    if not token:
        raise RuntimeError(
            f"Missing {AUTH_TOKEN_ENV}. Set it to require MCP authentication."
        )
    return token


def validate_auth_token(auth_token: str, expected: str) -> Optional[str]:
    if not auth_token or not auth_token.strip():
        return "Missing auth_token."
    if auth_token.strip() != expected:
        return "Invalid auth_token."
    return None


def fetch_simple_price(
    coin_ids: List[str],
    vs_currency: str,
    timeout_s: float = 10.0,
    max_retries: int = 2,
) -> Dict[str, Dict[str, float]]:
    if not coin_ids:
        raise ValueError("coin_ids is required")
    if not vs_currency or not vs_currency.strip():
        raise ValueError("vs_currency is required")

    api_key = get_api_key()
    url = f"{API_BASE_URL}/simple/price"
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": vs_currency,
        "x_cg_demo_api_key": api_key,
    }

    last_error: Optional[str] = None
    for attempt in range(max_retries + 1):
        try:
            logging.info("GET %s (attempt %s)", url, attempt + 1)
            resp = requests.get(
                url,
                headers=DEFAULT_HEADERS,
                params=params,
                timeout=timeout_s,
            )
        except requests.RequestException as exc:
            last_error = f"HTTP error: {exc}"
            logging.warning(last_error)
            time.sleep(0.5 * (attempt + 1))
            continue

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            wait_s = 1.0 + attempt
            if retry_after and retry_after.isdigit():
                wait_s = float(retry_after)
            logging.warning("Rate limited by CoinGecko. Sleeping %.1fs", wait_s)
            time.sleep(wait_s)
            last_error = "Rate limited by CoinGecko"
            continue

        if resp.status_code >= 400:
            last_error = f"CoinGecko error {resp.status_code}: {resp.text[:200]}"
            logging.warning(last_error)
            time.sleep(0.5 * (attempt + 1))
            continue

        try:
            return resp.json()
        except ValueError as exc:
            raise RuntimeError(f"Invalid JSON response: {exc}") from exc

    raise RuntimeError(last_error or "CoinGecko request failed")


def ensure_mcp_available() -> None:
    if Server is None or stdio_server is None or types is None:
        raise RuntimeError(
            "Python MCP SDK not installed. Please `pip install mcp` and retry."
        )


def ensure_auth_configured() -> None:
    _ = get_auth_token()


async def run_server() -> None:
    ensure_mcp_available()
    ensure_auth_configured()
    server = Server("coingecko")
    expected_token = get_auth_token()

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="get_coin_price",
                description="Fetch the price of a single coin.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "coin": {"type": "string"},
                        "vs_currency": {"type": "string", "default": "usd"},
                        "auth_token": {"type": "string"},
                    },
                    "required": ["coin"],
                },
            ),
            types.Tool(
                name="get_prices",
                description="Fetch prices for multiple coins.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "coins": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        "vs_currency": {"type": "string", "default": "usd"},
                        "auth_token": {"type": "string"},
                    },
                    "required": ["coins"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(tool_name: str, arguments: dict) -> dict | types.CallToolResult:
        auth_token = str(arguments.get("auth_token", ""))
        if not auth_token or not auth_token.strip():
            auth_token = expected_token
        auth_error = validate_auth_token(auth_token, expected_token)
        if auth_error:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Auth error: {auth_error}")],
                isError=True,
            )

        try:
            if tool_name == "get_coin_price":
                coin = str(arguments.get("coin", ""))
                vs_currency = str(arguments.get("vs_currency", "usd"))
                coin_id = normalize_coin_id(coin)
                data = fetch_simple_price([coin_id], vs_currency=vs_currency)
                price = data.get(coin_id, {}).get(vs_currency)
                if price is None:
                    return types.CallToolResult(
                        content=[
                            types.TextContent(
                                type="text",
                                text=f"No price found for '{coin_id}' in '{vs_currency}'.",
                            )
                        ],
                        isError=True,
                    )
                return {"coin_id": coin_id, "vs_currency": vs_currency, "price": price}

            if tool_name == "get_prices":
                coins_raw = arguments.get("coins", [])
                vs_currency = str(arguments.get("vs_currency", "usd"))
                normalized = [normalize_coin_id(str(c)) for c in coins_raw]
                data = fetch_simple_price(normalized, vs_currency=vs_currency)
                results = []
                for coin_id in normalized:
                    results.append(
                        {
                            "coin_id": coin_id,
                            "vs_currency": vs_currency,
                            "price": data.get(coin_id, {}).get(vs_currency),
                        }
                    )
                return {"results": results}

            return types.CallToolResult(
                content=[
                    types.TextContent(type="text", text=f"Unknown tool: {tool_name}")
                ],
                isError=True,
            )
        except Exception as exc:
            logging.exception("call_tool failed")
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Error: {exc}")],
                isError=True,
            )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            initialization_options=server.create_initialization_options(),
        )


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
