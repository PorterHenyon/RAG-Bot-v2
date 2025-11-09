# 🚀 Deploy Your Bot 24/7 - Complete Step-by-Step Guide

## 🎯 Goal
Get your Discord bot running **24/7 online** using Fly.io (FREE tier)

---

## ✅ Prerequisites

You'll need:
- ✅ Discord Bot Token
- ✅ Gemini API Key
- ✅ Forum Channel ID
- ✅ Discord Server (Guild) ID
- ✅ Vercel Dashboard URL (your DATA_API_URL)

---

## 📋 Step-by-Step Instructions

### **Step 1: Install Fly.io CLI** (First Time Only)

Open **PowerShell as Administrator** and run:
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

**After installation:**
1. Close and reopen your terminal/PowerShell
2. Verify it installed:
   ```bash
   fly version
   ```

---

### **Step 2: Create Fly.io Account & Login**

```bash
fly auth login
```

This will:
- Open your browser
- Ask you to sign up or log in to Fly.io
- Connect your terminal to your account

**Free Tier Includes:**
- 3 VMs (you only need 1)
- 256MB RAM per VM
- Perfect for Discord bots!

---

### **Step 3: Create Your Bot App on Fly.io**

```bash
fly launch --no-deploy
```

**When prompted, answer:**
- **App name?** → Press Enter (uses "rag-bot-v2" from fly.toml)
- **Choose region?** → Pick closest to you or press Enter for default
- **PostgreSQL database?** → **No** (type `n`)
- **Redis database?** → **No** (type `n`)
- **Deploy now?** → **No** (type `n`)

This creates the app but doesn't deploy yet (we need to add secrets first).

---

### **Step 4: Set Your Environment Variables (Secrets)**

Copy your actual values and run these commands one by one:

```bash
fly secrets set DISCORD_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
```

```bash
fly secrets set GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```

```bash
fly secrets set SUPPORT_FORUM_CHANNEL_ID="YOUR_FORUM_CHANNEL_ID"
```

```bash
fly secrets set DISCORD_GUILD_ID="YOUR_SERVER_ID"
```

```bash
fly secrets set DATA_API_URL="https://your-vercel-app.vercel.app/api/data"
```

**Where to find these values:**

1. **DISCORD_BOT_TOKEN**: 
   - Go to https://discord.com/developers/applications
   - Select your bot → Bot → Token → Copy

2. **GEMINI_API_KEY**:
   - Check your `.env` file (starts with `AIza...`)
   - Or get from https://aistudio.google.com/app/apikey

3. **SUPPORT_FORUM_CHANNEL_ID**:
   - Check your `.env` file
   - Or right-click your forum channel → Copy Channel ID

4. **DISCORD_GUILD_ID**:
   - Check your `.env` file
   - Or right-click your server icon → Copy Server ID

5. **DATA_API_URL**:
   - Your Vercel dashboard URL + `/api/data`
   - Example: `https://rag-bot-v2.vercel.app/api/data`

---

### **Step 5: Deploy Your Bot!** 🚀

```bash
fly deploy
```

**This will:**
1. Build your Docker container
2. Upload it to Fly.io
3. Start your bot
4. Keep it running 24/7!

**Wait 2-3 minutes** for deployment to complete.

---

### **Step 6: Verify Bot is Online**

#### Check Discord:
- Your bot should show as **🟢 Online** in Discord

#### Check Logs:
```bash
fly logs
```

You should see:
```
Logged in as YourBot (ID: ...)
✓ Loaded bot settings
✓ Successfully connected to dashboard API!
Bot is ready and listening for new forum posts.
```

#### Check Status:
```bash
fly status
```

Should show:
```
Status: running
```

---

## ✅ Success! Your Bot is Now 24/7 Online!

---

## 🔧 Common Management Commands

### View Live Logs
```bash
fly logs
```
Press `Ctrl+C` to stop viewing (bot keeps running).

### Restart Bot
```bash
fly apps restart rag-bot-v2
```

### Check Status
```bash
fly status
```

### Update a Secret
```bash
fly secrets set DISCORD_BOT_TOKEN="new_token_here"
```
Bot automatically restarts with new value.

### List All Secrets
```bash
fly secrets list
```
Shows names only (not values for security).

