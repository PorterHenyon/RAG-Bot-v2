# Fix Vercel API 404 Error

Your bot is getting a 404 error when trying to connect to Vercel. This means the URL in `.env` might be incorrect.

## Quick Fix:

### Step 1: Find Your Actual Vercel URL

1. Go to your Vercel dashboard: https://vercel.com/porterhenyons-projects/rag-bot-v2
2. Look at the **"Domains"** section OR
3. Look at the deployment details - it will show the actual URL

**Common Vercel URL formats:**
- `https://rag-bot-v2.vercel.app`
- `https://rag-bot-v2-xxxxx.vercel.app`
- Custom domain if you set one up

### Step 2: Test the API Endpoint

Once you have the URL, test it:
- Go to: `https://your-actual-url.vercel.app/api/data`
- You should see JSON with `ragEntries` and `autoResponses`
- If you get 404, the deployment might not be working

### Step 3: Update .env File

Replace the URL in your `.env` file:

```env
DATA_API_URL=https://your-actual-url.vercel.app/api/data
```

**Important:** Make sure you include `/api/data` at the end!

### Step 4: Restart Bot

After updating `.env`:
1. Stop the bot (Ctrl+C)
2. Restart: `python bot.py`
3. You should see: "✓ Synced X RAG entries and Y auto-responses from dashboard"

## Common Issues:

### Issue 1: Vercel Deployment Not Complete
- **Check:** Go to Vercel dashboard → Check deployment status
- **Fix:** Make sure deployment shows "Ready" (not "Error" or "Building")

### Issue 2: API Route Not Deployed
- **Check:** Visit `https://your-url.vercel.app/api/data` directly in browser
- **Fix:** If 404, the API file might not be deployed. Check that `api/data.ts` exists

### Issue 3: Wrong URL Format
- **Check:** Make sure URL includes `/api/data` at the end
- **Wrong:** `https://rag-bot-v2.vercel.app`
- **Right:** `https://rag-bot-v2.vercel.app/api/data`

## Alternative: Test Without Vercel

If Vercel isn't deployed yet, the bot will work fine with local data:
- Bot uses local fallback data automatically
- All Discord features work normally
- Forum posts won't sync to dashboard (but bot still responds)

You can deploy to Vercel later when ready!

## Need Help?

1. **Share your Vercel dashboard URL** - I can help verify the correct endpoint
2. **Check Vercel deployment logs** - See if there are any build errors
3. **Test API endpoint manually** - Open the URL in browser to see response

