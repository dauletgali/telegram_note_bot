# config.py
# Store all your sensitive credentials and configuration in this file
import os
from dotenv import load_dotenv
load_dotenv()
# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
USER_IDS = list(map(int, os.getenv("USER_IDS", "").split(",")))  # This is your personal Telegram user ID or you may choose many users if you want. 

# Google Sheets Configuration
SHEET_ID = os.getenv("SHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")  # Change if you use a different name
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")  # Path to your Google API credentials file

# Bot Behavior Configuration
DELETE_DELAY = 5  # Time in seconds before messages are deleted
RANDOM_NOTE_MIN_HOUR = 10  # Earliest hour to send random notes (24-hour format)
RANDOM_NOTE_MAX_HOUR = 22  # Latest hour to send random notes (24-hour format)
