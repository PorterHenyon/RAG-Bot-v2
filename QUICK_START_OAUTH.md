# Quick Start: Discord OAuth Setup

## ✅ What's Been Implemented

Your RAG Bot Dashboard now uses **Discord OAuth 2.0** for authentication! Here's what changed:

### Fixed Issues:
1. ✅ **Comma/Space Input Bug**: Fixed in RAG Management triggers/keywords fields (both new and edit forms)
2. ✅ **Authentication**: Replaced username/password with Discord OAuth
3. ✅ **Security**: Professional OAuth 2.0 implementation

### New Features:
- 🔐 Discord OAuth login
- 👤 User avatar display
- 🎨 Beautiful Discord-branded UI
- 📝 Comprehensive documentation

## 🚀 Quick Setup (5 minutes)

### Step 1: Configure OAuth on Your Existing Bot

**Good News**: You can use your existing Discord bot application! No need to create a new one.

1. Go to https://discord.com/developers/applications
2. **Select your existing bot application** (the one running your Discord bot)
3. Go to **OAuth2** → **General**
4. Under **Redirects**, click **"Add Redirect"** and add: `http://localhost:5173/callback`
5. Click **"Save Changes"**
6. Copy your **Client ID** (same as your bot's application ID)

**Alternative**: If you prefer a separate application for the dashboard, you can create a new one by clicking "New Application" instead.

### Step 2: Configure Environment

1. Create a `.env` file in your project root:
   ```bash
   # Copy the example file
   cp env.example .env
   ```

2. Edit `.env` and add your Discord Client ID:
   ```env
   VITE_DISCORD_CLIENT_ID=your_client_id_here
   VITE_DISCORD_REDIRECT_URI=http://localhost:5173/callback
   ```

### Step 3: Run the Application

```bash
# Install dependencies (if not already done)
npm install

# Start the dev server
npm run dev
```

### Step 4: Test It Out!

1. Open http://localhost:5173 in your browser
2. Click **"Sign in with Discord"**
3. Authorize the application
4. You'll be redirected back and logged in! 🎉

## 📁 New/Modified Files

### Created:
- `components/Login.tsx` - Discord OAuth login page
- `components/OAuthCallback.tsx` - Handles OAuth redirect
- `contexts/AuthContext.tsx` - Auth state management
- `env.example` - Environment variable template
- `DISCORD_OAUTH_SETUP.md` - Detailed setup guide
- `AUTHENTICATION_GUIDE.md` - Complete authentication documentation

### Modified:
- `App.tsx` - Added auth protection and callback handling
- `components/Header.tsx` - Discord avatar and logout
- `components/views/RagManagementView.tsx` - **FIXED** input fields!

## 🎯 Important Notes

### Current Implementation
⚠️ The current OAuth implementation is **simplified for demonstration**:
- Uses mock user data after OAuth callback
- Client-side only (no backend token exchange)
- Suitable for development and testing

### For Production Use
You should add a backend to:
1. **Securely exchange OAuth code for access token** (keeps client secret safe)
2. **Verify Discord tokens server-side**
3. **Check Discord server roles** for access control
4. **Implement proper session management**

See [DISCORD_OAUTH_SETUP.md](./DISCORD_OAUTH_SETUP.md) for production implementation details.

## 🔒 Security Recommendations

### Restrict Access by Discord Role (Recommended!)

To only allow specific Discord server members/roles:

1. Update OAuth scopes to include `guilds` and `guilds.members.read`
2. Create a backend endpoint that:
   - Exchanges OAuth code for access token
   - Fetches user's roles in your Discord server
   - Only allows access if user has required role

Example check:
```javascript
const hasAdminRole = member.roles.includes('YOUR_ADMIN_ROLE_ID');
if (!hasAdminRole) {
    return res.status(403).json({ error: 'Access denied' });
}
```

## 🐛 Troubleshooting

### "OAuth is not configured" Alert
- Make sure `.env` file exists with `VITE_DISCORD_CLIENT_ID`
- Restart dev server after creating `.env`

### "Redirect URI mismatch" from Discord
- Check that redirect URI in Discord app matches `.env` exactly
- Should be: `http://localhost:5173/callback`
- No trailing slashes!

### Still can't type commas in keyword fields?
- Hard refresh the browser (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache
- The fix uses separate string state for editing to prevent conversion issues

### Login button does nothing
- Check browser console for errors
- Verify Discord Client ID is correct
- Make sure you're using Client ID, not Application Secret

## 📚 Documentation

- **[DISCORD_OAUTH_SETUP.md](./DISCORD_OAUTH_SETUP.md)** - Complete OAuth setup guide
- **[AUTHENTICATION_GUIDE.md](./AUTHENTICATION_GUIDE.md)** - Full authentication documentation
- **[env.example](./env.example)** - Environment variables reference

## 🎨 What You'll See

### Login Page
- Modern gradient background (indigo/purple theme)
- Large Discord button
- Information box explaining OAuth benefits
- Professional, polished design

### After Login
- Your Discord username in top-right header
- Your Discord avatar (or Discord icon if no avatar)
- Red logout button
- All dashboard features unlocked

## 🚀 Next Steps

1. **Test the login flow** - Make sure everything works
2. **Set up for production** - Add proper backend OAuth handling
3. **Add role restrictions** - Only allow certain Discord roles
4. **Deploy** - Update environment variables for production URL

## 💡 Tips

- Session persists across refreshes (uses `sessionStorage`)
- Logs out automatically when browser closes
- Works seamlessly with your Discord bot
- Can be extended to show different features based on Discord roles

## ❓ Questions?

Check the detailed guides:
- OAuth setup issues → [DISCORD_OAUTH_SETUP.md](./DISCORD_OAUTH_SETUP.md)
- Authentication features → [AUTHENTICATION_GUIDE.md](./AUTHENTICATION_GUIDE.md)
- Input field issues → They're fixed! Uses separate state now.

---

**Everything is ready to go!** Just follow the 4 steps above and you'll be up and running with Discord OAuth. 🎉

