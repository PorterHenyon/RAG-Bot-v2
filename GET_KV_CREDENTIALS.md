# How to Get KV_REST_API_URL and KV_REST_API_TOKEN

## Step-by-Step Guide:

### Step 1: Go to Your Vercel Project

1. Open: https://vercel.com/dashboard
2. Find your project: **rag-bot-v2-lcze** (or whatever it's named)
3. Click on the project to open it

### Step 2: Navigate to Storage Tab

1. Look at the top menu bar in your project
2. Click on **"Storage"** tab (it's next to "Deployments", "Settings", etc.)

### Step 3: Create KV Database (If Not Already Created)

1. If you see **"Create Database"** button, click it
2. Select **"KV"** (Key-Value / Redis)
3. Choose a name (e.g., `rag-bot-storage`)
4. Select a region (choose closest to you)
5. Click **"Create"**

### Step 4: Get the Credentials

After the KV database is created:

1. **Click on your KV database** (the one you just created, or if it already exists)

2. You'll see several tabs at the top:
   - **Data** 
   - **Settings**
   - **Usage**
   - **.env.local** ← **Click this one!**

3. In the **.env.local** tab, you'll see two variables:

   ```
   KV_REST_API_URL=https://your-database-url.kv.vercel-storage.com
   KV_REST_API_TOKEN=your-long-token-here
   ```

4. **Copy these values!**

### Step 5: Add to Environment Variables

1. Go back to your project (click project name in breadcrumb)
2. Click **"Settings"** tab
3. Click **"Environment Variables"** in the left sidebar
4. Click **"Add New"** button

5. **Add first variable:**
   - **Name:** `KV_REST_API_URL`
   - **Value:** (paste the URL you copied from .env.local)
   - **Environments:** Select all three:
     - ☑️ Production
     - ☑️ Preview  
     - ☑️ Development
   - Click **"Save"**

6. **Add second variable:**
   - Click **"Add New"** again
   - **Name:** `KV_REST_API_TOKEN`
   - **Value:** (paste the token you copied from .env.local)
   - **Environments:** Select all three again
   - Click **"Save"**

### Step 6: Redeploy

After adding environment variables:

1. Go to **"Deployments"** tab
2. Find your latest deployment
3. Click the **3 dots** (⋯) menu
4. Click **"Redeploy"**
5. Or simply push to GitHub (it will auto-redeploy)

## Alternative: If You Don't See ".env.local" Tab

If the KV database exists but you don't see the `.env.local` tab:

1. Click on your **KV database**
2. Click **"Settings"** tab
3. Look for **"Connection Details"** or **"API Details"**
4. You should see:
   - **REST API URL** or **Endpoint**
   - **REST API Token** or **Token**

Copy those values!

## Still Can't Find It?

If you're having trouble:

1. Make sure you've **created a KV database** (not Postgres, not Blob - specifically **KV**)
2. Make sure you're in the **correct project** (rag-bot-v2-lcze)
3. The `.env.local` tab should appear once you click on your KV database

## Visual Guide:

```
Vercel Dashboard
  └─ Your Project (rag-bot-v2-lcze)
      └─ Storage Tab
          └─ KV Database (click it)
              └─ .env.local Tab ← CLICK HERE!
                  └─ Copy these two values:
                      • KV_REST_API_URL
                      • KV_REST_API_TOKEN
```

## Quick Checklist:

- [ ] Went to Vercel Dashboard
- [ ] Opened project: rag-bot-v2-lcze
- [ ] Clicked "Storage" tab
- [ ] Created/found KV database
- [ ] Clicked on KV database
- [ ] Clicked ".env.local" tab
- [ ] Copied KV_REST_API_URL
- [ ] Copied KV_REST_API_TOKEN
- [ ] Added both as Environment Variables
- [ ] Redeployed

Good luck! 🚀

