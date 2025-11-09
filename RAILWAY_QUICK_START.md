# 🚂 Railway Quick Start - 5 Minutes to Deploy!

## ⚡ Super Fast Setup

### 1️⃣ Create Account (1 minute)
1. Go to https://railway.app
2. Click **"Login"** → **"Login with GitHub"**
3. Authorize Railway

### 2️⃣ Deploy Bot (1 minute)
1. Click **"New Project"**
2. Click **"Deploy from GitHub repo"**
3. Select **`PorterHenyon/RAG-Bot-v2`**
4. Railway auto-detects Python and starts building!

### 3️⃣ Add Environment Variables (2 minutes)

Click on your deployed service, then click **"Variables"** tab.

Click **"RAW Editor"** and paste this (replace with YOUR values):

```
DISCORD_BOT_TOKEN=paste_your_discord_bot_token_here
GEMINI_API_KEY=paste_your_gemini_api_key_here
SUPPORT_FORUM_CHANNEL_ID=1435455947551150171
DISCORD_GUILD_ID=paste_your_server_id_here
DATA_API_URL=https://your-vercel-app.vercel.app/api/data
```

**Where to get these values:**
- **DISCORD_BOT_TOKEN**: https://discord.com/developers/applications → Your App → Bot → Reset Token
- **GEMINI_API_KEY**: https://aistudio.google.com/app/apikey
- **SUPPORT_FORUM_CHANNEL_ID**: Already set to your channel!
- **DISCORD_GUILD_ID**: Right-click your Discord server icon → Copy ID
- **DATA_API_URL**: Your Vercel dashboard URL + `/api/data`

### 4️⃣ Deploy! (1 minute)
1. Click **"Deploy"** button (or it auto-deploys)
2. Wait for green checkmark ✅
3. Click **"View Logs"** to watch bot start!

---

## ✅ Verify It's Working

**In Railway Logs, look for:**
```
Logged in as [Your Bot Name] (ID: ...)
✓ Monitoring channel: [channel name] (ID: 1435455947551150171)
```

**In Discord:**
- Your bot should show as "Online" 🟢
- Create a test forum post
- Bot should respond within 2-3 seconds!

---

## 🔧 Common Issues

### ❌ Bot shows offline in Discord?
**Fix:** Enable **MESSAGE CONTENT INTENT** in Discord Developer Portal
1. Go to https://discord.com/developers/applications
2. Click your bot → Bot tab
3. Enable "MESSAGE CONTENT INTENT"
4. Save → Restart bot in Railway (Settings → Restart)

### ❌ Railway build fails?
**Fix:** Check `requirements.txt` exists in your repo
- Should be there already!
- If not, push latest code from GitHub

### ❌ "DISCORD_BOT_TOKEN not found" in logs?
**Fix:** Make sure all 5 variables are set in Railway Variables tab

---

## 🎉 That's It!

Your bot is now:
- ✅ Running 24/7
- ✅ Auto-deploying from GitHub (push code → auto updates)
- ✅ Easy to monitor in Railway dashboard

**Full guide:** See `RAILWAY_SETUP.md` for detailed instructions!

---

## 💰 Cost

- **Free trial:** $5 credit (enough for testing)
- **After trial:** ~$3-5/month (way cheaper than most hosts!)
- **Small bot like yours:** Usually $3/month

**Much better than Fly.io!** 🚀

