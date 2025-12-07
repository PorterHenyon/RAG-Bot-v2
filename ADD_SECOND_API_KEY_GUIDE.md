# Adding Second Gemini API Key to Railway

Your bot already supports automatic key rotation! Just add the second key to Railway and it will be automatically picked up.

## 🔑 Your Second API Key

**Key Name:** `GEMINI_API_KEY_2`  
**Value:** `AIzaSyAZwOtFg1DhqfgQ872Qaz1fS_pgkT49Glo`

---

## 📝 Steps to Add to Railway

### Option 1: Railway Dashboard (Easiest)

1. **Go to Railway Dashboard**
   - Visit [railway.app](https://railway.app)
   - Open your bot's project

2. **Navigate to Variables**
   - Click on your bot service
   - Click the **"Variables"** tab

3. **Add New Variable**
   - Click **"+ New Variable"** or **"Raw Editor"**
   - Add:
     ```
     GEMINI_API_KEY_2=AIzaSyAZwOtFg1DhqfgQ872Qaz1fS_pgkT49Glo
     ```

4. **Deploy**
   - Click **"Deploy"** or the changes auto-deploy
   - Wait for the bot to restart (~30 seconds)

5. **Verify**
   - Check the bot logs for: `✓ Loaded 2 Gemini API key(s) for rotation`

---

### Option 2: Railway CLI

```bash
# Login to Railway
railway login

# Link to your project
railway link

# Add the environment variable
railway variables set GEMINI_API_KEY_2=AIzaSyAZwOtFg1DhqfgQ872Qaz1fS_pgkT49Glo

# Redeploy
railway up
```

---

## ✅ How to Verify It's Working

### Check Bot Logs

After the bot restarts, you should see in the logs:

```
✓ Loaded 2 Gemini API key(s) for rotation
```

### In Discord

Run any AI command (like `/ask`) and check the bot logs for:

```
📊 Using key AIzaSyAZw... (1/2) | Calls on this key: 5/100 | Total usage: ...
📊 Using key AIzaSyAZw... (2/2) | Calls on this key: 3/100 | Total usage: ...
```

The number in parentheses `(1/2)` or `(2/2)` shows which key is being used.

---

## 🔄 How Key Rotation Works

### Automatic Load Balancing

The bot automatically:
1. **Distributes load** across all available keys
2. **Rotates every 100 calls** per key (default)
3. **Detects rate limits** and switches to next key
4. **Marks bad keys** and skips them if one fails

### Smart Features

- ✅ **Round-robin rotation**: Evenly distributes API calls
- ✅ **Rate limit detection**: Automatically switches when hitting limits
- ✅ **Failure recovery**: Skips broken keys and tries others
- ✅ **Usage tracking**: Monitors calls per key for debugging

---

## 📊 Benefits of Using 2 Keys

### Doubled Rate Limits

| Metric | 1 Key | 2 Keys |
|--------|-------|--------|
| **Requests/Minute** | 15 RPM | **30 RPM** |
| **Tokens/Minute** | 1M TPM | **2M TPM** |
| **Requests/Day** | 1,500 RPD | **3,000 RPD** |

### Better Reliability

- If one key hits rate limit, automatically uses the other
- If one key fails, bot continues working with the other
- Reduced chance of hitting quota limits during busy periods

---

## 🔧 Advanced: Adding More Keys

You can add up to **6 keys total**:

```env
GEMINI_API_KEY=your_first_key
GEMINI_API_KEY_2=your_second_key
GEMINI_API_KEY_3=your_third_key
GEMINI_API_KEY_4=your_fourth_key
GEMINI_API_KEY_5=your_fifth_key
GEMINI_API_KEY_6=your_sixth_key
```

### Rate Limits with Multiple Keys

| Keys | RPM | TPM | RPD |
|------|-----|-----|-----|
| 1 key | 15 | 1M | 1,500 |
| 2 keys | 30 | 2M | 3,000 |
| 3 keys | 45 | 3M | 4,500 |
| 6 keys | 90 | 6M | 9,000 |

---

## ⚙️ Configuration (Optional)

You can adjust rotation behavior in `bot.py` if needed:

```python
class GeminiKeyManager:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.calls_per_key = 100  # Rotate after 100 calls (default)
        # ... rest of code
```

**Default settings work great for most use cases!**

---

## 🚨 Troubleshooting

### "Still showing 1 key"

- **Wait for redeploy**: Railway takes 30-60 seconds to restart
- **Check spelling**: Variable name must be exactly `GEMINI_API_KEY_2`
- **Check value**: Make sure there are no spaces or quotes around the key

### "Key not working"

- **Verify key is active**: Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Check restrictions**: Make sure API key restrictions allow your server IP
- **Test manually**: Use `/check_api_keys` command (Admin only)

### "Still getting rate limit errors"

- **Keys share project quota**: All keys from same Google project share daily limits
- **Create keys from different projects**: For true independence
- **Monitor usage**: Check Google AI Studio dashboard

---

## 📖 Related Commands

| Command | Description |
|---------|-------------|
| `/status` | Shows current bot configuration |
| `/check_api_keys` | Detailed API key usage stats (Admin) |

---

## 🎯 Summary

**What to do:**
1. Add `GEMINI_API_KEY_2=AIzaSyAZwOtFg1DhqfgQ872Qaz1fS_pgkT49Glo` to Railway environment variables
2. Wait for bot to restart
3. Check logs for "Loaded 2 Gemini API key(s)"
4. Done! ✅

**No code changes needed** - the bot already has built-in support for multiple keys!

---

**Your API keys are now working together to provide better performance and reliability!** 🚀

