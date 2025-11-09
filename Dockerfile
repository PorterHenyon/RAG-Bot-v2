# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only bot files (not frontend)
COPY requirements.txt .
COPY bot.py .
COPY bot_settings.json* ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create directory for local RAG storage
RUN mkdir -p localrag

# Run the bot
CMD ["python", "-u", "bot.py"]

