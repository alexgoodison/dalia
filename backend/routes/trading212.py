from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.services import PaginatedHistoryTransactions, Trading212Client, Trading212Error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trading212", tags=["Trading 212"])


def _build_trading212_client() -> Trading212Client:
    api_key = os.environ.get("TRADING212_API_KEY")
    api_secret = os.environ.get("TRADING212_API_SECRET")

    if not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="Trading 212 API credentials are not configured on the server.",
        )

    return Trading212Client(api_key=api_key, api_secret=api_secret)


@router.get("/transactions", response_model=PaginatedHistoryTransactions)
async def trading212_transactions(
    cursor: Optional[str] = Query(
        default=None, description="Pagination cursor returned by Trading 212."),
    time: Optional[str] = Query(
        default=None,
        description="Retrieve transactions starting from the specified ISO 8601 timestamp.",
    ),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        le=50,
        description="Maximum number of transactions to return (1-50).",
    ),
) -> PaginatedHistoryTransactions:
    client = _build_trading212_client()
    try:
        response = await client.list_transactions(cursor=cursor, time=time, limit=limit)
    except Trading212Error as exc:
        logger.exception("Trading 212 API error while fetching transactions")
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
    finally:
        await client.aclose()

    return response
