# Railway + Pinecone Environment Variables Setup 🚂🌲

Complete guide for setting up environment variables in Railway for your Discord bot with Pinecone integration.

## 📋 Overview

**Railway** (hosting platform) needs environment variables to:
- Connect to Discord
- Use Gemini API
- Connect to Pinecone
- Access your dashboard API

**Pinecone** (vector database) doesn't need environment variables - it's a cloud service. Your bot on Railway just needs the API key to connect to it.

---

## 🔧 Required Environment Variables for Railway

### 1. **Discord Bot Configuration** (Required)

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
SUPPORT_FORUM_CHANNEL_ID=your_forum_channel_id_here
DISCORD_GUILD_ID=your_server_guild_id_here
```

**Where to get:**
- `DISCORD_BOT_TOKEN`: [Discord Developer Portal](https://discord.com/developers/applications) → Your App → Bot → Reset Token
- `SUPPORT_FORUM_CHANNEL_ID`: Right-click your forum channel → Copy ID
- `DISCORD_GUILD_ID`: Right-click your server → Copy ID

---

### 2. **Gemini API Configuration** (Required)

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

**Optional:** Add more keys for rate limit handling:
```env
GEMINI_API_KEY_2=your_second_api_key_here
GEMINI_API_KEY_3=your_third_api_key_here
# ... up to GEMINI_API_KEY_20
```

**Where to get:**
- [Google AI Studio](https://aistudio.google.com/app/apikey) → Create API Key

---

### 3. **Dashboard API URL** (Required)

```env
DATA_API_URL=https://your-app.vercel.app/api/data
```

**Where to get:**
- Your Vercel deployment URL + `/api/data`

---

### 4. **Pinecone Configuration** (Required for Vector Search)

```env
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=rag-bot-index
PINECONE_ENVIRONMENT=us-east-1
ENABLE_EMBEDDINGS=true
```

**Where to get:**
- `PINECONE_API_KEY`: [Pinecone Dashboard](https://app.pinecone.io/) → API Keys → Copy
- `PINECONE_INDEX_NAME`: Default is `rag-bot-index` (bot will create it automatically)
- `PINECONE_ENVIRONMENT`: Region (default: `us-east-1`)
- `ENABLE_EMBEDDINGS`: Set to `true` to enable Pinecone vector search

**Pinecone Setup:**
1. Sign up at [https://www.pinecone.io/](https://www.pinecone.io/)
2. Get your API key from the dashboard
3. The bot will automatically create the index on first run

---

## 🚀 How to Add Environment Variables in Railway

### Method 1: Railway Dashboard (Recommended)

1. **Go to Railway Dashboard**
   - Visit [https://railway.app/](https://railway.app/)
   - Select your project

2. **Open Environment Variables**
   - Click on your service
   - Go to **Variables** tab
   - Click **+ New Variable**

3. **Add Each Variable**
   - **Name:** `DISCORD_BOT_TOKEN`
   - **Value:** `your_actual_token_here`
   - Click **Add**
   - Repeat for all variables

4. **Redeploy**
   - Railway will automatically redeploy when you add variables
   - Or click **Deploy** → **Redeploy**

### Method 2: Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Add variables
railway variables set DISCORD_BOT_TOKEN=your_token_here
railway variables set GEMINI_API_KEY=your_key_here
railway variables set PINECONE_API_KEY=your_pinecone_key_here
# ... etc
```

---

## ✅ Complete Environment Variables Checklist

Copy this checklist and mark off as you add each variable:

### Required (Bot won't work without these)
- [ ] `DISCORD_BOT_TOKEN`
- [ ] `GEMINI_API_KEY`
- [ ] `SUPPORT_FORUM_CHANNEL_ID`
- [ ] `DISCORD_GUILD_ID`
- [ ] `DATA_API_URL`

### Required for Pinecone Vector Search
- [ ] `PINECONE_API_KEY`
- [ ] `ENABLE_EMBEDDINGS=true`
- [ ] `PINECONE_INDEX_NAME=rag-bot-index` (optional, has default)
- [ ] `PINECONE_ENVIRONMENT=us-east-1` (optional, has default)

### Optional (for better performance)
- [ ] `GEMINI_API_KEY_2` (additional keys for rate limit handling)
- [ ] `GEMINI_API_KEY_3`
- [ ] ... (up to `GEMINI_API_KEY_20`)

---

## 🧪 Verify Your Setup

### 1. Check Railway Logs

After deploying, check Railway logs. You should see:

```
✓ Loaded API key from GEMINI_API_KEY
✓ Loaded 1 valid API key(s) for all operations
🌲 Pinecone vector search enabled - cost-effective cloud-based vector search
🌲 Initializing Pinecone connection...
✅ Pinecone initialized successfully
```

