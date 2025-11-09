# 🆔 How to Get Your Discord Guild ID

## Quick Method (30 seconds)

### Step 1: Enable Developer Mode
1. Open **Discord**
2. Click the ⚙️ **Settings** icon (bottom left, next to your username)
3. Go to **Advanced** (left sidebar, near the bottom)
4. Turn ON **Developer Mode**
5. Click **ESC** to close settings

### Step 2: Copy Your Server ID
1. Look at your **server list** (left side of Discord)
2. **Right-click** your server icon
3. Click **Copy Server ID** (at the bottom of the menu)
4. That's your Guild ID! ✅

**It looks like:** `1265864190883532872` (a long number)

---

## 📋 What You Have

Based on your code, I can see:
- **Default Guild ID in code:** `1265864190883532872`

This might already be your server! Let me help you verify.

---

## ✅ Quick Verification

The Guild ID from your bot code is:
```
1265864190883532872
```

**Is this your server?** You can check by:
1. Copy this ID: `1265864190883532872`
2. In Discord, press `Ctrl+K` (opens search)
3. Paste the ID and press Enter
4. If it takes you to your server, that's the right ID!

---

## 🎯 For Fly.io Deployment

Use this command with your Guild ID:

```bash
fly secrets set DISCORD_GUILD_ID="1265864190883532872"
```

Or if you found a different one:
```bash
fly secrets set DISCORD_GUILD_ID="your_copied_id_here"
```

---

## 🖼️ Visual Guide

### Where to Right-Click:
```
Discord Window
├── [Your Profile]
├── [DMs]
└── [SERVER LIST] ← Right-click your server here
    ├── 🏠 Your Server Name ← This one!
    ├── 🎮 Another Server
    └── ➕ Add Server
```

After right-clicking, you'll see a menu:
```
Server Name
────────────
Invite People
Server Settings
Create Channel
...
────────────
Copy Server ID  ← Click this!
```

---

## 🔍 Alternative Method: From URL

If your bot is already in the server:
1. Go to any channel in your server
2. Look at the URL in your browser/Discord:
   ```
   https://discord.com/channels/1265864190883532872/1234567890
                                ^^^^^^^^^^^^^^^^^^^^
                                This is your Guild ID!
   ```

---

## ✨ Quick Reference

Your Guild ID is most likely:
```
1265864190883532872
```

This is from your bot.py code (line 22):
```python
DISCORD_GUILD_ID_STR = os.getenv('DISCORD_GUILD_ID', '1265864190883532872')
```

Use this for deployment unless you have a different server!

