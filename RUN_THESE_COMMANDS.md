# ⚡ RUN THESE COMMANDS IN YOUR TERMINAL

Copy and paste these commands **one at a time** in your PowerShell or terminal.

---

## Step 1: Login to Fly.io
```bash
fly auth login
```
✅ Opens browser, sign up/login (free account)

---

## Step 2: Create the App
```bash
fly launch --copy-config --no-deploy
```

**When prompted:**
- Use existing configuration? → Type `y` and press Enter
- Choose region? → Just press Enter (uses default)

---

## Step 3: Set Your Secrets

**⚠️ REPLACE WITH YOUR ACTUAL VALUES!**

Find your values from your `.env` file, then run:

```bash
fly secrets set DISCORD_BOT_TOKEN="your_actual_token_here"
```

```bash
fly secrets set GEMINI_API_KEY="your_actual_key_here"
```

```bash
fly secrets set SUPPORT_FORUM_CHANNEL_ID="1435455947551150171"
```

```bash
fly secrets set DISCORD_GUILD_ID="1265864190883532872"
```

```bash
fly secrets set DATA_API_URL="https://your-vercel-app.vercel.app/api/data"
```

---

## Step 4: Verify Secrets
```bash
fly secrets list
```

Should show all 5 secrets.

---

## Step 5: DEPLOY!
```bash
fly deploy
```

Wait 2-3 minutes. Should see: `✓ Deployment successful!`

---

## Step 6: Check Bot is Online

### In Discord:
Bot should be 🟢 Online

### Check Logs:
```bash
fly logs
```

---

## ✅ Done! Bot is 24/7 Online!

---

## 🔄 BONUS: Auto-Deploy Setup

To make bot update automatically when you `git push`:

### 1. Get Token:
```bash
fly auth token
```
Copy the output.

### 2. Add to GitHub:
- Go to: https://github.com/PorterHenyon/RAG-Bot-v2/settings/secrets/actions
- Click **New repository secret**
- Name: `FLY_API_TOKEN`
- Value: Paste token
- Click **Add secret**

✅ Now `git push` auto-deploys!

---

## 🆘 Still Have Errors?

Run these and send me the output:
```bash
fly version
ls Dockerfile
fly auth whoami
```

