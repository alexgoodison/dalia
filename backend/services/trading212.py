from __future__ import annotations

from agno.tools import Toolkit

from backend.config import TRADING212_API_KEY, TRADING212_API_SECRET

from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field, model_validator
from requests.auth import HTTPBasicAuth


class Trading212Error(RuntimeError):
    """Raised when the Trading 212 API returns an error."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class Trading212Client:
    """Simple synchronous wrapper around the Trading 212 Public API."""

    _API_PREFIX = "/api/v0"

    def __init__(
        self,
        api_key: str | None,
        api_secret: str | None,
        *,
        timeout: float = 10.0,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError(
                "TRADING212_API_KEY and TRADING212_API_SECRET environment variables are not set")

        self.base_url = "https://live.trading212.com"
        self.timeout = timeout
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(api_key, api_secret)
        self._session.headers.update({"Accept": "application/json"})

    def get_account_info(self) -> Dict[str, Any]:
        return self._request("GET", "/equity/account/info")

    def get_account_cash(self) -> Dict[str, Any]:
        return self._request("GET", "/equity/account/cash")

    def list_orders(self) -> list[Dict[str, Any]]:
        return self._request("GET", "/equity/orders")

    def get_order(self, order_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/equity/orders/{order_id}")

    def cancel_order(self, order_id: int) -> Dict[str, Any] | None:
        return self._request("DELETE", f"/equity/orders/{order_id}")

    def get_portfolio(self) -> list[Dict[str, Any]]:
        return self._request("GET", "/equity/portfolio")

    def get_position(self, ticker: str) -> Optional[Dict[str, Any]]:
        return self._request("GET", f"/equity/portfolio/{ticker}", allow_404=True)

    def list_positions(self, ticker: str | None = None) -> list[Dict[str, Any]]:
        """
        Fetch all open equity positions for the account.

        Optionally filter by a specific instrument ticker (e.g. ``"AAPL_US_EQ"``).
        """
        params: Dict[str, Any] = {}
        if ticker is not None:
            params["ticker"] = ticker
        return self._request("GET", "/equity/positions", params=params or None)

    def list_historical_orders(
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
        return self._request("GET", "/equity/history/orders", params=params)

    def list_dividends(
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
        return self._request("GET", "/history/dividends", params=params)

    def list_transactions(
        self,
        *,
        cursor: str | None = None,
        time: str | None = None,
        limit: int | None = None,
    ) -> "PaginatedHistoryTransactions":
        params: Dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        if time:
            params["time"] = time
        if limit:
            params["limit"] = limit
        payload = self._request("GET", "/history/transactions", params=params)
        return PaginatedHistoryTransactions.model_validate(payload)

    def list_instruments(self) -> list[Dict[str, Any]]:
        return self._request("GET", "/equity/metadata/instruments")

    def list_exchanges(self) -> list[Dict[str, Any]]:
        return self._request("GET", "/equity/metadata/exchanges")

    def request_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/history/exports", json=payload)

    def list_reports(self) -> list[Dict[str, Any]]:
        return self._request("GET", "/history/exports")

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Dict[str, Any] | None = None,
        json: Dict[str, Any] | None = None,
        allow_404: bool = False,
    ) -> Any:
        """Make a synchronous request to the Trading 212 API."""
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
    def set_pagination_params(self) -> "PaginatedHistoryTransactions":
        if not self.next_cursor:
            self.next_cursor = self._extract_param(
                self.next_page_path, "cursor")

        if not self.next_time:
            self.next_time = self._extract_param(
                self.next_page_path, "time")

        return self

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


class Trading212Toolkit(Toolkit):

    _client = Trading212Client(
        api_key=TRADING212_API_KEY,
        api_secret=TRADING212_API_SECRET,
    )

    def __init__(self, **kwargs):
        super().__init__(name="trading212_tools", tools=[
            self.get_account_info, self.get_account_cash, self.list_transactions, self.list_positions], **kwargs)

    def get_account_info(self) -> Dict[str, Any]:
        """
        Get the account information from the Trading 212 API for the current user.
        """
        return self._client.get_account_info()

    def get_account_cash(self) -> Dict[str, Any]:
        """
        Get the account cash from the Trading 212 API for the current user.
        """
        return self._client.get_account_cash()

    def list_transactions(self) -> PaginatedHistoryTransactions:
        """
        List the transactions from the Trading 212 API for the current user.
        """
        return PaginatedHistoryTransactions.model_validate(self._client.list_transactions())

    def list_positions(self, ticker: str | None = None) -> list[Dict[str, Any]]:
        """
        List the positions from the Trading 212 API for the current user.
        """
        return self._client.list_positions(ticker=ticker)
