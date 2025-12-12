# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only bot files (not frontend)
COPY requirements.txt .
COPY bot.py .
COPY bot_settings.json* ./

# Install Python dependencies
# Remove old pinecone-client package if it exists (conflicts with new pinecone package)
RUN pip install --no-cache-dir --upgrade pip && \
    pip uninstall -y pinecone-client 2>/dev/null || true && \
    pip install --no-cache-dir -r requirements.txt

# Skip model download during build (saves ~5-10 minutes)
# Model will be downloaded at runtime only if needed (when SKIP_EMBEDDING_BOOTSTRAP=false)
# Since Railway uses SKIP_EMBEDDING_BOOTSTRAP=true, this is never needed on Railway
# Uncomment below if you need to pre-cache the model for local development:
# RUN python -c "from sentence_transformers import SentenceTransformer; print('Downloading model...'); SentenceTransformer('all-MiniLM-L6-v2'); print('Model cached successfully')" 2>&1 || (echo "⚠️ Model download failed during build (will retry at runtime)" && exit 0)

# No local storage needed - all data in Vercel KV API

# Run the bot
CMD ["python", "-u", "bot.py"]

