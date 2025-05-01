import os
import time
import random
import pandas as pd
import schedule
import threading
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from google.oauth2.service_account import Credentials
import gspread

# Import configuration - adjust the import based on your file location
from config import (
    TELEGRAM_TOKEN, 
    USER_ID, 
    SHEET_ID, 
    WORKSHEET_NAME, 
    GOOGLE_SHEETS_CREDENTIALS_FILE,
    DELETE_DELAY,
    RANDOM_NOTE_MIN_HOUR,
    RANDOM_NOTE_MAX_HOUR
)

# Global application reference for schedulers
app = None
scheduler_loop = None

# Set up Google Sheets connection
def setup_google_sheets():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = Credentials.from_service_account_file(
        GOOGLE_SHEETS_CREDENTIALS_FILE, 
        scopes=scopes
    )
    
    client = gspread.authorize(credentials)
    
    # Open your existing spreadsheet using the SHEET_ID
    spreadsheet = client.open_by_key(SHEET_ID)
    
    # Check if worksheet exists, if not create it
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(WORKSHEET_NAME, 1000, 2)
        # Add headers
        worksheet.append_row(["Note", "Timestamp"])
    
    return worksheet

# Save note to Google Sheets
async def save_note_to_sheets(note, worksheet):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    worksheet.append_row([note, timestamp])
    print(f"Note saved: {note[:30]}... at {timestamp}")

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to your private note-taking bot! Just send me any message and I'll save it as a note."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just send me any message and I'll save it as a note.\n"
        f"I'll delete the message after {DELETE_DELAY} seconds to keep your chat clean.\n\n"
        "Random notes will be sent to you periodically, and will be deleted after you react to them."
    )

# Handle incoming messages (notes)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Save the note to Google Sheets
    worksheet = context.bot_data["worksheet"]
    await save_note_to_sheets(user_message, worksheet)
    
    # Send confirmation (will be deleted soon)
    confirmation = await update.message.reply_text("Note saved! This message will disappear soon...")
    
    # Delete the user's message after the configured delay
    await asyncio.sleep(DELETE_DELAY)
    try:
        await update.message.delete()
        await confirmation.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

# Handle button callback (for random note interaction)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Get the message that contains the button
    message = query.message
    
    # Delete the message after the user has interacted with it
    try:
        await message.delete()
        print(f"Random note deleted after user interaction at {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"Error deleting message after callback: {e}")

# Send a random note to the user with a reaction button
async def send_random_note():
    global app
    if not app:
        print("Error: Application not initialized")
        return
        
    try:
        worksheet = app.bot_data["worksheet"]
        
        # Get all notes from the sheet
        all_values = worksheet.get_all_values()
        
        # Skip header row
        if len(all_values) <= 1:
            print("No notes available to send")
            return
        
        # Select a random note (skip header row)
        random_row = random.choice(all_values[1:])
        random_note = random_row[0]  # Note is in the first column
        timestamp = random_row[1] if len(random_row) > 1 else "unknown time"  # Timestamp is in the second column
        
        # Create an inline keyboard with a "Got it" button
        keyboard = [
            [InlineKeyboardButton("👍 Got it", callback_data="delete_note")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the note to the user with the inline keyboard
        sent_message = await app.bot.send_message(
            chat_id=USER_ID,
            text=f"📝 Random note from your collection:\n\n{random_note}\n\nOriginally saved: {timestamp}\n\n(Click 'Got it' to dismiss this message)",
            reply_markup=reply_markup
        )
        print(f"Sent random note to user at {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"Error sending random note: {e}")
        import traceback
        traceback.print_exc()

# Create a new event loop for the scheduler
def create_scheduler_loop():
    global scheduler_loop
    scheduler_loop = asyncio.new_event_loop()
    return scheduler_loop

# Run an async function in the scheduler's event loop
def run_in_scheduler_loop(coro):
    global scheduler_loop
    
    if scheduler_loop is None or scheduler_loop.is_closed():
        scheduler_loop = create_scheduler_loop()
    
    future = asyncio.run_coroutine_threadsafe(coro, scheduler_loop)
    
    try:
        # Wait for the result with a timeout
        return future.result(60)  # 60 second timeout
    except Exception as e:
        print(f"Error in scheduler task: {e}")
        import traceback
        traceback.print_exc()
        return None

# Schedule random notes
def schedule_random_notes():
    # Start the scheduler loop in a separate thread
    def run_scheduler_loop():
        global scheduler_loop
        scheduler_loop = create_scheduler_loop()
        asyncio.set_event_loop(scheduler_loop)
        scheduler_loop.run_forever()
    
    scheduler_thread = threading.Thread(target=run_scheduler_loop, daemon=True)
    scheduler_thread.start()
    
    # Function to send a random note
    def send_note_wrapper():
        try:
            # Run the coroutine in the scheduler's event loop
            run_in_scheduler_loop(send_random_note())
            print("Random note task executed")
        except Exception as e:
            print(f"Error in send_note_wrapper: {e}")
            import traceback
            traceback.print_exc()
    
    # Schedule a random note to be sent at a random time between configured hours
    def random_schedule():
        # Generate random hour and minute
        hour = random.randint(RANDOM_NOTE_MIN_HOUR, RANDOM_NOTE_MAX_HOUR)
        minute = random.randint(0, 59)
        
        # Schedule the job for today at the random time
        schedule_time = f"{hour:02d}:{minute:02d}"
        schedule.every().day.at(schedule_time).do(send_note_wrapper)
        print(f"Scheduled random note for {schedule_time}")
    
    # For testing - send a note every few minutes
    # schedule.every(5).minutes.do(send_note_wrapper)
    # print("Scheduled a test note to be sent every 5 minutes")
    
    # Regular daily scheduling
    random_schedule()
    schedule.every().day.at("00:01").do(random_schedule)
    
    # Run the scheduler in a separate thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(10)  # Check every 10 seconds
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

async def main():
    global app
    
    # Set up Google Sheets
    worksheet = setup_google_sheets()
    
    # Set up Telegram bot
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.bot_data["worksheet"] = worksheet
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler
    async def error_handler(update, context):
        print(f"Exception while handling an update: {context.error}")
        import traceback
        traceback.format_exception(None, context.error, context.error.__traceback__)
    
    app.add_error_handler(error_handler)
    
    # Start the bot
    await app.initialize()
    await app.start()
    
    # Schedule random notes
    schedule_random_notes()
    
    # Run the bot until the user presses Ctrl-C
    print("Bot started. Press Ctrl+C to stop.")
    
    # This is the key change - using a simpler approach for running the bot
    stop_event = asyncio.Event()
    
    # Create a task that will wait for user to press Ctrl+C
    asyncio.create_task(app.updater.start_polling(drop_pending_updates=True))
    
    # Handle Ctrl+C gracefully
    try:
        # Wait until the stop event is set (by Ctrl+C handler)
        await stop_event.wait()
    except KeyboardInterrupt:
        # This will catch Ctrl+C
        print("Bot is shutting down...")
    finally:
        # Stop the bot
        await app.stop()
        await app.shutdown()
        
        # Clean up the scheduler loop
        global scheduler_loop
        if scheduler_loop and not scheduler_loop.is_closed():
            scheduler_loop.call_soon_threadsafe(scheduler_loop.stop)
            scheduler_loop.call_soon_threadsafe(scheduler_loop.close)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user!")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()