### 2. Test Pinecone Connection

Run the test script locally (or on Railway):

```bash
# On Railway
railway run python test_pinecone.py

# Or locally (if you have .env file)
python test_pinecone.py
```

Expected output:
```
🌲 Connecting to Pinecone...
📋 Checking index: rag-bot-index
📊 Existing indexes: ['rag-bot-index']
✅ Index 'rag-bot-index' exists!
✅ Pinecone connection test completed successfully!
```

### 3. Test Bot Startup

Check Railway logs when bot starts. Look for:
- ✅ No "FATAL ERROR" messages
- ✅ "Pinecone initialized successfully"
- ✅ Bot connects to Discord

---

## 🔍 Troubleshooting

### "FATAL ERROR: 'DISCORD_BOT_TOKEN' not found"
- **Fix:** Add `DISCONE_BOT_TOKEN` to Railway environment variables
- **Check:** Railway → Variables tab → Make sure it's spelled correctly

### "FATAL ERROR: No Gemini API keys found"
- **Fix:** Add `GEMINI_API_KEY` to Railway environment variables
- **Check:** Make sure the key is valid and not expired

### "⚠️ Pinecone not installed"
- **Fix:** Make sure `pinecone-client>=3.0.0` is in `requirements.txt`
- **Check:** Railway should auto-install from requirements.txt

### "Failed to initialize Pinecone"
- **Check:** `PINECONE_API_KEY` is set correctly in Railway
- **Check:** API key is valid (not expired, correct format)
- **Check:** Internet connection from Railway to Pinecone

### "Index not found"
- **Normal:** Bot will auto-create the index on first run
- **Or:** Create manually in Pinecone dashboard

### Bot uses keyword search instead of Pinecone
- **Check:** `ENABLE_EMBEDDINGS=true` is set
- **Check:** `PINECONE_API_KEY` is set
- **Check:** Railway logs for Pinecone initialization messages

---

## 📊 Environment Variables Summary

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DISCORD_BOT_TOKEN` | ✅ Yes | - | Discord bot authentication |
| `GEMINI_API_KEY` | ✅ Yes | - | Google Gemini AI API |
| `SUPPORT_FORUM_CHANNEL_ID` | ✅ Yes | - | Discord forum channel |
| `DISCORD_GUILD_ID` | ✅ Yes | - | Discord server ID |
| `DATA_API_URL` | ✅ Yes | - | Dashboard API endpoint |
| `PINECONE_API_KEY` | ✅ For Pinecone | - | Pinecone authentication |
| `ENABLE_EMBEDDINGS` | ✅ For Pinecone | `false` | Enable vector search |
| `PINECONE_INDEX_NAME` | ❌ No | `rag-bot-index` | Pinecone index name |
| `PINECONE_ENVIRONMENT` | ❌ No | `us-east-1` | Pinecone region |
| `GEMINI_API_KEY_2-20` | ❌ No | - | Additional Gemini keys |

---

## 🎯 Quick Setup Steps

1. **Get all your API keys:**
   - Discord Bot Token
   - Gemini API Key
   - Pinecone API Key

2. **Add to Railway:**
   - Railway Dashboard → Your Project → Variables
   - Add each variable one by one

3. **Redeploy:**
   - Railway will auto-redeploy, or click Redeploy manually

4. **Verify:**
   - Check Railway logs for success messages
   - Test bot commands in Discord
   - Run `test_pinecone.py` to verify Pinecone connection

---

## 💡 Pro Tips

1. **Use Railway's Variable Groups** to share variables across services
2. **Never commit `.env` files** to Git (they're in `.gitignore`)
3. **Test locally first** with a `.env` file before deploying to Railway
4. **Keep API keys secure** - Railway encrypts them automatically
5. **Use Railway's secrets** for sensitive data (they're encrypted at rest)

---

## 🔗 Quick Links

- [Railway Dashboard](https://railway.app/dashboard)
- [Pinecone Dashboard](https://app.pinecone.io/)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Google AI Studio](https://aistudio.google.com/app/apikey)

---

## ✅ Final Checklist

Before deploying, make sure:
- [ ] All required environment variables are set in Railway
- [ ] `PINECONE_API_KEY` is added (if using Pinecone)
- [ ] `ENABLE_EMBEDDINGS=true` is set (if using Pinecone)
- [ ] `requirements.txt` includes `pinecone-client>=3.0.0`
- [ ] Railway service is connected to your GitHub repo
- [ ] Bot has proper Discord permissions

Your bot should now be ready to run with Pinecone! 🎉

