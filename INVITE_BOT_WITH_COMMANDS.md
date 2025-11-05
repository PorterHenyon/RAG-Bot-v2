# Invite Bot to Server with Slash Commands

## 🔗 Generate Invite Link

### Step 1: Go to Discord Developer Portal
1. Visit: https://discord.com/developers/applications
2. Click on your bot application
3. Go to **OAuth2** → **URL Generator**

### Step 2: Select Scopes
Check these boxes:
- ✅ **bot**
- ✅ **applications.commands** ← **CRITICAL for slash commands!**

### Step 3: Select Bot Permissions
Check these permissions:
- ✅ Read Messages/View Channels
- ✅ Send Messages
- ✅ Send Messages in Threads
- ✅ Create Public Threads
- ✅ Embed Links
- ✅ Attach Files
- ✅ Read Message History
- ✅ Add Reactions
- ✅ Manage Threads
- ✅ Manage Messages (for locking threads)

### Step 4: Copy the Generated URL
At the bottom of the page, you'll see a URL like:
```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=XXXXX&scope=bot%20applications.commands
```

### Step 5: Invite to Your Server
1. Copy that URL
2. Paste it in your browser
3. Select your server: **1265864190883532872**
4. Click **Authorize**

---

## ✅ After Inviting

Once the bot is in the server, **restart the bot**:
```bash
python bot.py
```

You should see:
```
✓ Slash commands synced to guild 1265864190883532872 (11 commands).
   Commands will appear instantly in the server!
```

Then type `/` in Discord and you'll see all 11 commands!

---

## 🔧 If Commands Still Don't Show

### Option A: Re-invite the bot
If you invited the bot before without the `applications.commands` scope, you need to re-invite it using the new URL with that scope.

### Option B: Manual command sync
In Discord (as server admin), you can:
1. Right-click the bot in member list
2. Look for "Sync Application Commands" or similar
3. Wait a few seconds
4. Try typing `/` again

---

## 📝 Quick Check:

**Bot is in server?** ✅ / ❌  
**Bot has `applications.commands` scope?** ✅ / ❌  
**Bot is running (`python bot.py`)?** ✅ / ❌  
**You see the sync message in console?** ✅ / ❌  

If all ✅, commands should appear when you type `/` in Discord!

