# How to Restrict Dashboard Access

This guide shows you how to control who can access your RAG Bot Dashboard.

---

## 🎯 Quick Start: Restrict by User ID (Easiest)

### Step 1: Get Your Discord User ID

1. Open Discord
2. Go to **Settings** → **Advanced**
3. Enable **Developer Mode**
4. Right-click your username anywhere in Discord
5. Click **Copy User ID**
6. You'll get a long number like: `123456789012345678`

### Step 2: Add Allowed Users

Open `config/accessControl.ts` and add user IDs:

```typescript
export const ALLOWED_USER_IDS: string[] = [
    '123456789012345678',  // Your user ID
    '987654321098765432',  // Another admin
    '555666777888999000',  // Another moderator
];
```

### Step 3: Test It!

1. Save the file
2. Restart dev server: `npm run dev`
3. Try logging in
4. Only users in the list can access the dashboard!

---

## 📋 Access Control Methods

### Method 1: Whitelist User IDs ✅ **EASIEST - START HERE**

**Best for**: Small teams, specific admins

**How it works**: Only specific Discord user IDs can log in

**Setup**:
1. Edit `config/accessControl.ts`
2. Add Discord user IDs to `ALLOWED_USER_IDS`
3. Done!

**Example**:
```typescript
export const ALLOWED_USER_IDS: string[] = [
    '123456789012345678',  // You
    '987654321098765432',  // Co-admin
];
```

---

### Method 2: Require Server Membership ⚠️ **REQUIRES BACKEND**

**Best for**: Anyone in your Discord server

**How it works**: User must be a member of your Discord server

**Setup** (requires backend implementation):
1. Add backend endpoint (see Backend Setup section below)
2. Backend checks if user is in your server
3. Only allows access if they're a member

**Current Status**: 
- ⚠️ Not implemented yet (client-side only)
- 🔧 Requires backend API (instructions below)

---

### Method 3: Role-Based Access ⚠️ **REQUIRES BACKEND**

**Best for**: Specific roles like "Admin", "Moderator"

**How it works**: User must have specific role(s) in your Discord server

**Setup** (requires backend implementation):
1. Get role IDs from Discord (right-click role → Copy Role ID)
2. Add to `ALLOWED_ROLE_IDS` in `config/accessControl.ts`
3. Implement backend role checking (see Backend Setup)

**Example**:
```typescript
export const ALLOWED_ROLE_IDS: string[] = [
    '111222333444555666',  // Admin role
    '777888999000111222',  // Moderator role
];
```

**Current Status**: 
- ⚠️ Not implemented yet (client-side only)
- 🔧 Requires backend API (instructions below)

---

## 🚀 Current Implementation (Client-Side Only)

Right now, the dashboard uses **client-side access control** for simplicity:

### ✅ What Works Now:
- Whitelist by Discord User IDs
- Simple, easy to set up
- Good for development and small teams

### ⚠️ Limitations:
- Can be bypassed by tech-savvy users
- No role checking (requires backend)
- No server membership checking (requires backend)

### 🔧 For Production:
You should add a backend to securely check roles/membership (see Backend Setup section)

---

## 📝 Configuration File: `config/accessControl.ts`

### Key Settings:

```typescript
// Enable/disable access control
export const ACCESS_CONTROL = {
    ENABLED: true,  // Set to false to allow anyone
    
    // If true, allows anyone when ALLOWED_USER_IDS is empty
    // Set to false in production!
    ALLOW_ALL_IF_EMPTY: true,
};

// Whitelist specific user IDs
export const ALLOWED_USER_IDS: string[] = [
    // Add Discord user IDs here
];

// Your Discord server ID
export const DISCORD_SERVER_ID = 'your_server_id_here';

// Require users to be in your server (needs backend)
export const REQUIRE_SERVER_MEMBERSHIP = true;

// Role IDs for role-based access (needs backend)
export const ALLOWED_ROLE_IDS: string[] = [
    // Add role IDs here
];
```

---

## 🛠️ Backend Setup (For Production)

To implement secure role-based or server membership checking, you need a backend.

### Why Backend is Needed:
- Client secret must stay secret (can't expose it in frontend)
- Role/membership checking requires Discord API calls with access token
- Prevents users from bypassing client-side checks

### Backend Implementation:

#### 1. Create Backend OAuth Endpoint

```javascript
// backend/routes/auth.js
const express = require('express');
const fetch = require('node-fetch');

const router = express.Router();

router.get('/discord/callback', async (req, res) => {
    const { code } = req.query;
    
    try {
        // Exchange code for access token
        const tokenResponse = await fetch('https://discord.com/api/oauth2/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                client_id: process.env.DISCORD_CLIENT_ID,
                client_secret: process.env.DISCORD_CLIENT_SECRET,
                grant_type: 'authorization_code',
                code: code,
                redirect_uri: process.env.DISCORD_REDIRECT_URI,
            }),
        });
        
        const tokens = await tokenResponse.json();
        
        // Get user info
        const userResponse = await fetch('https://discord.com/api/users/@me', {
            headers: {
                Authorization: `Bearer ${tokens.access_token}`,
            },
        });
        
        const user = await userResponse.json();
        
        // Check if user is in your server
        const guildResponse = await fetch(
            `https://discord.com/api/users/@me/guilds/${process.env.DISCORD_SERVER_ID}/member`,
            {
                headers: {
                    Authorization: `Bearer ${tokens.access_token}`,
                },
            }
        );
        
        if (!guildResponse.ok) {
            return res.status(403).json({ 
                error: 'You must be a member of our Discord server' 
            });
        }
        
        const member = await guildResponse.json();
        
        // Check if user has required role
        const requiredRoles = process.env.REQUIRED_ROLE_IDS.split(',');
        const hasRole = member.roles.some(roleId => requiredRoles.includes(roleId));
        
        if (!hasRole) {
            return res.status(403).json({ 
                error: 'You do not have the required role' 
            });
        }
        
        // Create session
        req.session.user = user;
        req.session.member = member;
        
        res.redirect('/');
        
    } catch (error) {
        console.error('OAuth error:', error);
        res.status(500).json({ error: 'Authentication failed' });
    }
});

