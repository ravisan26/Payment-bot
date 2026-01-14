import os
import asyncio
import logging

from flask import Flask, request, Response
from telegram import Update

# Flask app for webhook
flask_app = Flask(__name__)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Import application after environment is set
from bot import application


@flask_app.route("/")
def home():
    """Health check endpoint."""
    return "✅ Bot is running!", 200


@flask_app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle incoming webhook updates."""
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return Response(status=200)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return Response(status=200)


async def setup_webhook():
    """Set up the webhook URL."""
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    else:
        logger.warning("WEBHOOK_URL not set! Set it in Render environment variables.")


def main():
    """Initialize and start the bot with webhook."""
    # Initialize the application
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Initialize bot
    loop.run_until_complete(application.initialize())
    
    # Set webhook
    loop.run_until_complete(setup_webhook())
    
    # Run Flask
    logger.info(f"Starting web server on port {PORT}")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    main()
