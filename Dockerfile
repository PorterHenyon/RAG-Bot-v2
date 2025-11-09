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

# Create localrag directory (bot will populate it)
RUN mkdir -p localrag

# Run the bot
CMD ["python", "-u", "bot.py"]

