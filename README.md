# 📝 Telegram Note Bot

Why do I need another note taking solution when literally dozens of similar apps exists? Answer is simple, it takes time to adopt new app on my iPhone. Honestly, all users use only 5-6 apps on their phone. Since I use telegram as my main messaging app, I would like to have my personal bot to whom I can trust my thoughts. Also, what I don't like in all note taking apps is that I can see my notes (paradoxically) all the time. I like clean chat so i do not distract with my old notes. Thus, I needed a solution such that at any time of day I can open my primary messaging app and send note which will be saved in the simplest form to the google sheets. When I need (probably at the beginnging of day), I can open my google sheet and look through important information. 

A personal Telegram bot that saves your messages as notes in Google Sheets and sends you one random note per day at a random time between 10:00 and 22:00.

---

## 🚀 Features

- Save any message as a note
- Notes stored in Google Sheets with timestamps
- Messages auto-deleted after a short delay
- Sends back **one random note per day** at a random time
- Inline button to dismiss daily notes
- Fully asynchronous, simple, and minimal

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/telegram-note-bot.git
cd telegram-note-bot
```

### 2. Install Dependencies

Create a virtual environment (optional but recommended):

```bash
python3 -m venv venv
source venv/bin/activate
```

Install required packages:

```bash
pip install -r requirements.txt
```

### 3. Configure Your Credentials

Create a `config.py` file in the project root:

```python
TELEGRAM_TOKEN = "your-telegram-bot-token"
USER_IDS = [123456789]  # Your Telegram user ID, you can input many if you want

GOOGLE_SHEETS_CREDENTIALS_FILE = "service_account.json"
SHEET_ID = "your-google-sheet-id"
WORKSHEET_NAME = "Notes"

DELETE_DELAY = 10  # seconds
RANDOM_NOTE_MIN_HOUR = 10  # 10 AM
RANDOM_NOTE_MAX_HOUR = 22  # 10 PM
```

> 📝 To find your Telegram user ID, message [@userinfobot](https://t.me/userinfobot).

### 4. Google Sheets Setup

1. Create a Google Sheet and note the **sheet ID** from the URL.
2. Create a [service account in Google Cloud](https://cloud.google.com/iam/docs/service-accounts).
3. Download the service account key file as `service_account.json`.
4. Share the Google Sheet with the service account’s email (e.g., `your-bot@project.iam.gserviceaccount.com`).

---

## ▶️ Run the Bot

```bash
python claude_bot.py
```

The bot will:
- Save messages you send
- Delete them after a short delay
- Send back one random note per day

---

## 📦 Optional: Docker

Added dockerfile from which I built my image. Important thing to consider: bot rely on timezone information, and you need to run image with your timezone

```bash
docker run -e "TZ=YourTimeZone" your-image-name
```
Example in my case 

```bash
docker run -e "TZ=Asia/Almaty" telegram-note-bot
```
---

## 📦 To-DO

1. Add a local AI (probably LLAMA) which will read note and categorize it to the some groups: "useful quote", "gym", "remember to do", "other". Then bot should send information only from "useful quote" category.
2. Add function ‘
3. Add feature to talk with AI when message starts with "qq". i.e. When you enter grocery store you type "qq i am at grocery what I need to buy?" then AI will go through your notes and reply and disappeare after sometime. 

