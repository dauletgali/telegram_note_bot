# Use official slim Python image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy only requirement files first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the bot files
COPY claude_bot.py config.py creds.json ./

# If you add other files in the future, just COPY . ./

# Set default command to run the bot
CMD ["python", "claude_bot.py"]
