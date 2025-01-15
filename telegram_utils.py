import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Telegram credentials from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    """
    Sends a message to a specific Telegram chat using the Telegram Bot API.

    :param message: The message text to send.
    :return: The response from the API call.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }

    # Send the request to Telegram API
    response = requests.post(url, data=payload)

    # Check the response and return it
    if response.status_code == 200:
        return "Message sent successfully."
    else:
        return f"Failed to send message: {response.text}"