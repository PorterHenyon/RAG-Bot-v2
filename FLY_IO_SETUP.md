# Fly.io Deployment Setup

## 📋 What I Created for You

1. **Dockerfile** - Tells Fly.io how to build your bot
2. **fly.toml** - Fly.io configuration
3. **.dockerignore** - What files to exclude from deployment
4. **GitHub Actions Workflow** - Auto-deploys when you push to `main` branch

---

## 🚀 Initial Setup (One-Time)

### Step 1: Install Fly.io CLI

**Windows (PowerShell as Administrator):**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

After install, **restart your terminal** or VS Code.

### Step 2: Login to Fly.io
```bash
fly auth login
```

### Step 3: Create the App on Fly.io
```bash
fly launch --no-deploy
```

When prompted:
- **App name:** Press Enter (will use "rag-bot-v2" from fly.toml)
- **Region:** Choose closest to you (or press Enter for default)
- **PostgreSQL?** → No
- **Redis?** → No
- **Deploy now?** → No

### Step 4: Set Environment Variables (Secrets)

```bash
fly secrets set DISCORD_BOT_TOKEN="your_discord_bot_token_here"
fly secrets set GEMINI_API_KEY="your_gemini_api_key_here"
fly secrets set SUPPORT_FORUM_CHANNEL_ID="your_forum_channel_id_here"
fly secrets set DISCORD_GUILD_ID="your_discord_server_id_here"
fly secrets set DATA_API_URL="your_vercel_dashboard_url/api/data"
```

**Example:**
```bash
fly secrets set DISCORD_BOT_TOKEN="YOUR_ACTUAL_BOT_TOKEN_HERE"
fly secrets set GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"
fly secrets set SUPPORT_FORUM_CHANNEL_ID="1234567890123456789"
fly secrets set DATA_API_URL="https://your-dashboard.vercel.app/api/data"
```

> **Note:** Replace the placeholder values with your actual tokens from Discord and Google AI Studio.

### Step 5: Deploy!
```bash
fly deploy
```

---

## 🔄 Automatic Deployments (GitHub Actions)

### One-Time Setup:

1. **Get your Fly.io API Token:**
   ```bash
   fly auth token
   ```
   Copy the token that appears.

2. **Add to GitHub Secrets:**
   - Go to your GitHub repo: https://github.com/PorterHenyon/RAG-Bot-v2
   - Click **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `FLY_API_TOKEN`
   - Value: Paste your token from step 1
   - Click **Add secret**

3. **Done!** Now every time you push to `main` branch:
   - GitHub Actions will automatically deploy to Fly.io
   - The bot will update within 2-3 minutes

---

## 📊 Managing Your Bot

### View Logs (Real-time)
```bash
fly logs
```

### Check Status
```bash
fly status
```

### SSH into the Machine
```bash
fly ssh console
```

### Restart Bot
```bash
fly apps restart rag-bot-v2
```

### Stop Bot (saves resources)
```bash
fly scale count 0
```

### Start Bot Again
```bash
fly scale count 1
```

---

## 💰 Free Tier Info

Fly.io free tier includes:
- 3 shared-cpu VMs
- 256MB RAM per VM
- 160GB bandwidth/month
- **Perfect for Discord bots!**

Your bot will use **1 VM** running 24/7 with no sleep.

---

## 🐛 Troubleshooting

### Bot not starting?
```bash
fly logs
```
Check for errors in the output.

### Need to update secrets?
```bash
fly secrets set DISCORD_BOT_TOKEN="new_token"
```

### Want to see all secrets?
```bash
fly secrets list
```
(Shows names only, not values for security)

---

## ✅ Verification

After deployment, check:
1. Discord - Your bot should show as "Online"
2. Logs - `fly logs` should show bot starting up
3. Test - Send a message in your support forum

---

## 🔗 Useful Links

- Fly.io Dashboard: https://fly.io/dashboard
- Your app: https://fly.io/apps/rag-bot-v2
- Fly.io Docs: https://fly.io/docs

