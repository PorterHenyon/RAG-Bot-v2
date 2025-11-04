# How to Clear Your Session and Test Login

## Why Am I Already Logged In?

The dashboard uses `sessionStorage` to remember your login. If you tested it before, you're still logged in!

---

## Method 1: Use Logout Button (Easiest)

1. Look at the top-right corner of the dashboard
2. Click the red **"Logout"** button
3. Confirm the logout
4. You'll be taken to the login page
5. Now you can test the Discord login!

---

## Method 2: Clear Browser Data

### Chrome/Edge:
1. Press **F12** to open Developer Tools
2. Go to **Application** tab
3. Find **Session Storage** in left sidebar
4. Click on `http://localhost:5173`
5. Right-click → **Clear**
6. Refresh the page (F5)

### Firefox:
1. Press **F12** to open Developer Tools
2. Go to **Storage** tab
3. Find **Session Storage**
4. Click on `http://localhost:5173`
5. Right-click → **Delete All**
6. Refresh the page (F5)

---

## Method 3: Incognito/Private Window

1. Open an **Incognito Window** (Ctrl+Shift+N in Chrome)
2. Go to `http://localhost:5173`
3. You'll see the login page (fresh session)
4. Test Discord login there

---

## Method 4: Clear Using Browser Console

1. Press **F12** to open console
2. Go to **Console** tab
3. Type: `sessionStorage.clear()`
4. Press Enter
5. Refresh page (F5)

---

## After Clearing Session

You should see:
- ✅ Beautiful purple/indigo login page
- ✅ "Sign in with Discord" button
- ✅ Info box about OAuth

---

## Session Behavior Explained

### Normal Behavior:
- **First visit** → Shows login page
- **After logging in** → Redirects to dashboard
- **Refresh page** → Stays logged in (session persists)
- **Close browser** → Session clears, need to login again

### What Happened to You:
You tested login before, so the session is still active. That's why you see the dashboard immediately!

---

## Quick Command to Clear Session

Paste this in browser console (F12 → Console tab):

```javascript
sessionStorage.clear(); location.reload();
```

This clears session and refreshes the page automatically!

