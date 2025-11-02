# Update Vercel Environment Variables

Your bot needs the Discord bot token in Vercel to close Discord threads from the dashboard.

## Steps:

1. Go to your Vercel dashboard: https://vercel.com/porterhenyons-projects/rag-bot-v2

2. Navigate to: **Settings → Environment Variables**

3. Add this environment variable:
   - **Key:** `DISCORD_BOT_TOKEN`
   - **Value:** `your_discord_bot_token_here`
   - **Environment:** Production, Preview, Development (select all)

4. Save and redeploy if needed

This allows the dashboard to close Discord threads when you change post status to "Closed".

## Also add Gemini API key for dashboard:

- **Key:** `API_KEY`
- **Value:** `your_gemini_api_key_here`
- **Environment:** Production, Preview, Development (select all)

This enables the "Summarize for RAG" button to work in the dashboard.

