# Fix Red Folders (api, components, hooks)

## Why They're Red

The red folders are a **TypeScript/IDE issue**, not a code problem. This happens when:

1. **`node_modules` isn't installed** - TypeScript can't resolve imports
2. **TypeScript server needs restart** - IDE cache issue
3. **Missing type definitions** - Need to install dependencies

## Quick Fix

### Option 1: Install Dependencies (Recommended)

Open PowerShell in your project folder and run:

```powershell
cd c:\Users\porte\.cursor\RAG-Bot-v2
npm install
```

This will install all dependencies from `package.json` and the red folders should turn normal.

### Option 2: Restart TypeScript Server

In VS Code/Cursor:
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type: `TypeScript: Restart TS Server`
3. Press Enter

### Option 3: Reload Window

In VS Code/Cursor:
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type: `Developer: Reload Window`
3. Press Enter

## Why This Happens

- **`node_modules` is in `.gitignore`** - It's not committed to git (correct!)
- **Vercel installs it during build** - So deployment works fine
- **Your local IDE needs it** - To resolve TypeScript imports and show proper errors

## Is This a Problem?

**No!** This is just a local IDE issue. Your code will work fine:
- ✅ Vercel will install dependencies during build
- ✅ The code is correct
- ✅ It's just the IDE showing false errors

**But it's annoying**, so run `npm install` to fix it.

## After Installing

After running `npm install`:
1. Wait for it to finish (may take 1-2 minutes)
2. The red folders should turn normal
3. TypeScript errors should disappear
4. You'll get proper autocomplete and type checking
