"""Telegram bot for receiving and processing Strong app workout messages."""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from strong_parser import StrongParser
from intervals_client import IntervalsClient

logger = logging.getLogger(__name__)

# Whitelist of allowed Telegram user IDs
# To find your user ID: run the bot and send /start, check the console logs
# Example: ALLOWED_USERS = [123456789, 987654321]
ALLOWED_USERS = [337053497]  # Add your Telegram user ID here after finding it


class WorkoutBot:
    """Telegram bot for processing Strong app workouts."""

    def __init__(self, telegram_token: str, intervals_client: IntervalsClient):
        """
        Initialize the workout bot.

        Args:
            telegram_token: Telegram bot token
            intervals_client: Initialized IntervalsClient instance
        """
        self.intervals_client = intervals_client
        self.application = Application.builder().token(telegram_token).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up message and command handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("test", self.test_command))

        # Message handler for workout texts
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    def _is_user_authorized(self, user_id: int) -> bool:
        """
        Check if a user is authorized to use the bot.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user is authorized (whitelist is empty or user is in whitelist)
        """
        # If whitelist is empty, allow all users (for initial setup)
        if not ALLOWED_USERS:
            return True
        return user_id in ALLOWED_USERS

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        user_id = update.effective_user.id
        username = update.effective_user.username or "N/A"

        # Log user ID clearly for whitelist setup
        logger.info("=" * 60)
        logger.info(f"USER CONNECTED - Telegram ID: {user_id}, Username: @{username}")
        logger.info("=" * 60)

        # Check authorization
        if not self._is_user_authorized(user_id):
            await update.message.reply_text(
                "⛔ Not authorized. This bot is private and only accessible to whitelisted users."
            )
            logger.warning(f"Unauthorized access attempt by user {user_id} (@{username})")
            return

        welcome_message = (
            "Welcome to the Strong → Intervals.icu Bot!\n\n"
            "Simply share your workout from the Strong app to this chat, "
            "and I'll automatically create it as a completed activity in your Intervals.icu account.\n\n"
            "Commands:\n"
            "/start - Show this welcome message\n"
            "/help - Get help\n"
            "/test - Test the connection to Intervals.icu"
        )
        await update.message.reply_text(welcome_message)
        logger.info(f"User {user_id} started the bot")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command."""
        user_id = update.effective_user.id

        # Check authorization
        if not self._is_user_authorized(user_id):
            await update.message.reply_text(
                "⛔ Not authorized. This bot is private and only accessible to whitelisted users."
            )
            logger.warning(f"Unauthorized access attempt by user {user_id}")
            return

        help_message = (
            "**How to use this bot:**\n\n"
            "1. Open the Strong app on your phone\n"
            "2. Go to your completed workout\n"
            "3. Tap the share button (three dots)\n"
            "4. Select 'Share' and choose Telegram\n"
            "5. Send it to this bot\n\n"
            "The bot will automatically:\n"
            "- Parse your workout data\n"
            "- Create an activity in your Intervals.icu account\n"
            "- Send you a confirmation with a link\n\n"
            "**Supported formats:**\n"
            "- Exercises with sets, reps, and weights\n"
            "- Bodyweight exercises\n"
            "- Timed exercises (e.g., stretching)\n"
            "- Warmup sets\n\n"
            "Need help? Check the README or contact your administrator."
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
        logger.info(f"User {user_id} requested help")

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /test command to test Intervals.icu connection."""
        user_id = update.effective_user.id

        # Check authorization
        if not self._is_user_authorized(user_id):
            await update.message.reply_text(
                "⛔ Not authorized. This bot is private and only accessible to whitelisted users."
            )
            logger.warning(f"Unauthorized access attempt by user {user_id}")
            return

        await update.message.reply_text("Testing connection to Intervals.icu...")

        if self.intervals_client.test_connection():
            await update.message.reply_text(
                "✅ Connection successful! The bot is ready to sync your workouts."
            )
        else:
            await update.message.reply_text(
                "❌ Connection failed. Please check your API credentials and try again."
            )
        logger.info(f"User {user_id} ran connection test")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle incoming text messages and process potential workout data.

        Args:
            update: Telegram update object
            context: Callback context
        """
        text = update.message.text
        user_id = update.effective_user.id

        logger.info(f"Received message from user {user_id}")

        # Check authorization
        if not self._is_user_authorized(user_id):
            await update.message.reply_text(
                "⛔ Not authorized. This bot is private and only accessible to whitelisted users."
            )
            logger.warning(f"Unauthorized access attempt by user {user_id}")
            return

        # Check if this looks like a Strong workout
        if not StrongParser.is_strong_workout(text):
            await update.message.reply_text(
                "This doesn't look like a Strong app workout. "
                "Please share a workout directly from the Strong app.\n\n"
                "Use /help for instructions."
            )
            return

        # Parse the workout
        await update.message.reply_text("🏋️ Parsing your workout...")

        workout = StrongParser.parse_workout(text)

        if not workout:
            await update.message.reply_text(
                "❌ Could not parse the workout. Please make sure you're sharing "
                "a complete workout from the Strong app."
            )
            logger.warning(f"Failed to parse workout from user {user_id}")
            return

        # Format the workout description
        description = StrongParser.format_workout_description(workout)

        # Create the activity in Intervals.icu
        await update.message.reply_text(
            f"✅ Workout parsed successfully!\n"
            f"📝 {workout.name}\n"
            f"📅 {workout.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"💪 {len(workout.exercises)} exercises, {workout.get_total_sets()} sets\n\n"
            f"Creating activity in Intervals.icu..."
        )

        result = self.intervals_client.create_workout_activity(workout, description)

        if result:
            activity_id = result.get('id')
            activity_url = self.intervals_client.get_activity_url(activity_id)

            await update.message.reply_text(
                f"✅ **Workout created successfully!**\n\n"
                f"View it on Intervals.icu:\n{activity_url}",
                parse_mode='Markdown'
            )
            logger.info(f"Successfully created workout activity {activity_id} for user {user_id}")
        else:
            await update.message.reply_text(
                "❌ Failed to create the workout in Intervals.icu. "
                "Please check the logs or try again later."
            )
            logger.error(f"Failed to create workout activity for user {user_id}")

    def run(self):
        """Start the bot with polling."""
        logger.info("Starting bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("Stopping bot...")
        await self.application.stop()
