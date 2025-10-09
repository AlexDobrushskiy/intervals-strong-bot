# Strong → Intervals.icu Telegram Bot

Automatically sync your weight training workouts from the Strong app to your Intervals.icu activities via Telegram.

## Features

- 🏋️ **Automatic Workout Parsing**: Reads workouts shared from the Strong app
- 📊 **Smart Processing**: Extracts exercises, sets, reps, and weights
- 📅 **Activity Tracking**: Creates completed activities in your Intervals.icu account
- 🌍 **Multi-language Support**: Works with Portuguese and English Strong exports
- ⚡ **Real-time Processing**: Instant feedback and confirmation
- 💪 **Comprehensive Format Support**: Handles weighted exercises, bodyweight exercises, and timed activities

## Prerequisites

- Python 3.8 or higher
- A Telegram account
- A Strong app account (iOS/Android)
- An Intervals.icu account with API access

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the prompts to choose a name and username for your bot
4. **Save the bot token** - you'll need it for configuration
5. Find your bot in Telegram and start a chat with it

### 2. Get Intervals.icu Credentials

1. Log in to [Intervals.icu](https://intervals.icu)
2. Go to Settings (click your profile icon)
3. Scroll down to **Developer Settings**
4. Click **Generate API Key**
5. **Save your API key** - it won't be shown again
6. Note your **Athlete ID** (visible in your profile URL: `intervals.icu/athlete/YOUR_ID`)

### 3. Install the Bot

```bash
# Clone or download this repository
cd intervals-icu-bot

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure the Bot

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   INTERVALS_API_KEY=your_intervals_icu_api_key_here
   INTERVALS_ATHLETE_ID=your_athlete_id_here
   LOG_LEVEL=INFO
   ```

### 5. Run the Bot

```bash
python main.py
```

You should see output like:
```
INFO - Validating configuration...
INFO - Initializing Intervals.icu client...
INFO - Testing Intervals.icu connection...
INFO - Connection to Intervals.icu successful!
INFO - Bot is ready! Starting polling...
```

## Usage

### Sending Workouts to the Bot

1. **Complete your workout** in the Strong app
2. **Open the workout** in Strong
3. **Tap the share button** (usually three dots or a share icon)
4. **Choose "Share"**
5. **Select Telegram** from the share options
6. **Send to your bot** (the one you created with BotFather)

The bot will:
- ✅ Parse your workout data
- ✅ Create a completed activity in Intervals.icu
- ✅ Send you a confirmation with a link to view it

### Bot Commands

- `/start` - Show welcome message and instructions
- `/help` - Display detailed usage instructions
- `/test` - Test the connection to Intervals.icu

### Example Workout Format

The bot understands workouts in this format (from Strong app):

```
Treino da noite
quarta-feira, 8 de outubro de 2025 às 21:16

Back Extension
Série 1: +0 kg × 20 reps
Série 2: +10 kg × 20 reps

Bench Press (Barbell)
W: 40 kg × 10 reps
Série 1: 60 kg × 12 reps
Série 2: 60 kg × 12 reps

Pull Up
Série 1: 9 reps
Série 2: 6 reps

Stretching
Série 1: 7:00
```

The bot handles:
- ✅ Exercises with weight and reps
- ✅ Warmup sets (marked with `W:`)
- ✅ Bodyweight exercises (no weight)
- ✅ Timed exercises (e.g., stretching, planks)

## How It Works

1. **Message Reception**: Bot receives workout text via Telegram
2. **Format Detection**: Identifies Strong app workout format
3. **Parsing**: Extracts workout name, date, exercises, sets, reps, weights
4. **Calculation**: Estimates duration and training load
5. **API Call**: Creates manual workout activity in Intervals.icu
6. **Confirmation**: Sends success message with link to view workout

### Training Load Estimation

The bot estimates training load based on total volume (weight × reps):
- Formula: `total_volume / 1000`
- Minimum load: 10
- Default (no volume): 50

### Duration Estimation

The bot estimates workout duration based on:
- 2 minutes per set (includes rest)
- 1 minute per exercise transition
- Example: 12 sets across 5 exercises = ~29 minutes

## Deployment Options

### Local Development

Run the bot on your local machine (as described above):
```bash
python main.py
```

### Server Deployment

Deploy to a VPS or cloud server (Ubuntu example):

```bash
# Install Python and dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Clone and setup
git clone <your-repo>
cd intervals-icu-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env file
nano .env

# Run with systemd (create a service file)
sudo nano /etc/systemd/system/intervals-bot.service
```

Example systemd service file:
```ini
[Unit]
Description=Intervals.icu Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/intervals-icu-bot
Environment="PATH=/path/to/intervals-icu-bot/venv/bin"
ExecStart=/path/to/intervals-icu-bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable intervals-bot
sudo systemctl start intervals-bot
```

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t intervals-bot .
docker run -d --name intervals-bot --env-file .env intervals-bot
```

## Troubleshooting

### Bot doesn't respond
- Check that the bot is running (`python main.py`)
- Verify your Telegram bot token is correct
- Make sure you've started a chat with your bot in Telegram

### "Connection failed" error
- Verify your Intervals.icu API key is correct
- Check your athlete ID is correct
- Ensure you have internet connectivity

### Workout not parsed correctly
- Make sure you're sharing directly from Strong app
- Check that the workout format matches the expected structure
- Look at the logs for parsing errors (set `LOG_LEVEL=DEBUG`)

### API errors
- Check Intervals.icu is accessible (not down)
- Verify your API key hasn't been revoked
- Look for rate limiting issues in logs

## File Structure

```
intervals-icu-bot/
├── main.py                # Entry point
├── config.py              # Configuration management
├── telegram_bot.py        # Telegram bot handlers
├── strong_parser.py       # Strong app workout parser
├── intervals_client.py    # Intervals.icu API client
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Security Notes

- **Never commit your `.env` file** - it contains sensitive credentials
- Keep your API keys secure
- Consider using environment variables in production
- Rotate your API keys periodically
- Use HTTPS for any webhooks (if implementing webhook mode)

## Limitations

- Bot must be running to process messages (use a server for 24/7 operation)
- Intervals.icu doesn't have structured strength training format (uses descriptions)
- Training load estimation is approximate
- Duration estimation may not match actual workout time

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## License

MIT License - feel free to use and modify as needed.

## Support

If you encounter issues:
1. Check the troubleshooting section
2. Review the logs (set `LOG_LEVEL=DEBUG`)
3. Open an issue with details about the problem

## Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [Intervals.icu](https://intervals.icu) - Training analytics platform
- [Strong](https://www.strong.app) - Workout tracking app
