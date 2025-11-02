# How to Get Your Gemini API Key

## Quick Steps

1. **Go to Google AI Studio:**
   - Visit: https://aistudio.google.com/app/apikey
   - Or: https://makersuite.google.com/app/apikey

2. **Sign in with your Google account**

3. **Create a new API key:**
   - Click "Create API Key"
   - Select "Create API key in new project" (or choose existing project)
   - Your API key will be displayed

4. **Copy the API key:**
   - It will look like: `AIzaSy...` (starts with "AIza")
   - Click "Copy" to copy it

5. **Add it to your `.env` file:**
   ```env
   GEMINI_API_KEY=your_copied_api_key_here
   ```

6. **Save the file and restart the bot**

## Important Notes

- ✅ The API key is free for reasonable usage
- ✅ Keep your API key secret - don't share it publicly
- ✅ If you lose it, you can regenerate a new one
- ✅ There are usage limits on the free tier, but they're generous for testing

## Verify It Works

After adding your API key, run:
```bash
python bot.py
```

If you see "Bot is ready and listening for new forum posts" without errors, you're all set!

## Troubleshooting

**Error: "GEMINI_API_KEY not found"**
- Make sure the `.env` file is in the same directory as `bot.py`
- Check that there are no spaces around the `=` sign
- Verify the key starts with "AIza"

**Error: "API quota exceeded"**
- You may have hit the rate limit
- Wait a few minutes and try again
- Check your usage at https://aistudio.google.com/

