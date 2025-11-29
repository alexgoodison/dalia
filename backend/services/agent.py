from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb

from backend.config import GEMINI_API_KEY, GEMINI_MODEL_ID
from backend.services.alphavantage import AlphaVantageToolkit
from backend.services.trading212 import Trading212Toolkit

AGENT_DESCRIPTION = """
You are a helpful assistant that can help with stock portfolio and finance management.
You are also able to use the following tools to get information about the stock portfolio and finance:
- AlphaVantageToolkit: Use the Alpha Vantage API to get market data, search for symbols, get time series data, and currency exchange rates
- Trading212Toolkit: Use the Trading 212 API to get information about the stock portfolio and balance. Trading212 is allows for fractional trading.
"""


dalia_agent = Agent(
    model=Gemini(id=GEMINI_MODEL_ID, api_key=GEMINI_API_KEY),
    db=SqliteDb(db_file="tmp/agno.db"),
    markdown=True,
    add_history_to_context=True,
    num_history_runs=10,
    tools=[AlphaVantageToolkit(), Trading212Toolkit()],
    description=AGENT_DESCRIPTION,
    instructions=[
        "Format your response using markdown and use tables to display data where possible.",
    ],
)
