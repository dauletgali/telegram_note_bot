# config.py
# Store all your sensitive credentials and configuration in this file

# Telegram Bot Configuration
TELEGRAM_TOKEN = "TELEGRAM_BOT_TOKEN"
USER_IDS = ["USERID"]  # This is your personal Telegram user ID or you may choose many users if you want. 

# Google Sheets Configuration
SHEET_ID = "SHEETID" 
WORKSHEET_NAME = "Notes"  # Change if you use a different name
GOOGLE_SHEETS_CREDENTIALS_FILE = "PATH_TO_CREDENTIALS"  # Path to your Google API credentials file

# Bot Behavior Configuration
DELETE_DELAY = 5  # Time in seconds before messages are deleted
RANDOM_NOTE_MIN_HOUR = 10  # Earliest hour to send random notes (24-hour format)
RANDOM_NOTE_MAX_HOUR = 22  # Latest hour to send random notes (24-hour format)
