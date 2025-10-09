#!/usr/bin/env python3
"""
Main entry point for the Strong → Intervals.icu Telegram Bot.

This bot receives workout messages from the Strong app via Telegram
and automatically creates corresponding workout events in Intervals.icu.
"""

import sys
import logging
from config import (
    validate_config,
    setup_logging,
    TELEGRAM_BOT_TOKEN,
    INTERVALS_API_KEY,
    INTERVALS_ATHLETE_ID
)
from intervals_client import IntervalsClient
from telegram_bot import WorkoutBot

logger = setup_logging()


def main():
    """Main function to start the bot."""
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        validate_config()

        # Initialize Intervals.icu client
        logger.info("Initializing Intervals.icu client...")
        intervals_client = IntervalsClient(
            api_key=INTERVALS_API_KEY,
            athlete_id=INTERVALS_ATHLETE_ID
        )

        # Test connection
        logger.info("Testing Intervals.icu connection...")
        if not intervals_client.test_connection():
            logger.error("Failed to connect to Intervals.icu. Please check your credentials.")
            sys.exit(1)

        logger.info("Connection to Intervals.icu successful!")

        # Initialize and start the Telegram bot
        logger.info("Initializing Telegram bot...")
        bot = WorkoutBot(
            telegram_token=TELEGRAM_BOT_TOKEN,
            intervals_client=intervals_client
        )

        logger.info("Bot is ready! Starting polling...")
        logger.info("Press Ctrl+C to stop the bot")

        # Run the bot
        bot.run()

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
