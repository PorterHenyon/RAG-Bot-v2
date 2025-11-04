# Fix Production Login - 3 Steps

## Your production URL is likely: `https://rag-bot-v2.vercel.app` or similar

## ✅ DO THESE 3 THINGS:

### 1. Add Production Redirect to Discord (2 minutes)

1. Go to https://discord.com/developers/applications
2. Click your bot application
3. Go to **OAuth2** → **General**
4. Under **Redirects**, click **"Add Redirect"**
5. Add: `https://YOUR-VERCEL-URL.vercel.app/callback`
   - Replace YOUR-VERCEL-URL with your actual Vercel domain
6. Click **"Save Changes"**

### 2. Set Environment Variables on Vercel (2 minutes)

1. Go to https://vercel.com/dashboard
2. Select your RAG-Bot-v2 project
3. Go to **Settings** → **Environment Variables**
4. Add these two variables:

```
VITE_DISCORD_CLIENT_ID = your_discord_client_id
VITE_DISCORD_REDIRECT_URI = https://YOUR-VERCEL-URL.vercel.app/callback
```

5. Click **"Save"**

### 3. Redeploy (1 minute)

1. In Vercel dashboard, go to **Deployments**
2. Click the **three dots** on the latest deployment
3. Click **"Redeploy"**
4. Wait for it to finish

---

## THEN Clear Your Browser Session

After redeploying, go to your production URL and paste this in browser console:

```javascript
sessionStorage.clear(); localStorage.clear(); location.reload();
```

**YOU WILL SEE THE LOGIN PAGE.**

---

## What Your Vercel URL Is:

Check your Vercel dashboard or look at the URL where your dashboard is currently deployed.

It's probably something like:
- `https://rag-bot-v2.vercel.app`
- `https://rag-bot-v2-yourname.vercel.app`
- Or a custom domain if you set one up

Use that exact URL (with `/callback` at the end) in both Discord and Vercel settings.

