# 🚀 Deploy Your Bot 24/7 - Step by Step Together

## ✅ Let's Do This Right!

I'll guide you through each step. Follow along!

---

## 📍 STEP 1: Make Sure You're in the Right Directory

### Run this:
```bash
pwd
```

### Should show:
```
C:\Users\porte\.cursor\RAG-Bot-v2
```

### If not, run:
```bash
cd C:\Users\porte\.cursor\RAG-Bot-v2
```

---

## ✅ STEP 2: Check What We Have

### Run this:
```bash
ls Dockerfile, fly.toml, bot.py, requirements.txt
```

### Should show all 4 files exist.

---

## 🔑 STEP 3: Get Your Values Ready

### You need 5 values. Let's find them:

#### A. Check if you have a .env file:
```bash
cat .env
```

This should show you:
- DISCORD_BOT_TOKEN=...
- GEMINI_API_KEY=...
- SUPPORT_FORUM_CHANNEL_ID=...
- DISCORD_GUILD_ID=...
- DATA_API_URL=...

**Copy these values somewhere safe** - we'll need them in a minute!

---

## 🌐 STEP 4: Login to Fly.io

### Run this:
```bash
fly auth login
```

**What happens:**
- Opens your browser
- You sign up for Fly.io (FREE account)
- No credit card needed!

**After login**, come back to terminal.

---

## 🎯 STEP 5: Check Existing Apps

### Run this:
```bash
fly apps list
```

**Tell me what you see!**

---

## 📝 What Happens Next

After Step 5, based on what we see:
- If app exists → We'll use it or delete and recreate
- If no app → We'll create a fresh one

**Stop here and show me the output of Step 5!** Then we'll continue together! 🚀


