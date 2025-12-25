#!/usr/bin/env python3
"""
HTTP wrapper (FastAPI) for testing without MCP.

Endpoints:
- GET /health -> {status:"ok"}
- POST /price {coin, vs_currency, auth_token} -> single price
- POST /prices {coins, vs_currency, auth_token} -> multiple prices

Run:
- python -m week3.servers.coingecko.http_app
- or: uvicorn week3.servers.coingecko.http_app:app --port 8000 --reload
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .main import (
    fetch_simple_price,
    get_auth_token,
    normalize_coin_id,
    setup_logging,
    validate_auth_token,
)


setup_logging()
EXPECTED_AUTH_TOKEN = get_auth_token()
app = FastAPI(title="CoinGecko Debug API", version="0.1.0")


class PriceRequest(BaseModel):
    coin: str = Field(..., description="Coin id, name, or symbol (e.g., bitcoin, BTC)")
    vs_currency: str = Field("usd", description="Quote currency")
    auth_token: str = Field(..., description="Must match COINGECKO_MCP_AUTH_TOKEN")


class PricesRequest(BaseModel):
    coins: List[str] = Field(..., description="Coin ids, names, or symbols")
    vs_currency: str = Field("usd", description="Quote currency")
    auth_token: str = Field(..., description="Must match COINGECKO_MCP_AUTH_TOKEN")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def _require_auth(auth_token: str) -> None:
    auth_error = validate_auth_token(auth_token, EXPECTED_AUTH_TOKEN)
    if auth_error:
        raise HTTPException(status_code=401, detail=auth_error)


@app.post("/price")
def price(req: PriceRequest) -> Dict[str, Any]:
    _require_auth(req.auth_token)
    try:
        coin_id = normalize_coin_id(req.coin)
        data = fetch_simple_price([coin_id], vs_currency=req.vs_currency)
        price_val = data.get(coin_id, {}).get(req.vs_currency)
        if price_val is None:
            raise HTTPException(
                status_code=404,
                detail=f"No price found for '{coin_id}' in '{req.vs_currency}'.",
            )
        return {"coin_id": coin_id, "vs_currency": req.vs_currency, "price": price_val}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logging.exception("/price failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/prices")
def prices(req: PricesRequest) -> Dict[str, Any]:
    _require_auth(req.auth_token)
    try:
        if not req.coins:
            raise HTTPException(status_code=400, detail="coins must not be empty")
        normalized = [normalize_coin_id(c) for c in req.coins]
        data = fetch_simple_price(normalized, vs_currency=req.vs_currency)
        results = []
        for coin_id in normalized:
            results.append(
                {
                    "coin_id": coin_id,
                    "vs_currency": req.vs_currency,
                    "price": data.get(coin_id, {}).get(req.vs_currency),
                }
            )
        return {"results": results}
    except Exception as exc:  # pragma: no cover
        logging.exception("/prices failed")
        raise HTTPException(status_code=500, detail=str(exc))


def main() -> int:
    # Lazy import uvicorn to avoid dependency at import-time
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("week3.servers.coingecko.http_app:app", host="127.0.0.1", port=port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
