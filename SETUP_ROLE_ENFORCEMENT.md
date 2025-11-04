# Setup Role Enforcement

## What I Just Did:

### 1. Created Backend Endpoint
- **File**: `api/auth-callback.ts`
- **Purpose**: Checks if user has Staff role before allowing access
- **Checks**: 
  - User must be in your Discord server
  - User must have Staff role (ID: `1422106035337826315`)

### 2. Updated Frontend
- OAuth now requests `guilds` and `guilds.members.read` scopes
- Calls backend endpoint to validate user
- Shows error if user doesn't have Staff role

### 3. Made Sidebar Collapsible on Mobile
- Hamburger menu button appears on mobile
- Sidebar slides in/out
- Better mobile experience!

---

## ⚠️ CRITICAL: Add Environment Variables

You need to add these to Vercel:

### Go to Vercel → Settings → Environment Variables → Add:

**1. Discord Client Secret** (IMPORTANT!)
- **Name**: `DISCORD_CLIENT_SECRET`
- **Value**: Get this from Discord Developer Portal:
  1. https://discord.com/developers/applications
  2. Click your bot
  3. Go to **OAuth2** → **General**
  4. Click "Reset Secret" to see it (or use existing)
  5. Copy the secret

**2. Discord Server ID**
- **Name**: `DISCORD_SERVER_ID`
- **Value**: Your Discord server ID
  1. Enable Developer Mode in Discord
  2. Right-click your server icon
  3. Copy Server ID

### After Adding Variables:

1. **Save** the variables
2. **Redeploy** the site (Deployments → three dots → Redeploy)

---

## 🧪 How to Test:

### Test 1: User WITH Staff Role
1. Clear session (incognito window)
2. Login with Discord account that has Staff role
3. Should successfully access dashboard ✅

### Test 2: User WITHOUT Staff Role
1. Clear session (incognito window)
2. Login with Discord account without Staff role
3. Should see error: "You must have the Staff role to access this dashboard" ❌

### Test 3: Non-Server Member
1. Login with Discord account not in your server
2. Should see error: "You must be a member of the Discord server" ❌

---

## 📱 Mobile Sidebar:

On mobile devices:
- Sidebar is hidden by default
- Click hamburger menu (☰) to open
- Click outside or select a tab to close
- Much better mobile experience!

---

## What Happens Now:

**Before** (No enforcement):
- Anyone could login and access dashboard

**After** (Enforced):
- User must be in your Discord server
- User must have Staff role (ID: 1422106035337826315)
- Backend verifies this before allowing access
- Cannot be bypassed!

---

## If It's Not Working:

1. **Check environment variables are set on Vercel**:
   - `DISCORD_CLIENT_SECRET`
   - `DISCORD_SERVER_ID`
   - `VITE_DISCORD_CLIENT_ID`
   - `VITE_DISCORD_REDIRECT_URI`

2. **Redeploy after adding variables**

3. **Clear your session**:
   - Use incognito window
   - Or paste in console: `sessionStorage.clear(); location.reload();`

4. **Check Discord Developer Portal**:
   - Redirect URI is added: `https://rag-bot-v2-lcze.vercel.app/callback`
   - Client secret is correct

---

## 🎉 Summary:

✅ **Role enforcement** - Only Staff role can access
✅ **Backend validation** - Cannot be bypassed
✅ **Mobile sidebar** - Collapsible hamburger menu
✅ **Better UX** - Error messages explain why access denied

**Now add the environment variables and redeploy!**

