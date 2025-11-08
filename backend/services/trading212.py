from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field, model_validator
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class Trading212Error(RuntimeError):
    """Raised when the Trading 212 API returns an error."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class Trading212Client:
    """Async-friendly wrapper around the Trading 212 Public API."""

    _API_PREFIX = "/api/v0"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        *,
        timeout: float = 10.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = "https://live.trading212.com"
        self.timeout = timeout
        self._owns_session = session is None
        self._session = session or requests.Session()
        self._session.auth = HTTPBasicAuth(api_key, api_secret)
        self._session.headers.update({"Accept": "application/json"})

    async def __aenter__(self) -> "Trading212Client":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    async def aclose(self) -> None:
        await asyncio.to_thread(self.close)

    async def get_account_info(self) -> Dict[str, Any]:
        return await self._request("GET", "/equity/account/info")

    async def get_account_cash(self) -> Dict[str, Any]:
        return await self._request("GET", "/equity/account/cash")

    async def list_orders(self) -> list[Dict[str, Any]]:
        return await self._request("GET", "/equity/orders")

    async def get_order(self, order_id: int) -> Dict[str, Any]:
        return await self._request("GET", f"/equity/orders/{order_id}")

    async def cancel_order(self, order_id: int) -> Dict[str, Any] | None:
        return await self._request("DELETE", f"/equity/orders/{order_id}")

    async def get_portfolio(self) -> list[Dict[str, Any]]:
        return await self._request("GET", "/equity/portfolio")

    async def get_position(self, ticker: str) -> Optional[Dict[str, Any]]:
        return await self._request("GET", f"/equity/portfolio/{ticker}", allow_404=True)

    async def list_historical_orders(
        self,
        *,
        cursor: int | None = None,
        ticker: str | None = None,
        limit: int | None = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if ticker is not None:
            params["ticker"] = ticker
        if limit is not None:
            params["limit"] = limit
        return await self._request("GET", "/equity/history/orders", params=params)

    async def list_dividends(
        self,
        *,
        cursor: int | None = None,
        ticker: str | None = None,
        limit: int | None = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if ticker is not None:
            params["ticker"] = ticker
        if limit is not None:
            params["limit"] = limit
        return await self._request("GET", "/history/dividends", params=params)

    async def list_transactions(
        self,
        *,
        cursor: str | None = None,
        time: str | None = None,
        limit: int | None = None,
    ) -> "PaginatedHistoryTransactions":
        params: Dict[str, Any] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if time is not None:
            params["time"] = time
        if limit is not None:
            params["limit"] = limit
        payload = await self._request("GET", "/history/transactions", params=params)
        return PaginatedHistoryTransactions.model_validate(payload)

    async def list_instruments(self) -> list[Dict[str, Any]]:
        return await self._request("GET", "/equity/metadata/instruments")

    async def list_exchanges(self) -> list[Dict[str, Any]]:
        return await self._request("GET", "/equity/metadata/exchanges")

    async def request_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/history/exports", json=payload)

    async def list_reports(self) -> list[Dict[str, Any]]:
        return await self._request("GET", "/history/exports")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Dict[str, Any] | None = None,
        json: Dict[str, Any] | None = None,
        allow_404: bool = False,
    ) -> Any:
        return await asyncio.to_thread(
            self._request_sync,
            method,
            path,
            params,
            json,
            allow_404,
        )

    def _request_sync(
        self,
        method: str,
        path: str,
        params: Dict[str, Any] | None,
        json: Dict[str, Any] | None,
        allow_404: bool,
    ) -> Any:
        url = f"{self.base_url}{self._API_PREFIX}{path}"
        try:
            response = self._session.request(
                method,
                url,
                params=params,
                json=json,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.exception("HTTP error while calling Trading 212 API")
            raise Trading212Error("Failed to call Trading 212 API") from exc

        if response.status_code == 404 and allow_404:
            return None

        if not response.ok:
            message = self._extract_error_message(response)
            raise Trading212Error(
                message or "Trading 212 API returned an error",
                status_code=response.status_code,
                payload=self._safe_json(response),
            )

        if response.status_code == 204 or not response.content:
            return None

        data = self._safe_json(response)
        if data is None:
            raise Trading212Error(
                "Failed to decode Trading 212 response as JSON",
                status_code=response.status_code,
            )
        return data

    @staticmethod
    def _safe_json(response: requests.Response) -> Any | None:
        try:
            return response.json()
        except ValueError:
            return None

    def _extract_error_message(self, response: requests.Response) -> str | None:
        payload = self._safe_json(response)
        if isinstance(payload, dict):
            clarification = payload.get("clarification")
            if isinstance(clarification, str):
                return clarification
        return response.text or None


class HistoryTransactionItem(BaseModel):
    amount: float | None = None
    date_time: str | None = Field(default=None, alias="dateTime")
    reference: str | None = None
    type: str | None = None

    model_config = {"populate_by_name": True}


class PaginatedHistoryTransactions(BaseModel):
    items: list[HistoryTransactionItem]
    next_page_path: str | None = Field(default=None, alias="nextPagePath")
    next_cursor: str | None = Field(
        default=None,
        alias="nextCursor",
        serialization_alias="nextCursor",
    )
    next_time: str | None = Field(
        default=None,
        alias="nextTime",
        serialization_alias="nextTime",
    )

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def set_pagination_params(cls, values: "PaginatedHistoryTransactions") -> "PaginatedHistoryTransactions":
        if not values.next_cursor:
            values.next_cursor = cls._extract_param(
                values.next_page_path, "cursor")

        if not values.next_time:
            values.next_time = cls._extract_param(
                values.next_page_path, "time")

        return values

    @staticmethod
    def _extract_param(next_page_path: str | None, param_key: str) -> str | None:
        if not next_page_path:
            return None

        candidates: list[str] = []
        parts = next_page_path.split("?", 1)
        if len(parts) == 2:
            candidates.extend(parts)
        else:
            candidates.append(next_page_path)

        for candidate in candidates:
            query_pairs = [
                fragment.split("=", 1) for fragment in candidate.split("&") if "=" in fragment
            ]
            for key, value in query_pairs:
                if key == param_key and value:
                    return value

        return None
