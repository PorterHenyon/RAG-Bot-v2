# Update Bot to Monitor New Forum Channel

## Channel ID: 1435245345448656916

---

## 🤖 Update Your Bot Configuration:

### Step 1: Find Your `.env` File

The `.env` file is where your bot runs (same folder as `bot.py`)

### Step 2: Update the Channel ID

Open your `.env` file and change this line:

```env
SUPPORT_FORUM_CHANNEL_ID=1435245345448656916
```

Replace the old channel ID with the new one: **1435245345448656916**

### Step 3: Restart the Bot

**Stop the bot** (if it's running):
- Press `Ctrl+C` in the terminal where the bot is running

**Start the bot again**:
```bash
python bot.py
```

---

## ✅ Verify It's Working:

When the bot starts, you should see:
```
✓ Monitoring channel: YourChannelName (ID: 1435245345448656916)
```

---

## 📍 Where is the `.env` File?

The `.env` file is in the same folder as your `bot.py` file.

**Full path example:**
```
C:\Users\porte\.cursor\RAG-Bot-v2\.env
```

If you don't see a `.env` file, copy `env.example` and rename it to `.env`, then add the channel ID.

---

## 🎯 Complete `.env` Example:

Your `.env` file should look something like this:

```env
# Discord Bot Token
DISCORD_BOT_TOKEN=your_bot_token_here

# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Forum Channel to Monitor
SUPPORT_FORUM_CHANNEL_ID=1435245345448656916

# Data API URL (for dashboard sync)
DATA_API_URL=https://rag-bot-v2-lcze.vercel.app/api/data
```

---

## ⚠️ Important:

- The bot must be **restarted** after changing the `.env` file
- Changes won't take effect until you restart
- Make sure the channel ID is just the number (no quotes)

---

**After updating and restarting, your bot will only monitor channel 1435245345448656916!** 🤖

