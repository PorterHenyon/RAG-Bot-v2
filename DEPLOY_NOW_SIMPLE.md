# 🚀 Deploy Your Bot RIGHT NOW - Simple Guide

## ✅ Current Status

- ✅ Fly.io CLI installed (v0.3.209)
- ✅ All code pushed to GitHub
- ✅ Configuration files ready
- ⏳ Need to create app and deploy

**Time needed: 10 minutes**

---

## 📋 Exact Commands to Run

### **1. Login to Fly.io** (Opens browser)

```bash
fly auth login
```

✅ Sign up for FREE account (no credit card!)

---

### **2. Create Your App**

```bash
fly launch --no-deploy
```

**When it asks questions, just press Enter for everything:**
- App name? → **Press Enter** (uses "rag-bot-v2")
- Region? → **Press Enter** (uses default)
- PostgreSQL? → Type `n` → **Press Enter**
- Redis? → Type `n` → **Press Enter**
- Deploy now? → Type `n` → **Press Enter**

✅ App "rag-bot-v2" created!

---

### **3. Set Your Secrets** ⚠️ IMPORTANT

You need 5 secrets. I'll show you where to find each value, then the command to set it.

#### Secret 1: Discord Bot Token

**Where to find:**
1. Go to https://discord.com/developers/applications
2. Click your bot application
3. Go to **Bot** tab
4. Click **Reset Token** → Copy

**Command:**
```bash
fly secrets set DISCORD_BOT_TOKEN="paste_your_token_here"
```

---

#### Secret 2: Gemini API Key

**Where to find:**
1. Open your `.env` file in this project
2. Copy the value after `GEMINI_API_KEY=`
3. OR get new one: https://aistudio.google.com/app/apikey

**Command:**
```bash
fly secrets set GEMINI_API_KEY="paste_your_key_here"
```

---

#### Secret 3: Forum Channel ID

**Where to find:**
1. In Discord, right-click your support forum channel
2. Click **Copy Channel ID**
3. (Make sure Developer Mode is ON in Discord settings)

**Command:**
```bash
fly secrets set SUPPORT_FORUM_CHANNEL_ID="paste_channel_id_here"
```

---

#### Secret 4: Discord Server ID

**Where to find:**
1. In Discord, right-click your server icon (left sidebar)
2. Click **Copy Server ID**

**Command:**
```bash
fly secrets set DISCORD_GUILD_ID="paste_server_id_here"
```

---

#### Secret 5: Dashboard API URL

**Where to find:**
Your Vercel dashboard URL + `/api/data`

**Example:**
- If dashboard is at: `https://rag-bot-v2.vercel.app`
- Then API URL is: `https://rag-bot-v2.vercel.app/api/data`

**Command:**
```bash
fly secrets set DATA_API_URL="https://your-vercel-app.vercel.app/api/data"
```

---

### **4. Verify All Secrets Are Set**

```bash
fly secrets list
```

**Should show:**
```
NAME                              DIGEST
DISCORD_BOT_TOKEN                 xxxxxx
GEMINI_API_KEY                    xxxxxx
SUPPORT_FORUM_CHANNEL_ID          xxxxxx
DISCORD_GUILD_ID                  xxxxxx
DATA_API_URL                      xxxxxx
```

✅ All 5 secrets set!

---

### **5. DEPLOY YOUR BOT!** 🚀

```bash
fly deploy
```

**Wait for:**
```
✓ Building image
✓ Pushing image
✓ Deploying
✓ Monitoring deployment

==> Deployment successful!
```

Takes about 2-3 minutes.

---

### **6. Check Bot is Online**

#### In Discord:
Look at your bot - should be **🟢 Online**!

#### Check Logs:
```bash
fly logs
```

Should see:
```
Logged in as YourBotName
✓ Successfully connected to dashboard API!
Bot is ready and listening for new forum posts.
```

#### Test It:
Create a forum post in Discord - bot should respond!

---

## ✅ SUCCESS! Bot is 24/7 Online!

Your bot is now:
- ✅ Running on Fly.io cloud servers
- ✅ Online 24/7 (never sleeps!)
- ✅ Auto-restarts if it crashes
- ✅ FREE (Fly.io free tier)

---

## 📱 Daily Management

### View Logs (Most Useful):
```bash
fly logs
```
Press `Ctrl+C` to stop viewing (bot keeps running).

### Restart Bot:
```bash
fly apps restart rag-bot-v2
```

### Check Status:
```bash
fly status
```

### Update Code:
```bash
# Make your changes
git add .
git commit -m "your changes"
git push
fly deploy
```

---

## 🔄 BONUS: Auto-Deploy from GitHub

Want bot to update automatically when you push to GitHub?

### One-Time Setup:

**1. Get Token:**
```bash
fly auth token
```
Copy the output.

**2. Add to GitHub:**
- Go to: https://github.com/PorterHenyon/RAG-Bot-v2/settings/secrets/actions
- Click **New repository secret**
- Name: `FLY_API_TOKEN`
- Value: Paste token
- Click **Add secret**

**Done!** Now `git push` auto-deploys your bot! 🎉

---

## 🆘 Problems?

### Bot shows offline:
```bash
fly logs
```
Check for errors.

### Forgot a secret:
```bash
fly secrets set SECRET_NAME="new_value"
```

### Need to redeploy:
```bash
fly deploy
```

### Want to start over:
```bash
fly apps destroy rag-bot-v2
fly launch --no-deploy
# Then set secrets again and deploy
```

---

## 🎯 QUICK START CHECKLIST

- [ ] `fly auth login` - Login to Fly.io
- [ ] `fly launch --no-deploy` - Create app
- [ ] Set 5 secrets with `fly secrets set`
- [ ] `fly secrets list` - Verify all secrets
- [ ] `fly deploy` - Deploy bot
- [ ] Check Discord - bot should be online
- [ ] `fly logs` - Verify it's working

---

## ⚡ TL;DR - Copy/Paste This

```bash
# Step 1: Login
fly auth login

# Step 2: Create app
fly launch --no-deploy

# Step 3: Set secrets (replace values!)
fly secrets set DISCORD_BOT_TOKEN="YOUR_TOKEN"
fly secrets set GEMINI_API_KEY="YOUR_KEY"
fly secrets set SUPPORT_FORUM_CHANNEL_ID="YOUR_CHANNEL_ID"
fly secrets set DISCORD_GUILD_ID="YOUR_SERVER_ID"
fly secrets set DATA_API_URL="https://your-vercel-app.vercel.app/api/data"

# Step 4: Verify
fly secrets list

# Step 5: Deploy!
fly deploy

# Step 6: Check logs
fly logs
```

**Your bot will be online in 10 minutes!** 🎉

---

## 💰 Cost: $0/month

Fly.io free tier:
- ✅ 3 VMs (you use 1)
- ✅ 256MB RAM
- ✅ Plenty for Discord bot
- ✅ No credit card required
- ✅ Never goes to sleep

---

## 🎊 After It's Live

Your bot will:
- Stay online 24/7 automatically
- Respond to forum posts instantly
- Run background tasks (check old posts every hour)
- Sync with your Vercel dashboard
- Send high priority notifications
- Never sleep or go offline

**Just run the commands above and you're done!** ✨

