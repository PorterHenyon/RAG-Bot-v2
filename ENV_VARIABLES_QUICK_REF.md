# Environment Variables Quick Reference 📝

## 🎯 TL;DR

**Railway needs these environment variables** (set them in Railway Dashboard → Variables):
- Discord bot token
- Gemini API key
- Pinecone API key (if using Pinecone)
- Other config values

**Pinecone doesn't need environment variables** - it's a cloud service. Your bot just needs the API key to connect.

---

## ✅ Required Variables (Railway)

### Must Have (Bot won't start without these):
```env
DISCORD_BOT_TOKEN=xxx
GEMINI_API_KEY=xxx
SUPPORT_FORUM_CHANNEL_ID=xxx
DISCORD_GUILD_ID=xxx
DATA_API_URL=https://your-app.vercel.app/api/data
```

### For Pinecone Vector Search:
```env
PINECONE_API_KEY=xxx
ENABLE_EMBEDDINGS=true
PINECONE_INDEX_NAME=rag-bot-index        # Optional (has default)
PINECONE_ENVIRONMENT=us-east-1            # Optional (has default)
```

---

## 🚀 Quick Setup in Railway

1. **Railway Dashboard** → Your Project → **Variables** tab
2. Click **+ New Variable**
3. Add each variable from the list above
4. **Redeploy** (automatic or manual)

---

## 📋 Complete List

| Variable | Required | Where to Get |
|----------|----------|--------------|
| `DISCORD_BOT_TOKEN` | ✅ Yes | Discord Developer Portal |
| `GEMINI_API_KEY` | ✅ Yes | Google AI Studio |
| `SUPPORT_FORUM_CHANNEL_ID` | ✅ Yes | Discord (right-click channel) |
| `DISCORD_GUILD_ID` | ✅ Yes | Discord (right-click server) |
| `DATA_API_URL` | ✅ Yes | Your Vercel deployment URL |
| `PINECONE_API_KEY` | ✅ For Pinecone | Pinecone Dashboard |
| `ENABLE_EMBEDDINGS` | ✅ For Pinecone | Set to `true` |
| `PINECONE_INDEX_NAME` | ❌ No | Default: `rag-bot-index` |
| `PINECONE_ENVIRONMENT` | ❌ No | Default: `us-east-1` |

---

## 🔍 How to Verify

After adding variables, check Railway logs. You should see:

✅ **Success:**
```
✓ Loaded API key from GEMINI_API_KEY
🌲 Pinecone vector search enabled
🌲 Initializing Pinecone connection...
✅ Pinecone initialized successfully
```

❌ **If Missing:**
```
FATAL ERROR: 'DISCORD_BOT_TOKEN' not found in environment.
```

---

## 📚 Full Documentation

See `RAILWAY_PINECONE_SETUP.md` for detailed setup instructions.

