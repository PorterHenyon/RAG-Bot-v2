# Bot Testing Guide - Getting Started

## Prerequisites

1. ✅ Discord Bot Token (from Discord Developer Portal)
2. ✅ Gemini API Key (from Google AI Studio)
3. ✅ Discord Channel ID for your support forum
4. ✅ Vercel Dashboard URL (after deployment)
5. ✅ Python 3.8+ installed
6. ✅ Virtual environment set up

## Step 1: Set Up Environment Variables

Create a `.env` file in the project root:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
SUPPORT_FORUM_CHANNEL_ID=your_forum_channel_id_here
DATA_API_URL=https://your-vercel-url.vercel.app/api/data
```

### Getting Your Discord Channel ID

1. In Discord, right-click your forum channel
2. Click "Copy ID" (you need Developer Mode enabled)
3. Paste it in your `.env` file

**To Enable Developer Mode:**
- Discord Settings → Advanced → Enable Developer Mode

## Step 2: Install Dependencies

```bash
# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or
.\venv\Scripts\activate.bat   # Windows CMD

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Update Vercel Environment Variables

After deploying to Vercel, add this environment variable:

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add: `DISCORD_BOT_TOKEN` = `your_discord_bot_token`
3. This allows the API to close Discord threads

## Step 4: Run the Bot

```bash
python bot.py
```

### Expected Output:

```
Logged in as YourBotName (ID: 123456789)
✓ Synced 2 RAG entries and 1 auto-responses from dashboard.
✓ Slash commands synced (2 commands).
Bot is ready and listening for new forum posts.
-------------------
```

## Step 5: Test the Integration

### Test 1: Create a Forum Post in Discord

1. Go to your Discord server
2. Navigate to your support forum channel
3. Click "New Post" or create a new thread
4. Post a question (e.g., "How do I reset my password?")

**Expected Results:**
- ✅ Bot responds immediately in Discord
- ✅ Bot sends greeting message
- ✅ Bot analyzes the question and responds
- ✅ Post appears in dashboard within 10 seconds
- ✅ Console shows: `✓ Forum post sent to dashboard API`

### Test 2: Check Dashboard

1. Open your Vercel dashboard URL
2. Navigate to "Forum Posts" view
3. You should see the new post appear automatically

**What to Check:**
- ✅ Post title matches Discord thread name
- ✅ User information is correct
- ✅ Initial message is shown
- ✅ Bot response is in conversation history
- ✅ Status is set correctly (Unsolved, AI Response, or Human Support)

### Test 3: Test Status Dropdown

1. Click on a forum post in the dashboard
2. Change status dropdown to "Closed"
3. **Expected Results:**
   - ✅ Dropdown shows "Updating to Closed..."
   - ✅ Thread is archived in Discord (check Discord)
   - ✅ Post status updates in dashboard
   - ✅ System message added to conversation

### Test 4: Test Summarize Function

1. Change a post status to "Solved"
2. Click "Summarize for RAG" button
3. **Expected Results:**
   - ✅ Button shows "Summarizing..."
   - ✅ Summary is generated using Gemini AI
   - ✅ Summary appears in conversation history
   - ✅ Success message shown

**If it fails:**
- Check that `API_KEY` environment variable is set in Vercel
- Check browser console for errors
- Verify Gemini API key is valid

### Test 5: Test Delete Function

1. Select a Closed or Solved post
2. Click "Delete Post"
3. Confirm deletion
4. **Expected Results:**
   - ✅ Post is removed from dashboard
   - ✅ Post is removed from API

## Troubleshooting

### Bot Won't Start

**Error: "FATAL ERROR: 'DISCORD_BOT_TOKEN' not found"**
- ✅ Check `.env` file exists in project root
- ✅ Check token is correct (no extra spaces)
- ✅ Verify `.env` file is not in `.gitignore` (it should be)

**Error: "Failed to sync commands"**
- ✅ Check bot has proper permissions
- ✅ Verify bot is invited to server
- ✅ Check bot has "applications.commands" scope

### Forum Posts Don't Appear in Dashboard

**Check Bot Console:**
- Look for: `✓ Forum post sent to dashboard API`
- If you see: `⚠ Failed to send forum post to API`
  - ✅ Check `DATA_API_URL` in `.env` is correct
  - ✅ Verify Vercel deployment is live
  - ✅ Test API endpoint: `curl https://your-url.vercel.app/api/forum-posts`

**Check Dashboard:**
- Open browser console (F12)
- Look for errors in Network tab
- Check if API calls are being made

### Status Dropdown Doesn't Close Discord Threads

**Check Vercel Environment Variables:**
- ✅ `DISCORD_BOT_TOKEN` must be set in Vercel
- ✅ Token must match the bot token

**Check Browser Console:**
- Look for: "Error closing thread in Discord"
- Common issues:
  - Bot token not set in Vercel
  - Thread ID incorrect
  - Bot doesn't have permissions to archive threads

### Summarize Button Doesn't Work

**Check Browser Console:**
- Look for Gemini API errors
- Verify `API_KEY` is set in Vercel
- Check network requests to see if API calls are being made

**Common Issues:**
- Gemini API key not configured
- API quota exceeded
- Invalid API key format

## Monitoring the Bot

### Check Bot Logs

The bot prints useful information:

```
New forum post created: 'Question Title' by Username
✓ Forum post sent to dashboard API: Question Title
Responded to 'Question Title' with a RAG-based AI answer.
✓ Updated forum post with bot response in dashboard API
```

### Monitor Dashboard

- Forum posts refresh automatically every 10 seconds
- New posts appear within 10 seconds of creation
- Status changes are synced immediately

## Quick Test Checklist

- [ ] Bot starts without errors
- [ ] Bot syncs RAG data from dashboard on startup
- [ ] Creating a forum post in Discord shows up in dashboard
- [ ] Bot responses appear in dashboard conversation
- [ ] Status dropdown updates and closes Discord threads
- [ ] Summarize button generates summaries
- [ ] Delete button removes posts
- [ ] Dashboard auto-refreshes forum posts

## Next Steps After Testing

1. **Monitor Production:**
   - Watch bot console for errors
   - Monitor Vercel function logs
   - Check Discord for bot responses

2. **Improve RAG Database:**
   - Add more knowledge base entries
   - Add more auto-responses
   - Fine-tune keywords

3. **Production Setup:**
   - Consider using a database (Supabase, MongoDB)
   - Add authentication to dashboard
   - Set up monitoring/alerting

## Support

If you encounter issues:
1. Check bot console output
2. Check Vercel deployment logs
3. Check browser console (F12)
4. Verify all environment variables are set correctly

