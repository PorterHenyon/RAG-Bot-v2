# Using Your Existing Discord Bot for Dashboard Authentication

## TL;DR

**Yes! Use your existing bot application.** Just add the OAuth redirect URI and you're done.

---

## Why Use the Same Bot Application?

Your Discord bot and dashboard are part of the same system. Using the same Discord application makes perfect sense:

✅ **Simpler** - One application instead of two
✅ **Unified** - Everything under one roof
✅ **Logical** - Dashboard manages the bot, so they should use the same auth
✅ **Convenient** - Use the same Client ID you already have
✅ **Professional** - Standard practice for bot dashboards

Examples of other bots that do this:
- MEE6 Dashboard uses the MEE6 bot application
- Dyno Dashboard uses the Dyno bot application
- ProBot Dashboard uses the ProBot bot application

---

## Setup Steps (2 minutes)

### 1. Add OAuth Redirect to Your Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. **Click on your existing bot application**
3. Navigate to **OAuth2** → **General**
4. Scroll to **Redirects**
5. Click **"Add Redirect"**
6. Enter: `http://localhost:5173/callback`
7. Click **"Save Changes"**

### 2. Get Your Client ID

Your Client ID is the same as your bot's Application ID. You can find it:
- OAuth2 → General page
- Or on the General Information page
- It's a long number like: `123456789012345678`

### 3. Create `.env` File

In your project root, create a `.env` file:

```env
# Your bot's Client ID (same as Application ID)
VITE_DISCORD_CLIENT_ID=123456789012345678

# Callback URL
VITE_DISCORD_REDIRECT_URI=http://localhost:5173/callback
```

### 4. Start the Dashboard

```bash
npm run dev
```

Visit http://localhost:5173 and sign in with Discord!

---

## How It Works

When users log in to your dashboard:

1. They click "Sign in with Discord"
2. Discord shows: **"YourBot wants to access your account"**
3. Users authorize
4. Dashboard authenticates using the same bot application
5. Users can now manage the bot through the dashboard

**Note**: The bot doesn't need to be online for OAuth to work. OAuth and the bot are separate features of the same application.

---

## For Production Deployment

When deploying to Vercel or another platform:

### 1. Add Production Redirect URI

In Discord Developer Portal:
1. Go to your bot application
2. OAuth2 → General → Redirects
3. Add: `https://your-domain.vercel.app/callback`
4. Save Changes

### 2. Update Environment Variables on Vercel

In your Vercel project settings:
- `VITE_DISCORD_CLIENT_ID` = Your bot's Client ID
- `VITE_DISCORD_REDIRECT_URI` = `https://your-domain.vercel.app/callback`

---

## Optional: Role-Based Access Control

Since you're using your bot's application, you can restrict dashboard access to specific roles in your Discord server:

### Add Guild Scope

1. Update OAuth scopes in `contexts/AuthContext.tsx`:
```typescript
const scopes = 'identify email guilds guilds.members.read';
```

### Check Roles (Backend Required)

Create a backend endpoint that:
1. Exchanges OAuth code for access token
2. Fetches user's roles in your server
3. Only allows access if user has specific role (e.g., "Admin", "Moderator")

Example:
```javascript
const member = await getGuildMember(userId, guildId);
const requiredRoles = ['ADMIN_ROLE_ID', 'MODERATOR_ROLE_ID'];
const hasAccess = member.roles.some(role => requiredRoles.includes(role));

if (!hasAccess) {
    return res.status(403).json({ error: 'Access denied. Admin role required.' });
}
```

This way, only users with specific roles in your Discord server can access the dashboard.

---

## FAQ

### Q: Will this affect my bot?
**A:** No! Adding OAuth to your bot application doesn't change bot functionality at all. OAuth and bot are separate features.

### Q: Do I need the bot secret for OAuth?
**A:** For basic client-side OAuth (current implementation), no. For production with backend token exchange, yes - keep it secret!

### Q: Can I still create a separate application?
**A:** Yes, but there's no real benefit. Using the same application is simpler and standard practice.

### Q: What permissions does OAuth request?
**A:** By default: `identify` and `email`. This just lets the dashboard see the user's Discord username and avatar.

### Q: Is this secure?
**A:** Yes! OAuth 2.0 is industry-standard. For production, add a backend to handle token exchange securely.

### Q: Will users see my bot token?
**A:** No! Bot token and OAuth are completely separate. OAuth uses the Client ID (public) and Client Secret (keep private in backend).

---

## Summary

**You absolutely can and should use your existing bot application!**

Just:
1. Add OAuth redirect URI to your bot in Discord Developer Portal
2. Use your bot's Client ID in `.env`
3. Done!

No need to create a separate application. This is the standard approach used by all major Discord bot dashboards.

---

**Quick Start**: See [QUICK_START_OAUTH.md](./QUICK_START_OAUTH.md) for the complete setup process.

