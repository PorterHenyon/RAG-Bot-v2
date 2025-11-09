# 🚀 START YOUR BOT 24/7 RIGHT NOW

## ✅ Good News!

You already have:
- ✅ Fly.io CLI installed (v0.3.209)
- ✅ Dockerfile configured
- ✅ fly.toml configured
- ✅ GitHub Actions workflow ready
- ✅ All code pushed to GitHub

**You're 80% there!** Just need to deploy.

---

## 🎯 Choose Your Method

### **Method 1: Quick Deploy (5 minutes)** ⭐ RECOMMENDED
Follow these commands in order.

### **Method 2: Auto-Deploy (10 minutes)**
Set up GitHub Actions for automatic deployments.

---

# 🚀 METHOD 1: Quick Deploy

## Step 1: Login to Fly.io

```bash
fly auth login
```

- Opens browser
- Sign up or log in
- Free account (no credit card needed!)

---

## Step 2: Check if App Exists

```bash
fly apps list
```

**If you see "rag-bot-v2" listed:**
- Skip to Step 4 (secrets)

**If NOT listed:**
- Continue to Step 3

---

## Step 3: Create the App (If Needed)

```bash
fly launch --no-deploy
```

**Answers:**
- App name? → Press Enter
- Region? → Press Enter (or pick closest)
- PostgreSQL? → Type `n` and press Enter
- Redis? → Type `n` and press Enter
- Deploy? → Type `n` and press Enter

✅ App created!

---

## Step 4: Set Your Secrets

**IMPORTANT:** Replace the values with YOUR actual values!

### Get Your Values:

Open your `.env` file in this project and copy each value.

### Set Each Secret:

```bash
fly secrets set DISCORD_BOT_TOKEN="paste_your_token_here"
```

```bash
fly secrets set GEMINI_API_KEY="paste_your_key_here"
```

```bash
fly secrets set SUPPORT_FORUM_CHANNEL_ID="paste_channel_id_here"
```

```bash
fly secrets set DISCORD_GUILD_ID="paste_server_id_here"
```

```bash
fly secrets set DATA_API_URL="paste_your_vercel_url_here"
```

**Example DATA_API_URL:**
```
https://rag-bot-v2.vercel.app/api/data
```

### Verify Secrets Were Set:
```bash
fly secrets list
```

Should show all 5 secrets (names only, not values).

---

## Step 5: DEPLOY! 🚀

```bash
fly deploy
```

**What happens:**
1. ⏳ Builds Docker image (2 min)
2. ⏳ Uploads to Fly.io (1 min)
3. ⏳ Starts your bot (30 sec)

**Wait for:**
```
✓ Deployment successful!
```

---

## Step 6: Verify It's Working

### Check Discord:
Your bot should be **🟢 Online**!

### Check Logs:
```bash
fly logs
```

Look for:
```
Logged in as RevolutionMacroBot
✓ Successfully connected to dashboard API!
Bot is ready and listening for new forum posts.
```

### Test the Bot:
1. Create a forum post in Discord
2. Bot should respond automatically
3. Check your dashboard - post should appear

---

## ✅ SUCCESS! Your Bot is 24/7 Online!

Your bot is now:
- ✅ Running on Fly.io servers
- ✅ Online 24/7 (no sleep)
- ✅ Auto-restarts if it crashes
- ✅ Monitored by Fly.io
- ✅ Free forever (free tier)

---

# 🤖 METHOD 2: Auto-Deploy from GitHub

Want your bot to auto-update when you push code?

## Step 1: Get Fly.io API Token

```bash
fly auth token
```

Copy the token that appears.

---

## Step 2: Add Token to GitHub

1. Go to: https://github.com/PorterHenyon/RAG-Bot-v2/settings/secrets/actions
2. Click **New repository secret**
3. Name: `FLY_API_TOKEN`
4. Value: Paste the token from Step 1
5. Click **Add secret**

---

## Step 3: Push to Main Branch

```bash
git push
```

**That's it!** Every time you push code:
- GitHub Actions triggers
- Bot auto-deploys to Fly.io
- Takes 2-3 minutes
- Bot restarts with new code

---

## 📊 After Setup - Useful Commands

### View Logs Anytime:
```bash
fly logs
```

### Check Bot Status:
```bash
fly status
```

### Restart Bot:
```bash
fly apps restart rag-bot-v2
```

### Update a Secret:
```bash
fly secrets set GEMINI_API_KEY="new_key"
```

### Open Fly.io Dashboard:
```bash
fly open
```
Or visit: https://fly.io/apps/rag-bot-v2

---

## 🎯 Quick Reference Card

```bash
# Initial Setup (Do Once)
fly auth login                          # Login
fly launch --no-deploy                  # Create app
fly secrets set KEY="value"             # Add secrets (×5)
fly deploy                              # Deploy!

# Daily Use
fly logs                                # View logs
fly status                              # Check status
fly apps restart rag-bot-v2             # Restart

# Updates
git push                                # Auto-deploy (if configured)
# OR
fly deploy                              # Manual deploy
```

---

## 🆘 Need Help?

### Check Logs First:
```bash
fly logs
```

### Common Issues:

**Bot offline?**
```bash
fly apps restart rag-bot-v2
```

**Secrets wrong?**
```bash
fly secrets list                        # View names
fly secrets set KEY="new_value"         # Update
```

**Need to redeploy?**
```bash
fly deploy
```

---

## 🎉 You're Done!

Follow Method 1 (Steps 1-6) to get online in 5 minutes!

**Current Status:**
- ✅ Code ready
- ✅ Fly.io CLI installed
- ✅ Configuration files ready
- ⏳ Just need to run the deploy commands!

**Start with:**
```bash
fly auth login
```

Then follow the steps above! 🚀

---

## 💡 Pro Tip

After deployment, bookmark these commands:
```bash
fly logs          # Most useful - see what bot is doing
fly status        # Quick health check
fly deploy        # Update bot with new code
```

**Your bot will be online 24/7 in less than 10 minutes!** ⚡

