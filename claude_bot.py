import asyncio
import random
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from config import (
    TELEGRAM_TOKEN, USER_IDS, SHEET_ID, WORKSHEET_NAME,
    GOOGLE_SHEETS_CREDENTIALS_FILE, DELETE_DELAY,
    RANDOM_NOTE_MIN_HOUR, RANDOM_NOTE_MAX_HOUR
)
import nest_asyncio

nest_asyncio.apply()

# --- TEMP: for testing random note scheduling ---
# def random_time():
#     """TEMPORARY: Returns a datetime 1–2 minutes from now (for testing)."""
#     now = datetime.now()
#     return (now + timedelta(minutes=random.randint(1, 2))).replace(second=0, microsecond=0)

# --- PROD: real random time between 10:00 and 22:00 ---
def random_time():
    """Returns a random datetime today between 10:00 and 22:00."""
    now = datetime.now()
    hour = random.randint(RANDOM_NOTE_MIN_HOUR, RANDOM_NOTE_MAX_HOUR)
    minute = random.randint(0, 59)
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

# Set up Google Sheets connection
def setup_google_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(WORKSHEET_NAME, 1000, 2)
        worksheet.append_row(["Note", "Timestamp"])
    return worksheet

# Save note to Google Sheets
async def save_note(note, worksheet):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    worksheet.append_row([note, timestamp])
    print(f"Saved: {note[:30]}... at {timestamp}")

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send me any message to save it as a note.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send any message to save it. I’ll delete it after a few seconds and send you one note daily.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # accept only authorized users' message 
    if update.message.from_user.id not in context.bot_data["user_ids"]:
        await update.message.reply_text("You're not authorized to use this bot.")
        return
    
    note = update.message.text
    worksheet = context.bot_data["worksheet"]
    await save_note(note, worksheet)

    confirm = await update.message.reply_text("Note saved. This will disappear...")
    await asyncio.sleep(DELETE_DELAY)
    try:
        await update.message.delete()
        await confirm.delete()
    except:
        pass

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
        await update.callback_query.message.delete()
    except:
        pass

# Send one random note
async def send_random_note(app: Application):
    worksheet = app.bot_data["worksheet"]
    rows = worksheet.get_all_values()[1:]  # skip header
    if not rows:
        print("No notes to send.")
        return

    row = random.choice(rows)
    note = row[0]
    timestamp = row[1] if len(row) > 1 else "unknown"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("👍 Got it", callback_data="delete_note")]
    ])

    # Send to all user IDs
    for user_id in app.bot_data["user_ids"]:
        await app.bot.send_message(
            chat_id=user_id,
            text=f"📝 Random note:\n\n{note}\n\nSaved: {timestamp}",
            reply_markup=reply_markup
        )
        print(f"Sent random note to {user_id} at {datetime.now().strftime('%H:%M')}")

# Run once per day, at a random time between 10–22
async def schedule_daily_note(app: Application):
    while True:
        target = random_time()
        now = datetime.now()

        # If the time has already passed today, set for tomorrow
        if target <= now:
            target += timedelta(days=1)

        print(f"Next random note scheduled for {target.strftime('%Y-%m-%d %H:%M')}")
        await asyncio.sleep((target - now).total_seconds())

        try:
            await send_random_note(app)
        except Exception as e:
            print(f"Error sending random note: {e}")

        # Wait until next day
        tomorrow = target + timedelta(days=1)
        midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_time = (midnight - datetime.now()).total_seconds()
        await asyncio.sleep(max(sleep_time, 0))

# Entry point
async def main():
    worksheet = setup_google_sheets()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.bot_data["worksheet"] = worksheet
    app.bot_data["user_ids"] = USER_IDS  # support multiple users

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    asyncio.create_task(schedule_daily_note(app))
    print("Bot running... Press Ctrl+C to stop.")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
