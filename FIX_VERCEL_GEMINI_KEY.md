# Fix Vercel Dashboard Summarization Error

## Error Message
```
Failed to generate summary: Failed to generate summary. 
Please check that VITE_GEMINI_API_KEY is set in Vercel environment variables and try again.
```

## Solution

Your Vercel dashboard needs the Gemini API key to generate summaries for RAG entries.

### Steps to Fix:

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard
   - Select your project: `rag-bot-v2`

2. **Navigate to Settings**
   - Click **Settings** tab
   - Click **Environment Variables** in sidebar

3. **Add New Variable**
   - **Name**: `VITE_GEMINI_API_KEY`
   - **Value**: Your Gemini API key (same one from your `.env` file)
   - **Environments**: Check all (Production, Preview, Development)
   - Click **Save**

4. **Redeploy**
   - Go to **Deployments** tab
   - Click the three dots on the latest deployment
   - Click **Redeploy**

### Where to Find Your Gemini API Key

Open your `.env` file and look for:
```
GEMINI_API_KEY=your_key_here
```

Copy that value and paste it into Vercel.

---

## ✅ Done!

After redeployment, the "Summarize for RAG" button will work!

