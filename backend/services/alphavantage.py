from __future__ import annotations

import os
import asyncio
import logging
from typing import Any, Dict, Iterable

import requests

logger = logging.getLogger(__name__)


class AlphaVantageError(RuntimeError):
    """Raised when the Alpha Vantage API returns an error response."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class AlphaVantageClient:
    """Client for interacting with the Alpha Vantage market data API.

    The client provides async-friendly wrapper methods around the most common endpoints.
    All methods default to returning JSON payloads.
    """

    _BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, *, timeout: float = 10.0, session: requests.Session | None = None) -> None:
        self.api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "ALPHA_VANTAGE_API_KEY environment variable is not set")

        self.timeout = timeout
        self._session = session or requests.Session()
        self._owns_session = session is None

    async def __aenter__(self) -> "AlphaVantageClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    async def aclose(self) -> None:
        await asyncio.to_thread(self.close)

    async def get_global_quote(self, symbol: str, *, datatype: str = "json") -> Dict[str, Any]:
        """Retrieve the latest quote for a symbol."""
        params = {
            "symbol": symbol,
            "datatype": datatype,
        }
        return await self._request("GLOBAL_QUOTE", params)

    async def get_daily_time_series(
        self,
        symbol: str,
        *,
        outputsize: str = "compact",
        datatype: str = "json",
    ) -> Dict[str, Any]:
        """Retrieve the daily time series for a symbol."""
        params = {
            "symbol": symbol,
            "outputsize": outputsize,
            "datatype": datatype,
        }
        return await self._request("TIME_SERIES_DAILY", params)

    async def get_intraday_time_series(
        self,
        symbol: str,
        *,
        interval: str = "5min",
        outputsize: str = "compact",
        adjusted: bool | None = None,
        datatype: str = "json",
    ) -> Dict[str, Any]:
        """Retrieve the intraday time series for a symbol with the specified interval."""
        params: Dict[str, Any] = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "datatype": datatype,
        }
        if adjusted is not None:
            params["adjusted"] = "true" if adjusted else "false"
        return await self._request("TIME_SERIES_INTRADAY", params)

    async def search_symbol(self, keywords: str, *, datatype: str = "json") -> Dict[str, Any]:
        """Search for symbols that match the provided keywords."""
        params = {
            "keywords": keywords,
            "datatype": datatype,
        }
        return await self._request("SYMBOL_SEARCH", params)

    async def get_currency_exchange_rate(self, from_currency: str, to_currency: str, *, datatype: str = "json") -> Dict[str, Any]:
        """Retrieve the latest foreign exchange rate between two currencies."""
        params = {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "datatype": datatype,
        }
        return await self._request("CURRENCY_EXCHANGE_RATE", params)

    async def _request(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return await asyncio.to_thread(self._request_sync, function_name, params)

    def _request_sync(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        query_params = {
            "function": function_name,
            "apikey": self.api_key,
        }
        query_params.update(self._filter_params(params))

        try:
            response = self._session.get(
                self._BASE_URL, params=query_params, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.exception(
                "HTTP error while calling Alpha Vantage API function %s", function_name)
            raise AlphaVantageError(
                "Failed to call Alpha Vantage API") from exc

        if not response.ok:
            raise AlphaVantageError(
                "Alpha Vantage API returned an error status",
                status_code=response.status_code,
                payload=self._safe_json(response),
            )

        payload = self._safe_json(response)
        if payload is None:
            raise AlphaVantageError(
                "Failed to decode Alpha Vantage response as JSON",
                status_code=response.status_code,
            )

        self._ensure_success_payload(payload)
        return payload

    @staticmethod
    def _filter_params(params: Dict[str, Any]) -> Dict[str, Any]:
        filtered: Dict[str, Any] = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, str):
                if value:
                    filtered[key] = value
                continue
            if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
                joined = ",".join(str(item)
                                  for item in value if item is not None)
                if joined:
                    filtered[key] = joined
                continue
            filtered[key] = value
        return filtered

    @staticmethod
    def _safe_json(response: requests.Response) -> Dict[str, Any] | None:
        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else None
        except ValueError:
            return None

    @staticmethod
    def _ensure_success_payload(payload: Dict[str, Any]) -> None:
        message_keys = ("Error Message", "Note", "Information")
        for key in message_keys:
            message = payload.get(key)
            if isinstance(message, str) and message.strip():
                raise AlphaVantageError(message, payload=payload)
