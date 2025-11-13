import os
from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from agno.tools import tool
from backend.services.alphavantage import AlphaVantageClient

alpha_vantage_client = AlphaVantageClient()


@tool(
    name="get_current_stock_price",
    description="Fetches the latest price of a stock",
    cache_results=True,
    cache_dir="/tmp/agno_cache",
    cache_ttl=100
)
async def get_current_stock_price(symbol: str) -> float:
    print(f"Fetching current stock price for {symbol}")
    response = await alpha_vantage_client.get_global_quote(symbol)
    print(response)
    return response["Global Quote"]["05. price"]


dalia_agent = Agent(
    model=Gemini(id="gemini-2.0-flash",
                 api_key=os.environ.get("GEMINI_API_KEY")),
    db=SqliteDb(db_file="tmp/agno.db"),
    markdown=True,
    add_history_to_context=True,
    num_history_runs=10,
    tools=[get_current_stock_price],
    description="You are a helpful assistant that can help with stock portfolio and finance management.",
    instructions=[
        "Format your response using markdown and use tables to display data where possible.",
    ],
)
