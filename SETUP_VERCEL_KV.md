# Setup Vercel KV for Persistent Storage 🔧

## ⚠️ **Critical: Data Persistence Fix**

Your APIs were using in-memory storage which gets wiped on every restart. I've updated the code to use **Vercel KV** (Redis) for persistent storage.

## 🚀 **Setup Steps:**

### Step 1: Create Vercel KV Database

1. Go to your Vercel Dashboard: https://vercel.com/dashboard
2. Select your project: **rag-bot-v2-lcze**
3. Go to **Storage** tab
4. Click **Create Database**
5. Select **KV** (Key-Value / Redis)
6. Choose a name (e.g., `rag-bot-storage`)
7. Choose region (closest to you)
8. Click **Create**

### Step 2: Get Connection Details

After creating the KV database:

1. Click on your KV database
2. Go to **.env.local** tab
3. Copy these two values:
   - `KV_REST_API_URL`
   - `KV_REST_API_TOKEN`

### Step 3: Add Environment Variables to Vercel

1. In Vercel Dashboard → Your Project → **Settings**
2. Go to **Environment Variables**
3. Add these two variables:
   - **Key:** `KV_REST_API_URL` → **Value:** (paste from Step 2)
   - **Key:** `KV_REST_API_TOKEN` → **Value:** (paste from Step 2)
4. Select environment: **Production**, **Preview**, and **Development** (select all)
5. Click **Save**

### Step 4: Redeploy

1. Go to **Deployments** tab
2. Click the **3 dots** on latest deployment
3. Click **Redeploy**
4. OR push to GitHub (auto-deploys)

## ✅ **What This Fixes:**

- ✅ **RAG entries persist** - No more losing your entries
- ✅ **Auto-responses persist** - Settings saved permanently
- ✅ **Forum posts persist** - Discord posts stay on dashboard
- ✅ **Data survives restarts** - Everything persists across deployments

## 🧪 **Test After Setup:**

1. **Add a RAG entry** on dashboard
2. **Refresh page** - Entry should still be there
3. **Create forum post** in Discord
4. **Check dashboard** - Post should appear and stay

## 📊 **Without KV (Current):**

- Data resets on every serverless function restart
- Each deployment loses all data
- Data doesn't persist

## 📊 **With KV (After Setup):**

- Data persists permanently
- Survives deployments and restarts
- All your entries and posts saved

## 🔍 **Verification:**

After redeploying, check Vercel logs. You should see:
```
✓ Using Vercel KV for persistent storage
✓ Using Vercel KV for forum posts (persistent storage)
```

If you see:
```
⚠ Vercel KV not available, using in-memory storage
```

Then the environment variables aren't set correctly - check Step 3.

## 💰 **Cost:**

- **Free tier:** 256 MB storage, 10,000 reads/day
- More than enough for your bot!
- No credit card required

## 🐛 **If Setup Fails:**

1. Check Vercel logs for errors
2. Verify environment variables are set
3. Make sure `@vercel/kv` package is installed (I've added it to package.json)
4. Redeploy after adding environment variables

---

**Once KV is set up, your data will persist forever!** 🎉

