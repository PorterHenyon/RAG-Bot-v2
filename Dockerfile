# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code
COPY bot.py .
COPY bot_settings.json .

# Create localrag directory
RUN mkdir -p localrag

# Copy localrag files if they exist
COPY localrag/ ./localrag/ 2>/dev/null || true

# Run the bot
CMD ["python", "-u", "bot.py"]

