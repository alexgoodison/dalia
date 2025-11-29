from __future__ import annotations

from agno.tools import Toolkit

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

    def get_news_sentiment(
        self,
        *,
        tickers: str | list[str] | None = None,
        topics: str | list[str] | None = None,
        time_from: str | None = None,
        time_to: str | None = None,
        sort: str = "LATEST",
        limit: int = 50,
        datatype: str = "json",
    ) -> Dict[str, Any]:
        """Retrieve live and historical market news & sentiment data.

        Args:
            tickers: Comma-separated string or list of stock/crypto/forex symbols
                (e.g., "AAPL" or "COIN,CRYPTO:BTC,FOREX:USD")
            topics: Comma-separated string or list of news topics. Supported topics:
                blockchain, earnings, ipo, mergers_and_acquisitions, financial_markets,
                economy_fiscal, economy_monetary, economy_macro, energy_transportation,
                finance, life_sciences, manufacturing, real_estate, retail_wholesale, technology
            time_from: Start time in YYYYMMDDTHHMM format (e.g., "20220410T0130")
            time_to: End time in YYYYMMDDTHHMM format (e.g., "20220410T0130")
            sort: Sort order - "LATEST" (default), "EARLIEST", or "RELEVANCE"
            limit: Maximum number of results to return (default 50, max 1000)
            datatype: Response format - "json" (default) or "csv"
        """
        params: Dict[str, Any] = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.api_key,
            "datatype": datatype,
            "sort": sort,
            "limit": limit,
        }

        if tickers:
            # Handle both string and list formats
            if isinstance(tickers, list):
                tickers = ",".join(tickers)
            params["tickers"] = tickers

        if topics:
            # Handle both string and list formats
            if isinstance(topics, list):
                topics = ",".join(topics)
            params["topics"] = topics

        if time_from:
            params["time_from"] = time_from

        if time_to:
            params["time_to"] = time_to

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


class AlphaVantageToolkit(Toolkit):

    _client = AlphaVantageClient()

    def __init__(self, **kwargs):
        super().__init__(
            name="alphavantage_tools",
            tools=[
                self.get_global_quote,
                self.get_daily_time_series,
                self.get_intraday_time_series,
                self.search_symbol,
                self.get_currency_exchange_rate,
                self.get_news_sentiment,
            ],
            **kwargs,
        )

    def get_global_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieve the latest quote for a stock symbol (e.g., 'AAPL', 'MSFT').
        Returns information including current price, volume, and trading data.
        """
        return self._client.get_global_quote(symbol)

    def get_daily_time_series(
        self,
        symbol: str,
        *,
        outputsize: str = "compact",
    ) -> Dict[str, Any]:
        """
        Retrieve the daily time series data for a stock symbol.

        Args:
            symbol: The stock symbol (e.g., 'AAPL', 'MSFT')
            outputsize: Either 'compact' (last 100 data points) or 'full' (full-length time series)
        """
        return self._client.get_daily_time_series(symbol, outputsize=outputsize)

    def get_intraday_time_series(
        self,
        symbol: str,
        *,
        interval: str = "5min",
        outputsize: str = "compact",
        adjusted: bool | None = None,
    ) -> Dict[str, Any]:
        """
        Retrieve the intraday time series data for a stock symbol.

        Args:
            symbol: The stock symbol (e.g., 'AAPL', 'MSFT')
            interval: Time interval between two consecutive data points (1min, 5min, 15min, 30min, 60min)
            outputsize: Either 'compact' (last 100 data points) or 'full' (full-length time series)
            adjusted: Whether to return adjusted prices (True) or raw prices (False)
        """
        return self._client.get_intraday_time_series(
            symbol, interval=interval, outputsize=outputsize, adjusted=adjusted
        )

    def search_symbol(self, keywords: str) -> Dict[str, Any]:
        """
        Search for stock symbols that match the provided keywords.
        Useful for finding the correct symbol when you know the company name.
        """
        return self._client.search_symbol(keywords)

    def get_currency_exchange_rate(self, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """
        Retrieve the latest foreign exchange rate between two currencies.

        Args:
            from_currency: The currency to convert from (e.g., 'USD', 'EUR')
            to_currency: The currency to convert to (e.g., 'GBP', 'JPY')
        """
        return self._client.get_currency_exchange_rate(from_currency, to_currency)

    def get_news_sentiment(
        self,
        *,
        tickers: str | list[str] | None = None,
        topics: str | list[str] | None = None,
        time_from: str | None = None,
        time_to: str | None = None,
        sort: str = "LATEST",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Retrieve live and historical market news & sentiment data from premier news outlets.
        Covers stocks, cryptocurrencies, forex, and topics like fiscal policy, M&A, IPOs, etc.

        Args:
            tickers: Stock/crypto/forex symbols to filter by. Can be:
                - A single symbol string (e.g., "AAPL")
                - A comma-separated string (e.g., "COIN,CRYPTO:BTC,FOREX:USD")
                - A list of symbols (e.g., ["AAPL", "MSFT"])
            topics: News topics to filter by. Can be:
                - A single topic string (e.g., "technology")
                - A comma-separated string (e.g., "technology,ipo")
                - A list of topics (e.g., ["technology", "earnings"])
                Supported topics: blockchain, earnings, ipo, mergers_and_acquisitions,
                financial_markets, economy_fiscal, economy_monetary, economy_macro,
                energy_transportation, finance, life_sciences, manufacturing,
                real_estate, retail_wholesale, technology
            time_from: Start time for news articles in YYYYMMDDTHHMM format (e.g., "20220410T0130").
                If specified without time_to, returns articles from this time to now.
            time_to: End time for news articles in YYYYMMDDTHHMM format (e.g., "20220410T0130")
            sort: Sort order - "LATEST" (default), "EARLIEST", or "RELEVANCE"
            limit: Maximum number of results to return (default 50, max 1000)
        """
        return self._client.get_news_sentiment(
            tickers=tickers,
            topics=topics,
            time_from=time_from,
            time_to=time_to,
            sort=sort,
            limit=limit,
        )
