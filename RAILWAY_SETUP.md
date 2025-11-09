# 🚂 Railway.app Setup Guide - Super Easy!

Railway.app is **way easier** than Fly.io with a better UI and simpler setup.

---

## ✅ What You Get

- 🆓 **$5 free credit/month** (enough for small bots)
- 🔄 **Auto-deploy from GitHub** (push code → auto updates)
- 📊 **Beautiful dashboard** with logs
- ⚡ **No sleep** - bot runs 24/7
- 🎯 **Simple setup** - 5 minutes total

---

## 🚀 Step-by-Step Setup

### **Step 1: Create Railway Account**

1. Go to: https://railway.app
2. Click **"Start a New Project"**
3. Sign up with **GitHub** (recommended for auto-deploy)
4. No credit card required for trial!

---

### **Step 2: Deploy from GitHub**

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repo: `PorterHenyon/RAG-Bot-v2`
4. Railway will automatically detect it's a Python project!

**Important:** If Railway asks for permissions, grant access to your repo.

---

### **Step 3: Add Environment Variables**

After deployment starts, click on your service, then go to **"Variables"** tab.

Add these 5 variables (click **"New Variable"** for each):

#### Required Variables:

**1. DISCORD_BOT_TOKEN**
```
Your Discord bot token from https://discord.com/developers/applications
```

**2. GEMINI_API_KEY**
```
Your Gemini API key from https://aistudio.google.com/app/apikey
```

**3. SUPPORT_FORUM_CHANNEL_ID**
```
1435455947551150171
```

**4. DISCORD_GUILD_ID**
```
Your Discord server ID (right-click server icon → Copy ID)
```

**5. DATA_API_URL**
```
https://your-vercel-app.vercel.app/api/data
```

*(Replace with your actual Vercel dashboard URL)*

---

### **Step 4: Deploy!**

1. After adding all variables, Railway will **automatically redeploy**
2. Wait 1-2 minutes for build to complete
3. Check the **"Deployments"** tab - it should show green ✅
4. Click **"View Logs"** to see your bot starting up!

---

## 📊 Using Railway Dashboard

### View Logs (Real-time)
1. Click your service
2. Go to **"Deployments"** tab
3. Click latest deployment
4. Logs appear automatically!

**Look for:**
```
Logged in as [Your Bot Name] (ID: ...)
✓ Monitoring channel: [channel name]
```

### Restart Bot
1. Go to your service
2. Click **"Settings"** tab
3. Scroll to **"Service"** section
4. Click **"Restart"**

### Check Resource Usage
1. Click your service
2. Go to **"Metrics"** tab
3. See CPU, Memory, and Network usage

---

## 🔄 Automatic Deployments

**Already set up!** Every time you push to GitHub:
1. Railway detects the change
2. Automatically rebuilds and deploys
3. Bot updates in 2-3 minutes
4. Zero downtime!

---

## 💰 Pricing & Free Tier

### Free Trial
- ✅ **$5 free credit** to start
- ✅ Enough for ~500 hours of bot runtime
- ✅ No credit card needed initially

### After Trial (Hobby Plan - $5/month)
- ✅ $5/month for 500 hours + $5 in credits
- ✅ Small Discord bots use ~$3-5/month
- ✅ Very affordable!

### Resource Usage
Your bot will use approximately:
- **Memory:** ~200-300 MB
- **CPU:** Very low (spikes when responding)
- **Cost:** ~$3-5/month

---

## 🔧 Troubleshooting

### Bot Not Starting?

**Check Logs:**
1. Go to Railway dashboard
2. Click your service → Deployments → Latest deployment
3. Look for error messages

**Common Issues:**

**"DISCORD_BOT_TOKEN not found"**
- Go to Variables tab
- Make sure all 5 variables are set
- Click "Redeploy" button

**"Module not found"**
- Railway should auto-detect `requirements.txt`
- If not, check that `requirements.txt` exists in repo
- Manually trigger redeploy

**Bot shows offline in Discord:**
- Check **MESSAGE CONTENT INTENT** is enabled in Discord Developer Portal
- See `BOT_FIX_INSTRUCTIONS.md` for details

### Bot Crashes on Startup?

**Check for Python errors in logs:**
- Syntax errors will show in deployment logs
- Fix the error in your code
- Push to GitHub (auto-redeploys)

### Need to Update Environment Variables?

1. Go to **Variables** tab
2. Click on variable to edit
3. Update value
4. Railway auto-redeploys with new value

---

## 📱 Railway Mobile App

Railway has a mobile app!
- 📊 Check logs on your phone
- 🔄 Restart services
- 📈 View metrics

**Download:**
- iOS: https://apps.apple.com/app/railway/id1622266989
- Android: Not yet available

---

## ⚙️ Advanced Settings

### Custom Start Command
Already configured in `railway.json`:
```
python -u bot.py
```

### Restart Policy
Set to restart automatically on failure (max 10 retries).

### Health Checks
Railway automatically monitors if your bot is running.

---

## 🆚 Railway vs Fly.io

| Feature | Railway | Fly.io |
|---------|---------|---------|
| Setup Difficulty | ⭐ Easy | ⭐⭐⭐ Complex |
| Dashboard UI | ⭐⭐⭐ Beautiful | ⭐⭐ Basic |
| Logs Viewer | ⭐⭐⭐ Excellent | ⭐⭐ Good |
| Auto-Deploy | ✅ Yes | ✅ Yes (needs setup) |
| Free Tier | $5 credit | Limited free |
| Pricing After | $5/month | Pay-as-you-go |

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Railway dashboard shows deployment as "Success" (green ✅)
- [ ] Logs show "Logged in as [Bot Name]"
- [ ] Logs show "✓ Monitoring channel: [channel name]"
- [ ] Bot shows as "Online" in Discord
- [ ] Bot responds to forum posts
- [ ] All 5 environment variables are set

---

## 🔗 Useful Links

- **Railway Dashboard:** https://railway.app/dashboard
- **Railway Docs:** https://docs.railway.app
- **Pricing:** https://railway.app/pricing
- **Support:** https://help.railway.app

---

## 🎉 You're Done!

Your bot is now:
- ✅ Running 24/7 on Railway
- ✅ Auto-deploying from GitHub
- ✅ Easy to monitor and manage
- ✅ Much better than Fly.io!

**Test it:** Create a forum post in your Discord server and watch the bot respond!

---

## 💡 Pro Tips

1. **Bookmark your Railway dashboard** for easy access
2. **Enable notifications** in Railway settings to get alerts
3. **Check logs regularly** to monitor bot health
4. **Use the mobile app** to check status on the go

---

## ❓ Need Help?

If something doesn't work:
1. Check the logs in Railway dashboard
2. Verify all environment variables are set
3. Make sure MESSAGE CONTENT INTENT is enabled in Discord
4. Check `BOT_FIX_INSTRUCTIONS.md` for bot-specific issues

**Railway is way simpler than Fly.io - you got this!** 🚀

