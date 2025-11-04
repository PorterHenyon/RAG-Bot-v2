# Discord OAuth Setup Guide

This guide will walk you through setting up Discord OAuth authentication for your RAG Bot Dashboard.

## Prerequisites
- A Discord account
- Your existing Discord bot application (or create a new one at https://discord.com/developers/applications)

## Step 1: Use Your Existing Bot Application (Recommended)

**You can use the same Discord application that's running your bot!** This is simpler and more cohesive.

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. **Select your existing bot application** from the list
3. *(Skip to Step 2 below)*

**OR** if you want a separate application for the dashboard:

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Give it a name (e.g., "RAG Bot Dashboard")
4. Click **"Create"**

## Step 2: Configure OAuth2 Settings

1. In your application, go to the **"OAuth2"** section in the left sidebar
2. Click on **"General"** under OAuth2
3. Under **"Redirects"**, add your redirect URIs:
   - For local development: `http://localhost:5173/callback`
   - For production: `https://your-domain.com/callback`
4. Click **"Save Changes"**

## Step 3: Get Your Client ID

1. Still in the OAuth2 section, copy your **"Client ID"**
2. You'll need this for your environment variables

## Step 4: Set Up Environment Variables

1. Create a `.env` file in your project root (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Add your Discord credentials to `.env`:
   ```env
   VITE_DISCORD_CLIENT_ID=your_client_id_here
   VITE_DISCORD_REDIRECT_URI=http://localhost:5173/callback
   ```

3. For production deployment on Vercel:
   - Go to your Vercel project settings
   - Navigate to **"Environment Variables"**
   - Add:
     - `VITE_DISCORD_CLIENT_ID` = your Client ID
     - `VITE_DISCORD_REDIRECT_URI` = `https://your-domain.vercel.app/callback`

## Step 5: Configure OAuth Scopes

The dashboard requests these Discord scopes:
- `identify` - Get basic user info (username, avatar)
- `email` - Get user's email address (optional but recommended)

These are already configured in the code and will be requested automatically.

## Step 6: Test Your Setup

### Local Development
1. Make sure your `.env` file is configured
2. Start your development server:
   ```bash
   npm run dev
   ```
3. Navigate to `http://localhost:5173`
4. Click **"Sign in with Discord"**
5. You should be redirected to Discord's authorization page
6. After authorizing, you'll be redirected back to your dashboard

### Production
1. Deploy to Vercel with environment variables set
2. Update your Discord OAuth redirect URI to match your production URL
3. Test the login flow on your production site

## Advanced: Full OAuth Flow (Optional Backend)

For production use, you should implement a backend to:
1. Exchange the authorization code for an access token (keeps client secret secure)
2. Verify the access token
3. Store user sessions securely
4. Refresh tokens when needed

### Backend Example (Node.js/Express)

```javascript
// callback endpoint
app.get('/api/auth/discord/callback', async (req, res) => {
    const { code } = req.query;
    
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
    
    // Store user session and return to frontend
    req.session.user = user;
    res.redirect('/');
});
```

## Security Considerations

### Current Implementation (Client-Side Only)
⚠️ **Warning**: The current implementation is simplified for demonstration purposes. It:
- Does not securely exchange the authorization code for an access token
- Does not use the client secret (which should NEVER be exposed to the frontend)
- Uses a mock user for demonstration

### Production Recommendations
1. **Add a Backend API**: 
   - Handle the OAuth code exchange server-side
   - Keep your Discord client secret secure
   - Implement proper session management

2. **Use HTTPOnly Cookies**: 
   - Store session tokens in HTTPOnly cookies
   - Prevents XSS attacks

3. **Implement CSRF Protection**: 
   - Use CSRF tokens for state management
   - Validate state parameter in OAuth flow

4. **Add Rate Limiting**: 
   - Prevent brute force attacks
   - Limit OAuth attempts per IP

5. **Role-Based Access Control**: 
   - Check Discord roles/permissions
   - Only allow specific roles to access dashboard
   - Example: Only users with "Admin" role in your Discord server

## Role-Based Authorization (Recommended)

To restrict access to specific Discord roles:

1. Add `guilds` and `guilds.members.read` scopes to OAuth
2. Check if user has required role in your Discord server
3. Deny access if user doesn't have the required role

Example backend check:
```javascript
// Check if user has admin role in your server
const guildId = process.env.DISCORD_SERVER_ID;
const memberResponse = await fetch(
    `https://discord.com/api/users/@me/guilds/${guildId}/member`,
    {
        headers: {
            Authorization: `Bearer ${tokens.access_token}`,
        },
    }
);

const member = await memberResponse.json();
const hasAdminRole = member.roles.includes(process.env.ADMIN_ROLE_ID);

if (!hasAdminRole) {
    return res.status(403).json({ error: 'Unauthorized' });
}
```

## Troubleshooting

### "OAuth is not configured" Error
- Make sure `VITE_DISCORD_CLIENT_ID` is set in your `.env` file
- Restart your dev server after adding environment variables

### Redirect URI Mismatch
- Ensure the redirect URI in Discord matches exactly (including protocol and port)
- Check for trailing slashes

### "Invalid Client" Error
- Verify your Client ID is correct
- Make sure you're using the Client ID, not the Application ID (they should be the same)

### Cannot Read User Data
- Check that you've requested the correct scopes (`identify`, `email`)
- Verify the access token is being sent correctly

## Resources

- [Discord OAuth2 Documentation](https://discord.com/developers/docs/topics/oauth2)
- [Discord API Documentation](https://discord.com/developers/docs/intro)
- [OAuth 2.0 Specification](https://oauth.net/2/)

## Support

If you encounter any issues:
1. Check the browser console for errors
2. Verify all environment variables are set correctly
3. Ensure your Discord application is properly configured
4. Check that your redirect URI is whitelisted in Discord

