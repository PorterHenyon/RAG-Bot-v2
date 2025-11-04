# Test Your Discord OAuth Setup

## Quick Checklist ✅

Before running, make sure:
- [ ] `.env` file exists in project root
- [ ] `VITE_DISCORD_CLIENT_ID` is set in `.env`
- [ ] `VITE_DISCORD_REDIRECT_URI` is set in `.env` 
- [ ] Redirect URI is added in Discord Developer Portal
- [ ] Dev server is stopped (if running) before starting again

---

## Step-by-Step Testing

### 1. Verify `.env` File

Your `.env` file should look like this:

```env
VITE_DISCORD_CLIENT_ID=123456789012345678
VITE_DISCORD_REDIRECT_URI=http://localhost:5173/callback
```

**Replace** `123456789012345678` with your actual Discord bot's Client ID.

### 2. Start the Dev Server

```bash
npm run dev
```

**Important**: If the server was already running, stop it (Ctrl+C) and restart it. Environment variables are only loaded on startup.

### 3. Test the Login Page

1. Open http://localhost:5173 in your browser
2. You should see:
   - ✅ Beautiful purple/indigo gradient background
   - ✅ Large "Sign in with Discord" button (Discord blue color)
   - ✅ Info box explaining OAuth benefits
   - ✅ "RAG Bot Dashboard" title

**If you see an error about OAuth not configured:**
- Make sure `.env` file is in the project root (same folder as `package.json`)
- Restart the dev server (environment variables need a restart to load)
- Check that the variable is named exactly `VITE_DISCORD_CLIENT_ID` (with `VITE_` prefix)

### 4. Test Discord OAuth Flow

1. Click **"Sign in with Discord"**
2. You should be redirected to Discord's authorization page
3. It should say: **"[Your Bot Name] wants to access your account"**
4. Click **"Authorize"**
5. You should be redirected back to your dashboard
6. You should see a loading spinner, then either:
   - ✅ Success message and redirect to dashboard
   - ❌ Error message

**If you get "Redirect URI mismatch" error:**
- Go to Discord Developer Portal → Your Bot → OAuth2 → General
- Make sure `http://localhost:5173/callback` is listed under Redirects (exact match, no typos)
- Save changes if you added it

### 5. Verify Dashboard Display

After successful login, check:
- [ ] You're on the main dashboard (not login page)
- [ ] Top-right header shows your Discord username
- [ ] Your Discord avatar appears (or Discord icon if no avatar)
- [ ] Red "Logout" button is visible
- [ ] Sidebar is visible on the left
- [ ] You can navigate between different tabs

### 6. Test Session Persistence

1. Refresh the page (F5 or Ctrl+R)
2. You should stay logged in
3. You should NOT be redirected to login page

### 7. Test Logout

1. Click the **"Logout"** button in top-right
2. Confirm the logout dialog
3. You should be redirected to login page
4. Your session should be cleared

### 8. Test Input Fields (Bug Fix Verification)

1. Navigate to **RAG Management** tab
2. Click **"Add New Response"**
3. In the "Trigger keywords" field:
   - Try typing: `help, support, info`
   - Commas should work ✅
   - Spaces should work ✅
   - Text should be visible (white color) ✅
4. Click **"Add New Entry"** (Knowledge Base)
5. In the "Keywords" field:
   - Try typing: `error, fix, crash`
   - Should work smoothly ✅
6. Create a test entry and try editing it
7. Edit form should also allow commas and spaces ✅

---

## Common Issues & Solutions

### Issue: "OAuth is not configured" Alert

**Cause**: Environment variables not loaded or incorrect

**Solutions**:
1. Verify `.env` file exists in project root
2. Check variable name is `VITE_DISCORD_CLIENT_ID` (not `DISCORD_CLIENT_ID`)
3. Restart dev server (Ctrl+C, then `npm run dev`)
4. Check for typos in `.env` file
5. Make sure there are no quotes around the values

```env
# ✅ Correct
VITE_DISCORD_CLIENT_ID=123456789012345678

# ❌ Wrong
VITE_DISCORD_CLIENT_ID="123456789012345678"
```

### Issue: Redirected to Discord but Can't Authorize

**Cause**: Redirect URI mismatch

**Solutions**:
1. Go to Discord Developer Portal
2. Select your bot application
3. OAuth2 → General → Redirects
4. Make sure `http://localhost:5173/callback` is listed
5. Click "Save Changes"
6. Try logging in again

### Issue: Stuck on "Authenticating..." Screen

**Cause**: OAuth callback not processing correctly

**Solutions**:
1. Check browser console (F12) for errors
2. Make sure you're using the correct Client ID
3. Try logging out of Discord in your browser and try again
4. Clear browser cache and cookies for localhost