### Stop Bot (Temporarily)
```bash
fly scale count 0
```

### Start Bot Again
```bash
fly scale count 1
```

---

## 🔄 Automatic Updates (Optional but Recommended)

Want your bot to auto-deploy when you push to GitHub?

### One-Time Setup:

1. **Get Fly.io API Token:**
   ```bash
   fly auth token
   ```
   Copy the token that appears.

2. **Add to GitHub Secrets:**
   - Go to: https://github.com/PorterHenyon/RAG-Bot-v2/settings/secrets/actions
   - Click **New repository secret**
   - Name: `FLY_API_TOKEN`
   - Value: Paste your token
   - Click **Add secret**

3. **Create GitHub Actions Workflow:**
   I'll create this file for you!

Now every time you `git push`, your bot auto-deploys! 🎉

---

## 💰 Cost

**FREE TIER:**
- ✅ Your bot runs 24/7 for FREE
- ✅ No credit card required
- ✅ 256MB RAM (plenty for Discord bot)
- ✅ 3 VMs free (you only need 1)

---

## 🐛 Troubleshooting

### Problem: Bot shows offline in Discord

**Solution 1: Check logs**
```bash
fly logs
```
Look for error messages.

**Solution 2: Verify secrets are set**
```bash
fly secrets list
```
Should show all 5 secrets.

**Solution 3: Restart**
```bash
fly apps restart rag-bot-v2
```

### Problem: "Error: Could not find App"

**Solution:**
```bash
fly launch --no-deploy
```
Re-create the app.

### Problem: Bot works locally but not on Fly.io

**Solution:**
Check that all secrets are set correctly:
```bash
fly secrets list
```
Should show:
- DISCORD_BOT_TOKEN
- GEMINI_API_KEY
- SUPPORT_FORUM_CHANNEL_ID
- DISCORD_GUILD_ID
- DATA_API_URL

### Problem: Deployment fails

**Solution 1: Check Dockerfile**
Make sure `Dockerfile` exists and is correct.

**Solution 2: Check requirements.txt**
All dependencies should be listed.

**Solution 3: View build logs**
```bash
fly logs
```

---

## 📊 Monitoring Your Bot

### Dashboard
- Go to: https://fly.io/dashboard
- See all your apps
- View metrics, logs, and status

### Real-Time Logs
```bash
fly logs --app rag-bot-v2
```

### Bot Status in Discord
- Bot profile should show 🟢 Online
- Use `/status` command in Discord to check bot internals

---

## 🎯 Quick Command Reference

```bash
# Initial setup
fly auth login                    # Login to Fly.io
fly launch --no-deploy           # Create app (one-time)
fly secrets set KEY="value"      # Add secrets
fly deploy                       # Deploy bot

# Management
fly logs                         # View logs
fly status                       # Check status
fly apps restart rag-bot-v2      # Restart bot
fly scale count 1                # Ensure 1 instance running

# Secrets
fly secrets set KEY="value"      # Update secret
fly secrets list                 # List all secrets
fly secrets unset KEY            # Remove secret
```

---

## 🎉 After Deployment

Once deployed, your bot will:
- ✅ Stay online 24/7
- ✅ Auto-restart if it crashes
- ✅ Sync with your Vercel dashboard
- ✅ Monitor forum posts continuously
- ✅ Send high priority notifications
- ✅ Run all background tasks (hourly checks, daily cleanup)

---

## 🚨 Important Notes

1. **Don't delete `fly.toml`** - Fly.io needs this!
2. **Don't delete `Dockerfile`** - This builds your bot!
3. **Keep secrets secret** - Never commit them to git!
4. **Monitor logs occasionally** - Check for errors
5. **Free tier is plenty** - Your bot uses minimal resources

---

## 📱 Alternative: Use My Quick Deploy Script

Want to do it all at once? I can create a script that:
1. Checks if Fly.io is installed
2. Prompts for your secrets
3. Deploys everything automatically

Let me know if you want this! For now, follow the manual steps above.

---

## ✅ You're Ready!

Follow steps 1-6 above and your bot will be online 24/7!

**Estimated time: 10-15 minutes** (mostly waiting for deployment)

**Need help?** Check the troubleshooting section or ask me!

