import os
from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb

dalia_agent = Agent(
    model=Gemini(id="gemini-2.0-flash",
                 api_key=os.environ.get("GEMINI_API_KEY")),
    db=SqliteDb(db_file="tmp/agno.db"),
    markdown=True,
    add_history_to_context=True,
    num_history_runs=10,
)
