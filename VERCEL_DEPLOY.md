# Deploying to Vercel - Step by Step Guide

## Step 1: Import Your Repository to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Select your GitHub repository: `RAG-Bot-v2`
5. Click **"Import"**

## Step 2: Configure Project Settings

Vercel should auto-detect the settings, but verify:

- **Framework Preset**: `Vite`
- **Root Directory**: `./` (leave as default)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

## Step 3: Configure Environment Variables

In the Vercel project settings, add these environment variables:

### For the Dashboard (Frontend):

- `VITE_API_URL` - Leave empty (will auto-detect your Vercel URL)

OR set to your production URL (you'll get this after first deployment):
- `VITE_API_URL` = `https://your-project-name.vercel.app`

### For the API Route (Backend):

No environment variables needed for the API route initially (it uses in-memory storage).

**Note**: After deployment, you'll update the bot's `.env` file with the actual Vercel URL.

## Step 4: Deploy!

1. Click **"Deploy"**
2. Wait for the build to complete (usually 1-2 minutes)
3. Your app will be live at: `https://your-project-name.vercel.app`

## Step 5: Update Your Bot Configuration

After deployment, you'll get a URL like: `https://rag-bot-v2.vercel.app`

### Update your bot's `.env` file:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
SUPPORT_FORUM_CHANNEL_ID=your_channel_id
DATA_API_URL=https://your-actual-vercel-url.vercel.app/api/data
```

**Important**: Replace `your-actual-vercel-url` with your actual Vercel deployment URL!

## Step 6: Test the API

Test that your API is working:

```bash
# Test the GET endpoint
curl https://your-vercel-url.vercel.app/api/data

# Should return JSON with ragEntries and autoResponses
```

## Step 7: Run Your Bot

```bash
python bot.py
```

The bot should:
- ✅ Connect to Discord
- ✅ Fetch data from your Vercel API
- ✅ Sync every 5 minutes
- ✅ Respond to forum posts

## Troubleshooting

### Build Fails?

**Error: Cannot find module**
```bash
# Make sure all dependencies are in package.json
npm install
npm run build
```

**Error: TypeScript errors**
```bash
# Check for type errors
npm run lint
```

### API Not Working?

**404 on /api/data**
- Check that `api/data.ts` exists in your repository
- Verify Vercel detected the API route (should show in build logs)
- Check the Functions tab in Vercel dashboard

**CORS errors**
- The API already has CORS headers configured
- Make sure your frontend URL matches the API URL domain

### Dashboard Not Loading?

**Blank page**
- Check browser console for errors
- Verify build completed successfully
- Check that `index.html` exists in `dist/` folder

**API calls failing**
- Check network tab in browser DevTools
- Verify `VITE_API_URL` is correct (or leave empty for auto-detection)
- Make sure the API route is deployed

## Next Steps: Production Improvements

For production, consider:

1. **Add a Database**:
   - Replace in-memory storage with Supabase, MongoDB, or Vercel Postgres
   - Update `api/data.ts` to use database instead of `dataStore` variable

2. **Add Authentication**:
   - Protect your dashboard with authentication
   - Add API key authentication for the bot

3. **Add Rate Limiting**:
   - Prevent API abuse
   - Limit requests per IP

4. **Add Error Monitoring**:
   - Integrate Sentry or similar
   - Track API errors

## Quick Reference

**Your Dashboard URL**: `https://your-project-name.vercel.app`
**Your API Endpoint**: `https://your-project-name.vercel.app/api/data`
**Bot Sync Interval**: Every 5 minutes (or use `/reload` command)

## Need Help?

If you encounter issues:
1. Check Vercel deployment logs
2. Check Vercel function logs for API errors
3. Test API directly with curl/Postman
4. Check bot console output for sync errors

