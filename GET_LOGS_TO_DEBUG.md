# 🔍 Get Logs to Debug Crash

## The bot is crashing on Fly.io. Let's see why!

---

## 🚀 Run These Commands

### **Method 1: Get Recent Logs** (Fastest)

```bash
fly logs --app rag-bot-v2-silent-grass-1075
```

Press `Ctrl+C` to stop when you see the error.

---

### **Method 2: Get Specific Instance Logs**

```bash
fly logs -i 2863795a71d978
```

---

### **Method 3: Get Last 100 Lines**

```bash
fly logs --app rag-bot-v2-silent-grass-1075 -n 100
```

---

## 📋 What to Look For

The logs will show one of these common errors:

### **Missing Environment Variable:**
```
FATAL ERROR: 'DISCORD_BOT_TOKEN' not found in environment.
```
**Fix:** Run the `fly secrets set` commands

### **Invalid API Key:**
```
FATAL ERROR: 'GEMINI_API_KEY' not found
```
**Fix:** Set your Gemini API key

### **Module Not Found:**
```
ModuleNotFoundError: No module named 'discord'
```
**Fix:** Check requirements.txt

### **Connection Error:**
```
discord.errors.LoginFailure: Improper token has been passed
```
**Fix:** Your Discord token is wrong

---

## 🔧 Common Fixes

### Fix 1: Secrets Not Set

```bash
fly secrets set DISCORD_BOT_TOKEN="your_actual_token"
fly secrets set GEMINI_API_KEY="your_actual_key"
fly secrets set SUPPORT_FORUM_CHANNEL_ID="1435455947551150171"
fly secrets set DISCORD_GUILD_ID="1265864190883532872"
fly secrets set DATA_API_URL="https://your-vercel-url.vercel.app/api/data"
```

After setting secrets:
```bash
fly deploy
```

---

### Fix 2: Wrong App Name

Your app got named: `rag-bot-v2-silent-grass-1075`

All commands need to use this name:
```bash
fly logs --app rag-bot-v2-silent-grass-1075
fly secrets list --app rag-bot-v2-silent-grass-1075
fly deploy --app rag-bot-v2-silent-grass-1075
```

---

### Fix 3: Check Secrets Are Set

```bash
fly secrets list --app rag-bot-v2-silent-grass-1075
```

Should show 5 secrets. If missing any:
```bash
fly secrets set KEY="value" --app rag-bot-v2-silent-grass-1075
```

---

## 📊 Full Debug Process

### Step 1: Get logs
```bash
fly logs --app rag-bot-v2-silent-grass-1075 -n 200
```

### Step 2: Copy the error message here

### Step 3: I'll tell you exactly how to fix it!

---

## 🎯 Most Likely Issues

### 1. Secrets Not Set (90% chance)
**Check:**
```bash
fly secrets list --app rag-bot-v2-silent-grass-1075
```

**Fix:**
Set all 5 secrets, then:
```bash
fly deploy --app rag-bot-v2-silent-grass-1075
```

### 2. Invalid Token (8% chance)
**Check logs for:** `LoginFailure` or `Invalid token`

**Fix:**
Get fresh token from Discord developers portal:
```bash
fly secrets set DISCORD_BOT_TOKEN="new_token" --app rag-bot-v2-silent-grass-1075
```

### 3. Missing Dependency (2% chance)
**Check logs for:** `ModuleNotFoundError`

**Fix:**
Already in requirements.txt, should work automatically.

---

## ⚡ Quick Commands Reference

```bash
# View logs
fly logs --app rag-bot-v2-silent-grass-1075

# Check secrets
fly secrets list --app rag-bot-v2-silent-grass-1075

# Set a secret
fly secrets set KEY="value" --app rag-bot-v2-silent-grass-1075

# Redeploy
fly deploy --app rag-bot-v2-silent-grass-1075

# Check status
fly status --app rag-bot-v2-silent-grass-1075
```

---

## 🎯 What to Do Right Now

### 1. Get the error:
```bash
fly logs --app rag-bot-v2-silent-grass-1075 -n 200
```

### 2. Send me the last 20-30 lines (especially any red ERROR lines)

### 3. I'll tell you exactly what's wrong and how to fix it!

---

## 💡 Pro Tip

The crash usually happens within the first 5 seconds of startup, so the error will be in the most recent logs.

Look for lines that say:
- ❌ `FATAL ERROR:`
- ❌ `Error:`
- ❌ `Exception:`
- ❌ `Failed:`

**Run the logs command and send me the output!** 🔍