### Issue: Avatar Not Showing

**Cause**: Either you don't have a Discord avatar, or it's a normal fallback

**Solutions**:
- If you don't have a Discord avatar set, a Discord icon will show (this is normal)
- If you do have an avatar, hard refresh (Ctrl+Shift+R)
- Check browser console for any image loading errors

### Issue: Can't Type Commas or Spaces in Keywords

**Cause**: Browser cache showing old code

**Solutions**:
1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache for localhost
3. Restart dev server
4. Try in incognito/private window

### Issue: Page is Blank/White Screen

**Cause**: JavaScript error or build issue

**Solutions**:
1. Open browser console (F12) to see errors
2. Run `npm install` to ensure all dependencies are installed
3. Delete `node_modules` folder and run `npm install` again
4. Check for any TypeScript errors in terminal

---

## Browser Console Testing

Open browser console (F12) and check for:

### Good Signs ✅
- No red errors
- You might see: `Received Discord code: [some code]` (this is normal)
- You might see: `🔍 RagManagementView - pendingRagEntries updated` (this is normal)

### Bad Signs ❌
- Red error messages
- "Failed to fetch" errors
- "Unexpected token" errors
- CORS errors

---

## Testing Checklist

Run through this checklist:

### Login Flow
- [ ] Login page loads with Discord button
- [ ] Clicking button redirects to Discord
- [ ] Discord shows authorization prompt
- [ ] After authorizing, redirects back to dashboard
- [ ] Dashboard loads successfully
- [ ] User info appears in header

### Display
- [ ] Discord username shows in header
- [ ] Avatar or Discord icon shows
- [ ] Logout button is visible and red
- [ ] Sidebar is present
- [ ] All tabs are accessible

### Session Management
- [ ] Refreshing page keeps you logged in
- [ ] Logging out clears session
- [ ] After logout, must re-authenticate

### Input Fields (Bug Fix)
- [ ] Can type commas in new auto-response triggers
- [ ] Can type spaces in new auto-response triggers
- [ ] Can type commas in new knowledge base keywords
- [ ] Can type spaces in new knowledge base keywords
- [ ] Edit forms also work correctly
- [ ] Text is visible (white on dark background)

### Overall Functionality
- [ ] Can navigate between tabs
- [ ] Can create new entries
- [ ] Can edit entries
- [ ] Can delete entries (with confirmation)
- [ ] Dashboard is responsive

---

## Expected Behavior

### First Visit
1. See login page
2. Click "Sign in with Discord"
3. Authorize on Discord
4. Return to dashboard and see main view

### Return Visit (same browser session)
1. Open localhost:5173
2. Automatically logged in
3. Go straight to dashboard

### After Browser Restart
1. Open localhost:5173
2. See login page again
3. Need to authenticate again

---

## Manual Testing Script

Copy and paste these tests:

```
1. Login Test:
   - Open http://localhost:5173
   - Expected: Login page with Discord button
   - Click "Sign in with Discord"
   - Expected: Redirected to Discord
   - Authorize
   - Expected: Return to dashboard with username in header

2. Session Test:
   - Refresh page
   - Expected: Stay logged in

3. Input Test:
   - Go to RAG Management
   - Click "Add New Response"
   - Type "help, support, info" in triggers
   - Expected: All characters work, text is visible

4. Logout Test:
   - Click Logout button
   - Confirm dialog
   - Expected: Return to login page

5. Re-login Test:
   - Click "Sign in with Discord" again
   - Expected: Faster login (may skip Discord auth if recently used)
```

---

## Success Criteria ✅

Your setup is working correctly if:

1. ✅ Login page appears on first visit
2. ✅ Discord OAuth flow completes successfully
3. ✅ Dashboard loads after authentication
4. ✅ Username and avatar display in header
5. ✅ Can navigate all tabs
6. ✅ Can type commas and spaces in keyword fields
7. ✅ Session persists across refreshes
8. ✅ Logout works correctly

---

## Next Steps After Successful Testing

Once everything works:

1. **For Production Deployment**:
   - Update Discord redirect URI to production URL
   - Set environment variables in Vercel/hosting platform
   - Deploy and test production OAuth flow

2. **Optional Enhancements**:
   - Add role-based access control
   - Implement backend OAuth token exchange
   - Add more security features

---

## Need Help?

If something isn't working:

1. Check browser console (F12) for errors
2. Check terminal for server errors
3. Verify `.env` file contents
4. Verify Discord Developer Portal settings
5. Try in incognito window
6. Restart dev server
7. Clear browser cache

**Still stuck?** Look for specific error messages and check the troubleshooting section in [DISCORD_OAUTH_SETUP.md](./DISCORD_OAUTH_SETUP.md)

