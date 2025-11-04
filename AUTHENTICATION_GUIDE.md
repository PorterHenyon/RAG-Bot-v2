# Authentication System Guide

## Overview
Your RAG Bot Dashboard now uses **Discord OAuth 2.0** for secure authentication! Users sign in with their Discord accounts to access the admin panel.

## Features

### 🔐 Discord OAuth Login
- **Secure OAuth 2.0**: Industry-standard authentication through Discord
- **No Password Management**: Users authenticate with their existing Discord account
- **Session Management**: Uses sessionStorage to keep users logged in during their browser session
- **Beautiful UI**: Modern gradient login page with Discord branding
- **Avatar Display**: Shows user's Discord avatar and username in the header

### 🎯 Why Discord OAuth?
1. **Seamless Integration**: Works perfectly with your Discord bot
2. **No Password Fatigue**: Users don't need another username/password
3. **Enhanced Security**: Leverages Discord's robust authentication
4. **Role-Based Access**: Can be extended to check Discord server roles (recommended)
5. **Professional**: Standard OAuth flow used by major applications

### 🎨 UI Components

#### Login Page (`components/Login.tsx`)
- Full-screen Discord OAuth login interface
- Large "Sign in with Discord" button with Discord branding
- Information box explaining OAuth benefits
- Professional gradient design matching Discord's style

#### OAuth Callback (`components/OAuthCallback.tsx`)
- Handles the OAuth redirect from Discord
- Shows processing, success, or error states
- Automatic redirect to dashboard on success
- Error handling with retry option

#### Header Updates (`components/Header.tsx`)
- Displays Discord avatar (or Discord icon if no avatar)
- Shows Discord username
- Logout button with confirmation dialog

### 🔄 Session Management

#### Authentication Context (`contexts/AuthContext.tsx`)
The authentication state is managed globally using React Context:

- **`isAuthenticated`**: Boolean indicating login status
- **`user`**: Discord user object (id, username, avatar, etc.)
- **`loginWithDiscord()`**: Redirects to Discord OAuth authorization
- **`handleDiscordCallback(code)`**: Processes OAuth callback code
- **`logout()`**: Clears session and returns to login page
- **`isLoading`**: Loading state for initial authentication check

#### Discord User Object
```typescript
interface DiscordUser {
    id: string;              // Discord user ID
    username: string;        // Discord username
    discriminator: string;   // Discord discriminator (e.g., "0000")
    avatar: string | null;   // Avatar hash
    email?: string;          // User's email (optional)
}
```

#### Session Persistence
- Uses `sessionStorage` to maintain login state
- Stores Discord user info securely
- Session persists across page refreshes
- Automatically cleared when browser tab/window is closed

### 🛡️ Security Features

1. **Protected Routes**: All dashboard views require authentication
2. **Session-based Auth**: Prevents unauthorized access
3. **Logout Confirmation**: Prevents accidental logouts
4. **Auto-complete Off**: Prevents browser from saving credentials (for the keywords/triggers inputs)

### 🚀 How to Use

#### Setup (First Time)

1. **Create a Discord Application**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Get your Client ID
   - See [DISCORD_OAUTH_SETUP.md](./DISCORD_OAUTH_SETUP.md) for detailed instructions

2. **Configure Environment Variables**:
   - Copy `env.example` to `.env`
   - Add your Discord Client ID
   - Set your redirect URI (e.g., `http://localhost:5173/callback`)

3. **Start the Application**:
   ```bash
   npm install
   npm run dev
   ```

#### Using the Dashboard

1. **First Time Access**:
   - Navigate to your dashboard URL (e.g., `http://localhost:5173`)
   - Click **"Sign in with Discord"**
   - Authorize the application on Discord
   - You'll be redirected back and automatically logged in

2. **Working with the Dashboard**:
   - Your Discord username and avatar appear in the top-right corner
   - Full access to all dashboard features
   - Session persists across page refreshes

3. **Logging Out**:
   - Click the **"Logout"** button in the top-right corner
   - Confirm the logout action
   - You'll be returned to the Discord login screen

### 📝 Customization

#### Restricting Access by Discord Role
To only allow specific Discord roles to access the dashboard:

1. Request additional OAuth scopes in `contexts/AuthContext.tsx`:
   ```typescript
   const scopes = 'identify email guilds guilds.members.read';
   ```

2. In your backend, check user's roles:
   ```javascript
   // Check if user has admin role
   const hasAdminRole = member.roles.includes(ADMIN_ROLE_ID);
   ```

3. See [DISCORD_OAUTH_SETUP.md](./DISCORD_OAUTH_SETUP.md) for implementation details

#### Changing Redirect URI
Edit your `.env` file:
```env
# For development
VITE_DISCORD_REDIRECT_URI=http://localhost:5173/callback

# For production
VITE_DISCORD_REDIRECT_URI=https://your-domain.com/callback
```

**Important**: Also update the redirect URI in your Discord application settings!

### 🔧 Technical Implementation

The authentication system is implemented using:
- **React Context API**: For global state management
- **sessionStorage**: For client-side session persistence
- **TypeScript**: For type safety
- **Tailwind CSS**: For beautiful, responsive UI

### 📦 Files Modified/Created

1. **New Files**:
   - `contexts/AuthContext.tsx` - Discord OAuth authentication context
   - `components/Login.tsx` - Discord OAuth login page
   - `components/OAuthCallback.tsx` - Handles OAuth callback
   - `DISCORD_OAUTH_SETUP.md` - Complete Discord OAuth setup guide
   - `env.example` - Environment variable template

2. **Modified Files**:
   - `App.tsx` - Added authentication check, loading state, and callback handling
   - `index.tsx` - Wrapped app with AuthProvider
   - `components/Header.tsx` - Display Discord avatar and username
   - `components/views/RagManagementView.tsx` - Fixed input fields for triggers/keywords

### 🐛 Troubleshooting

**Issue**: "OAuth is not configured" alert
- **Solution**: Make sure `VITE_DISCORD_CLIENT_ID` is set in your `.env` file
- Restart the dev server after adding environment variables

**Issue**: "Redirect URI mismatch" error from Discord
- **Solution**: Ensure the redirect URI in your `.env` matches exactly what's configured in Discord Developer Portal
- Check for trailing slashes and protocol (http vs https)

**Issue**: Can't type commas or spaces in keyword fields
- **Solution**: This has been fixed! The issue was with array/string conversion. Now uses separate state for editing.

**Issue**: Logged out automatically
- **Solution**: Expected behavior. Session storage clears when browser closes.

**Issue**: OAuth callback shows error
- **Solution**: Check browser console for details. Verify Discord app configuration and environment variables.

**Issue**: User avatar not showing
- **Solution**: This is normal if the user hasn't set a Discord avatar. A Discord icon placeholder is shown instead.

## Next Steps for Production

1. **Backend Integration**: 
   - Create authentication API endpoints
   - Implement proper user database
   - Use secure password hashing (bcrypt, argon2)

2. **Enhanced Security**:
   - Implement JWT tokens
   - Add refresh token mechanism
   - Use HTTPS in production
   - Add CSRF protection
   - Implement rate limiting

3. **User Management**:
   - Add user registration
   - Password reset functionality
   - User roles and permissions
   - Activity logging

4. **Testing**:
   - Add unit tests for auth logic
   - Integration tests for login flow
   - Security testing

