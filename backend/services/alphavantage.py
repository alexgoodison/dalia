from __future__ import annotations

from backend.config import ALPHA_VANTAGE_API_KEY
from typing import Any, Dict

import requests


class AlphaVantageError(RuntimeError):
    """Raised when the Alpha Vantage API returns an error response."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class AlphaVantageClient:
    """Client for interacting with the Alpha Vantage market data API.

    The client provides simple synchronous wrapper methods around the most common endpoints.
    All methods default to returning JSON payloads.
    """

    _BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, *, timeout: float = 10.0) -> None:
        self.api_key = ALPHA_VANTAGE_API_KEY
        if not self.api_key:
            raise ValueError(
                "ALPHA_VANTAGE_API_KEY environment variable is not set")

        self.timeout = timeout

    def get_global_quote(self, symbol: str, *, datatype: str = "json") -> Dict[str, Any]:
        """Retrieve the latest quote for a symbol."""
        params = {
            "symbol": symbol,
            "datatype": datatype,
            "function": "GLOBAL_QUOTE",
            "apikey": self.api_key
        }
        return self._request(params)

    def get_daily_time_series(
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
            "function": "TIME_SERIES_DAILY",
            "apikey": self.api_key
        }
        return self._request(params)

    def get_intraday_time_series(
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
            "function": "TIME_SERIES_INTRADAY",
            "apikey": self.api_key
        }
        if adjusted is not None:
            params["adjusted"] = "true" if adjusted else "false"
        return self._request(params)

    def search_symbol(self, keywords: str, *, datatype: str = "json") -> Dict[str, Any]:
        """Search for symbols that match the provided keywords."""
        params = {
            "keywords": keywords,
            "datatype": datatype,
            "function": "SYMBOL_SEARCH",
            "apikey": self.api_key
        }
        return self._request(params)

    def get_currency_exchange_rate(self, from_currency: str, to_currency: str, *, datatype: str = "json") -> Dict[str, Any]:
        """Retrieve the latest foreign exchange rate between two currencies."""
        params = {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "datatype": datatype,
            "function": "CURRENCY_EXCHANGE_RATE",
            "apikey": self.api_key
        }
        return self._request(params)

    def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a synchronous request to the Alpha Vantage API."""
        try:
            response = requests.get(
                self._BASE_URL, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
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
