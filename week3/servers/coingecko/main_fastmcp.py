#!/usr/bin/env python3
"""
FastMCP-based STDIO server for CoinGecko price queries.
"""
from __future__ import annotations

import logging

try:
    from mcp.server.fastmcp import FastMCP
except Exception as e:  # pragma: no cover
    raise SystemExit(
        "FastMCP not available. Please `pip install mcp` (with fastmcp) and retry."
    )

from .main import (
    ensure_auth_configured,
    fetch_simple_price,
    normalize_coin_id,
    setup_logging,
    validate_auth_token,
    get_auth_token,
)


server = FastMCP("coingecko")


@server.tool()
def get_coin_price(coin: str, vs_currency: str = "usd", auth_token: str = "") -> str:
    """Fetch the price of a single coin."""
    expected_token = get_auth_token()
    if not auth_token or not auth_token.strip():
        auth_token = expected_token
    auth_error = validate_auth_token(auth_token, expected_token)
    if auth_error:
        return f"Auth error: {auth_error}"
    try:
        coin_id = normalize_coin_id(coin)
        data = fetch_simple_price([coin_id], vs_currency=vs_currency)
        price = data.get(coin_id, {}).get(vs_currency)
        if price is None:
            return f"No price found for '{coin_id}' in '{vs_currency}'."
        import json

        return json.dumps(
            {"coin_id": coin_id, "vs_currency": vs_currency, "price": price},
            indent=2,
        )
    except Exception as exc:
        logging.exception("get_coin_price failed")
        return f"Error: {exc}"


@server.tool()
def get_prices(coins: list[str], vs_currency: str = "usd", auth_token: str = "") -> str:
    """Fetch prices for multiple coins."""
    expected_token = get_auth_token()
    if not auth_token or not auth_token.strip():
        auth_token = expected_token
    auth_error = validate_auth_token(auth_token, expected_token)
    if auth_error:
        return f"Auth error: {auth_error}"
    try:
        normalized = [normalize_coin_id(c) for c in coins]
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
        import json

        return json.dumps({"results": results}, indent=2)
    except Exception as exc:
        logging.exception("get_prices failed")
        return f"Error: {exc}"


def main() -> int:
    setup_logging()
    try:
        ensure_auth_configured()
        server.run()
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception:
        logging.exception("FastMCP server terminated with error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
