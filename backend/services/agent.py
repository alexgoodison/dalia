from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from agno.tools import tool

from backend.config import GEMINI_API_KEY, GEMINI_MODEL_ID
from backend.services.alphavantage import AlphaVantageClient
from backend.services.trading212 import Trading212Toolkit


alpha_vantage_client = AlphaVantageClient()


@tool(
    name="get_current_stock_price",
    description="Fetches the latest price of a stock",
    cache_results=True,
    cache_dir="/tmp/agno_cache",
    cache_ttl=100
)
def get_current_stock_price(symbol: str) -> float:
    response = alpha_vantage_client.get_global_quote(symbol)
    return response["Global Quote"]["05. price"]


dalia_agent = Agent(
    model=Gemini(id=GEMINI_MODEL_ID, api_key=GEMINI_API_KEY),
    db=SqliteDb(db_file="tmp/agno.db"),
    markdown=True,
    add_history_to_context=True,
    num_history_runs=10,
    tools=[get_current_stock_price, Trading212Toolkit()],
    description="""
    You are a helpful assistant that can help with stock portfolio and finance management.
    You are also able to use the following tools to get information about the stock portfolio and finance:
    - get_current_stock_price: Get the current price of a stock
    - Trading212Toolkit: Use the Trading 212 API to get information about the stock portfolio and balance. Trading212 is allows for fractional trading.
    """,
    instructions=[
        "Format your response using markdown and use tables to display data where possible.",
    ],
)
