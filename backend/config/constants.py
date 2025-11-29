"""Constants and configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "env")
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_ID = os.environ.get("GEMINI_MODEL_ID", "gemini-2.0-flash")

TRADING212_API_KEY = os.environ.get("TRADING212_API_KEY")
TRADING212_API_SECRET = os.environ.get("TRADING212_API_SECRET")

ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")


def validate_required_config() -> None:
    """Validate that all required configuration values are set."""
    errors = []

    if not GEMINI_API_KEY or not GEMINI_API_KEY.strip():
        errors.append(
            "GEMINI_API_KEY environment variable is not set or is empty. "
            "Please set the environment variable with a valid API key. "
            f"You can create a .env file in {BASE_DIR}/ directory with: GEMINI_API_KEY=your_key_here"
        )

    if errors:
        raise ValueError("\n".join(errors))
