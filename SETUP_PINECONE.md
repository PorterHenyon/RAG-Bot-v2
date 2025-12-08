# Pinecone Vector Database Setup 🌲

Pinecone integration has been added to reduce CPU costs and improve vector search performance!

## Why Pinecone?

- **Cost-Effective**: Offloads vector storage and similarity search to Pinecone's cloud service
- **Reduced CPU Usage**: No more expensive local CPU-based vector computations
- **Scalable**: Handles large RAG databases efficiently
- **Fast**: Optimized vector search performance

## Setup Steps

### 1. Create Pinecone Account

1. Go to [https://www.pinecone.io/](https://www.pinecone.io/)
2. Sign up for a free account (free tier available!)
3. Navigate to your dashboard

### 2. Get Your API Key

1. In Pinecone dashboard, go to **API Keys**
2. Copy your API key (starts with something like `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

### 3. Create an Index (Optional - Auto-Created)

The bot will automatically create an index named `rag-bot-index` if it doesn't exist. However, you can create it manually:

1. Go to **Indexes** in Pinecone dashboard
2. Click **Create Index**
3. Name: `rag-bot-index`
4. Dimensions: `384` (for all-MiniLM-L6-v2 model)
5. Metric: `cosine`
6. Cloud: `AWS`
7. Region: `us-east-1` (or your preferred region)

### 4. Configure Environment Variables

Add these to your `.env` file:

```env
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=rag-bot-index
PINECONE_ENVIRONMENT=us-east-1

# Enable embeddings (required for Pinecone)
ENABLE_EMBEDDINGS=true
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install `pinecone-client>=3.0.0`

### 6. Restart Your Bot

The bot will automatically:
- Connect to Pinecone on startup
- Create the index if it doesn't exist
- Upload all RAG entries to Pinecone
- Use Pinecone for all vector searches

## How It Works

1. **On Startup**: Bot connects to Pinecone and initializes the index
2. **When RAG Updates**: All embeddings are computed and uploaded to Pinecone
3. **During Search**: Queries are sent to Pinecone for fast similarity search
4. **Fallback**: If Pinecone is unavailable, falls back to local vector storage or keyword search

## Monitoring

The bot will print status messages:
- `🌲 Pinecone initialized successfully` - Connection successful
- `🌲 Storing embeddings in Pinecone...` - Uploading vectors
- `🌲 Pinecone search: Found X relevant entries` - Using Pinecone for search
- `💾 Local vector search: Found X relevant entries` - Fallback to local storage

## Troubleshooting

### "Failed to initialize Pinecone"
- Check your `PINECONE_API_KEY` is correct
- Verify your internet connection
- Check Pinecone dashboard for service status

### "Index not found"
- The bot will auto-create the index, but you can create it manually in the dashboard
- Make sure `PINECONE_INDEX_NAME` matches your index name

### "Falling back to local storage"
- This is normal if Pinecone is temporarily unavailable
- Bot will continue working with local vector search
- Check Pinecone connection and API key

## Cost Savings

With Pinecone:
- ✅ No CPU-intensive local vector computations
- ✅ Reduced server costs
- ✅ Free tier available (up to 100K vectors)
- ✅ Pay-as-you-go pricing for larger databases

## Migration Notes

- Existing RAG entries will be automatically uploaded to Pinecone on first run
- No data loss - local fallback still available
- Can switch back to local storage by removing `PINECONE_API_KEY`