module.exports = router;
```

#### 2. Update Frontend to Use Backend

In `contexts/AuthContext.tsx`, replace the mock callback with:

```typescript
const handleDiscordCallback = async (code: string): Promise<boolean> => {
    try {
        // Send code to backend
        const response = await fetch('/api/auth/discord/callback?code=' + code);
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error || 'Authentication failed');
            return false;
        }
        
        const userData = await response.json();
        
        setIsAuthenticated(true);
        setUser(userData);
        sessionStorage.setItem('isAuthenticated', 'true');
        sessionStorage.setItem('discordUser', JSON.stringify(userData));
        
        return true;
    } catch (error) {
        console.error('Discord OAuth callback failed:', error);
        return false;
    }
};
```

#### 3. Add Required OAuth Scopes

In `contexts/AuthContext.tsx`, update scopes:

```typescript
// Change from:
const scopes = 'identify email';

// To:
const scopes = 'identify email guilds guilds.members.read';
```

This allows the backend to:
- See user's servers
- Check server membership
- See user's roles

---

## 📋 Quick Reference: How to Get IDs

### Get Discord User ID:
1. Discord Settings → Advanced → Enable Developer Mode
2. Right-click username → Copy User ID

### Get Discord Server ID:
1. Enable Developer Mode (above)
2. Right-click server icon → Copy Server ID

### Get Discord Role ID:
1. Server Settings → Roles
2. Right-click a role → Copy Role ID

---

## 🧪 Testing Access Control

### Test 1: Allowed User
1. Add your Discord user ID to `ALLOWED_USER_IDS`
2. Try logging in
3. Should work! ✅

### Test 2: Blocked User
1. Remove your user ID from `ALLOWED_USER_IDS`
2. Try logging in
3. Should show "Access Denied" message ❌

### Test 3: Empty Whitelist
1. Set `ALLOWED_USER_IDS` to `[]` (empty)
2. Set `ALLOW_ALL_IF_EMPTY: true`
3. Anyone can log in (for testing only!)

---

## 🔒 Security Best Practices

### For Development:
✅ Use user ID whitelist
✅ Set `ALLOW_ALL_IF_EMPTY: true` for easy testing

### For Production:
✅ Implement backend role checking
✅ Set `ALLOW_ALL_IF_EMPTY: false`
✅ Use environment variables for sensitive data
✅ Enable HTTPS
✅ Use session tokens, not just sessionStorage
✅ Add rate limiting

---

## 💡 Recommended Setup by Team Size

### Solo/1-2 Admins:
→ **User ID Whitelist** (simplest)

### Small Team (3-10 people):
→ **User ID Whitelist** or **Role-Based** (with backend)

### Medium Team (10-50 people):
→ **Role-Based Access** (with backend)

### Large Community:
→ **Role-Based Access** + **Server Membership** (with backend)

---

## 🚨 Common Issues

### "Access Denied" even though I'm in the list
- Check user ID is correct (long number, no quotes issues)
- Restart dev server after changing config
- Check `ACCESS_CONTROL.ENABLED` is `true`
- Clear browser cache

### Can't get role checking to work
- Role checking requires backend implementation
- Current client-side version only supports user ID whitelist
- See Backend Setup section above

### Anyone can still access
- Check `ACCESS_CONTROL.ENABLED` is `true`
- Check `ALLOWED_USER_IDS` is not empty
- If empty, set `ALLOW_ALL_IF_EMPTY: false`

---

## 📚 Summary

### Current Implementation:
- ✅ User ID whitelist (works now)
- ⚠️ Role-based access (needs backend)
- ⚠️ Server membership (needs backend)

### To Restrict Access Now:
1. Edit `config/accessControl.ts`
2. Add Discord user IDs to `ALLOWED_USER_IDS`
3. Restart dev server
4. Done!

### For Production:
1. Implement backend OAuth handler
2. Add role/membership checking
3. Update frontend to use backend
4. Deploy securely

---

## 🎯 Next Steps

1. **Now**: Add your user ID to `ALLOWED_USER_IDS`
2. **Soon**: Add other admin user IDs
3. **Later**: Implement backend for role checking (if needed)
4. **Production**: Secure backend with proper session management

---

**Ready to restrict access?** Just edit `config/accessControl.ts` and add your Discord user ID!

