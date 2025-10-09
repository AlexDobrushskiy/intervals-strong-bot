"""Configuration management for the Intervals.icu Telegram Bot."""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Intervals.icu Configuration
INTERVALS_API_KEY = os.getenv('INTERVALS_API_KEY')
INTERVALS_ATHLETE_ID = os.getenv('INTERVALS_ATHLETE_ID')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


def validate_config():
    """Validate that all required configuration variables are set."""
    missing = []

    if not TELEGRAM_BOT_TOKEN:
        missing.append('TELEGRAM_BOT_TOKEN')

    if not INTERVALS_API_KEY:
        missing.append('INTERVALS_API_KEY')

    if not INTERVALS_ATHLETE_ID:
        missing.append('INTERVALS_ATHLETE_ID')

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please check your .env file."
        )


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    )
    return logging.getLogger(__name__)
