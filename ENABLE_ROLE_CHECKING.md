# How to Re-Enable Role Checking

Role checking is currently **DISABLED** to allow easy access.

## 🔒 To Re-Enable Staff Role Restriction:

### Step 1: Edit `contexts/AuthContext.tsx`

1. Open `contexts/AuthContext.tsx`
2. Find the `handleDiscordCallback` function (around line 62)
3. **Delete** the mock user code (lines that create the mockUser)
4. **Uncomment** the code block that says "TO RE-ENABLE ROLE CHECKING"

### Step 2: Add Environment Variables on Vercel

1. Go to https://vercel.com/dashboard
2. Select RAG-Bot-v2
3. **Settings** → **Environment Variables**
4. Add:
   - **Name**: `DISCORD_CLIENT_SECRET`
   - **Value**: From Discord Developer Portal (OAuth2 → General → Client Secret)
   
   - **Name**: `DISCORD_SERVER_ID`
   - **Value**: Your Discord server ID

### Step 3: Commit and Push

```bash
git add contexts/AuthContext.tsx
git commit -m "Re-enable role checking - Staff role required"
git push origin main
```

### Step 4: Redeploy on Vercel

Go to Deployments → Three dots → Redeploy

---

## ✅ After Re-Enabling:

- ✅ Only users with Staff role (1422106035337826315) can access
- ✅ Discord user 614865086804394012 can access (if they have Staff role)
- 🔒 Fully secure - backend validates roles

---

## 🎯 Current State:

⚠️ **ROLE CHECKING IS OFF** - Anyone with Discord OAuth can access
🔓 **Not secure** - Good for testing, bad for production

**Re-enable when you're ready to restrict access!**





