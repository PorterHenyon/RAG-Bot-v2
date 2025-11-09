# 📝 Get Your Values for Fly.io Deployment

Before deploying, you need 5 values. Here's where to find each one:

---

## ✅ Checklist

### 1. **DISCORD_BOT_TOKEN** ⚠️ Required

**Where to get it:**
1. Go to https://discord.com/developers/applications
2. Click your bot application
3. Go to **Bot** tab (left sidebar)
4. Click **Reset Token** → **Copy**

**Example:** `MTIz...long_token_string_here...aBcDe`

**Looks like your current value:**
- Check your local `.env` file
- Or get a new token from the link above

---

### 2. **GEMINI_API_KEY** ⚠️ Required

**Where to get it:**
1. Check your `.env` file in this project
2. OR get new one: https://aistudio.google.com/app/apikey

**Example:** `AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz`

**Starts with:** `AIza`

---

### 3. **SUPPORT_FORUM_CHANNEL_ID** ⚠️ Required

**Where to get it:**
1. Open Discord
2. Right-click your support forum channel
3. Click **Copy Channel ID**

*(Make sure Developer Mode is ON: Settings → Advanced → Developer Mode)*

**Example:** `1435455947551150171`

**Your current value (from bot_settings.json):**
```
1435455947551150171
```
✅ Use this one!

---

### 4. **DISCORD_GUILD_ID** ⚠️ Required

**Where to get it:**

**Method 1 - From Discord:**
1. Right-click your **server icon** (left sidebar)
2. Click **Copy Server ID**

**Method 2 - From Your Code:**
Your bot code has a default:
```
1265864190883532872
```
✅ This is probably your server! Verify by:
- Open Discord
- Press `Ctrl+K`
- Paste `1265864190883532872`
- If it opens your server, that's the right ID!

**Example:** `1265864190883532872`

---

### 5. **DATA_API_URL** ⚠️ Required

**What it is:**
Your Vercel dashboard URL + `/api/data`

**Where to find:**
- Check your `.env` file
- Or check your Vercel dashboard URL

**Format:**
```
https://your-app-name.vercel.app/api/data
```

**Examples:**
- `https://rag-bot-v2.vercel.app/api/data`
- `https://my-dashboard.vercel.app/api/data`

**To find your Vercel URL:**
1. Go to https://vercel.com/dashboard
2. Click your project
3. Look at the "Domains" section
4. Copy the `.vercel.app` domain
5. Add `/api/data` to the end

---

## 📋 Summary - Your Values

Fill this out as you find them:

```bash
# 1. Discord Bot Token
DISCORD_BOT_TOKEN="____________________________________"

# 2. Gemini API Key  
GEMINI_API_KEY="____________________________________"

# 3. Forum Channel ID
SUPPORT_FORUM_CHANNEL_ID="1435455947551150171"  # ✅ Already have this!

# 4. Discord Guild ID (Server ID)
DISCORD_GUILD_ID="1265864190883532872"  # ✅ Probably this one!

# 5. Dashboard API URL
DATA_API_URL="https://____________.vercel.app/api/data"
```

---

## 🚀 Once You Have All Values

Run these commands (replace with your actual values):

```bash
fly secrets set DISCORD_BOT_TOKEN="paste_token_here"
fly secrets set GEMINI_API_KEY="paste_key_here"
fly secrets set SUPPORT_FORUM_CHANNEL_ID="1435455947551150171"
fly secrets set DISCORD_GUILD_ID="1265864190883532872"
fly secrets set DATA_API_URL="https://your-app.vercel.app/api/data"
```

Then:
```bash
fly deploy
```

---

## 🆘 Can't Find a Value?

### Discord Bot Token:
- Must get from: https://discord.com/developers/applications
- Select your bot → Bot tab → Reset Token

### Gemini API Key:
- Check your `.env` file first
- Or get new: https://aistudio.google.com/app/apikey

### Forum Channel ID:
- Right-click forum channel in Discord → Copy Channel ID
- (Already have: `1435455947551150171`)

### Guild ID:
- Right-click server icon in Discord → Copy Server ID
- (Probably: `1265864190883532872`)

### Vercel URL:
- Go to https://vercel.com/dashboard
- Click your project → Copy domain

---

## ✅ Values You Already Have

From your configuration files, I can see:

✅ **Forum Channel ID:** `1435455947551150171`  
✅ **Guild ID (likely):** `1265864190883532872`  
✅ **High Priority Channel:** `1436918674069000212`

You just need to find:
- ⏳ Discord Bot Token
- ⏳ Gemini API Key  
- ⏳ Vercel Dashboard URL

Check your `.env` file - they should all be there!

---

## 💡 Pro Tip

If you have your `.env` file with all values, you can quickly copy them:

1. Open `.env` file
2. Copy each value after the `=`
3. Paste into the `fly secrets set` commands
4. Done!

