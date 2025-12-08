# Dashboard Sync Configuration 📊

This document explains how the bot syncs all data from the dashboard API, ensuring everything is managed through the web interface.

## 🔄 How Dashboard Sync Works

### **Data Flow**

```
Dashboard (Vercel) → API → Bot (Railway) → Pinecone
     ↑                                    ↓
     └─────────── Sync Every 6 Hours ─────┘
```

1. **You manage data** in the web dashboard
2. **Dashboard stores** data in Vercel KV/Redis
3. **Bot syncs** from dashboard API every 6 hours
4. **Bot uploads** embeddings to Pinecone
5. **Bot uses** Pinecone for all searches

---

## 📋 What Gets Synced

### ✅ **RAG Entries**
- Title, content, keywords
- All managed in dashboard
- Automatically synced to bot
- Embeddings uploaded to Pinecone

### ✅ **Auto-Responses**
- Name, trigger keywords, response text
- All managed in dashboard
- Automatically synced to bot
- Used for keyword matching

### ✅ **Bot Settings**
- System prompt
- Temperature, delays, retention
- Notification channels
- All managed in dashboard

### ✅ **Leaderboard Data**
- Monthly scores
- Staff performance
- All managed in dashboard

---

## ⚙️ Sync Configuration

### **Sync Frequency**

```python
@tasks.loop(hours=6)  # Sync every 6 hours
async def sync_data_task():
    await fetch_data_from_api()
```

**Why 6 hours?**
- ✅ Balances freshness with cost
- ✅ Not too frequent (saves CPU)
- ✅ Not too infrequent (data stays current)
- ✅ Only recomputes if data changed

### **Smart Change Detection**

The bot uses hash comparison to detect changes:

```python
# Only process if data actually changed
if last_data_hash == current_hash:
    print("✓ Data unchanged - skipping update to save resources")
    return True
```

**Benefits:**
- ✅ Skips unnecessary processing
- ✅ Saves Railway CPU costs
- ✅ Only recomputes embeddings when needed

---

## 🔧 Configuration

### **Required Environment Variable**

```env
DATA_API_URL=https://your-app.vercel.app/api/data
```

**Where to get:**
- Your Vercel deployment URL
- Add `/api/data` to the end
- Example: `https://rag-bot-v2.vercel.app/api/data`

### **Dashboard API Endpoints**

The bot uses these endpoints:

**GET `/api/data`**
- Fetches all RAG entries, auto-responses, settings
- Returns JSON with all data

**POST `/api/data`**
- Saves data back to dashboard
- Used for leaderboard updates

---

## 📊 Sync Process

### **Step-by-Step**

1. **Bot starts up**
   - Fetches initial data from dashboard
   - Uploads embeddings to Pinecone if needed

2. **Every 6 hours**
   - Checks dashboard API for updates
   - Compares hash to detect changes
   - Updates local data if changed
   - Recomputes embeddings if RAG changed

3. **When RAG changes**
   - Detects new/updated entries
   - Computes embeddings
   - Uploads to Pinecone
   - Clears local cache (saves Railway memory)

4. **During searches**
   - Queries Pinecone (not local storage)
   - Gets results from Pinecone cloud
   - Returns relevant entries

---

## ✅ Verification

### **Check Sync Status**

Look for these messages in Railway logs:

**Successful Sync:**
```
🔗 Attempting to fetch data from: https://your-app.vercel.app/api/data
✓ Successfully connected to dashboard API!
✓ Synced X RAG entries and Y auto-responses from dashboard.
```

**No Changes:**
```
✓ Data unchanged (hash match) - skipping update to save resources
✓ Data already up to date (X RAG entries, Y auto-responses)
```

**RAG Changed:**
```
🔄 RAG database changed - uploading embeddings to Pinecone...
✅ Upserted X embeddings to Pinecone (Railway CPU saved!)
```

### **Check Dashboard Connection**

If you see:
```
⚠ Dashboard API not found (404) at https://...
ℹ Using local data. Deploy to Vercel to sync with dashboard.
```

**Fix:**
- Check `DATA_API_URL` is correct
- Verify Vercel deployment is live
- Check API endpoint is accessible

---

## 🎯 Best Practices

### **1. Always Use Dashboard**

- ✅ Add/edit RAG entries in dashboard
- ✅ Configure auto-responses in dashboard
- ✅ Update bot settings in dashboard
- ❌ Don't edit bot code directly

### **2. Verify Sync**

After making changes in dashboard:
- Wait up to 6 hours for automatic sync
- Or use `/reload_data` command for immediate sync
- Check Railway logs to verify sync

### **3. Monitor Changes**

The bot logs all changes:
```
→ RAG entries changed: 5 (was 3)
  + New RAG entry: 'Example Title' (ID: RAG-001)
    Keywords: keyword1, keyword2
```

---

## 🔍 Troubleshooting

### **"Skipping API sync - Vercel URL not configured"**

**Fix:**
- Set `DATA_API_URL` in Railway environment variables
- Make sure URL points to your Vercel deployment
- Format: `https://your-app.vercel.app/api/data`

### **"Failed to fetch data from API: Status 404"**

**Fix:**
- Verify Vercel deployment is live
- Check API endpoint exists
- Test URL in browser: `https://your-app.vercel.app/api/data`

### **"Using local data"**

**Fix:**
- Check `DATA_API_URL` is set correctly
- Verify Vercel deployment is accessible
- Check Railway logs for connection errors

### **Data Not Syncing**

**Check:**
- Is `DATA_API_URL` set in Railway?
- Is Vercel deployment live?
- Are there errors in Railway logs?
- Try `/reload_data` command for manual sync

---

## 📈 Sync Performance

### **What Happens During Sync**

1. **API Call** (minimal CPU)
   - GET request to dashboard API
   - Receives JSON data

2. **Change Detection** (minimal CPU)
   - Computes hash of data
   - Compares with previous hash

3. **Data Update** (minimal CPU)
   - Updates in-memory variables
   - No heavy processing

4. **Embedding Computation** (only if changed)
   - Only runs if RAG data changed
   - Uploads to Pinecone (not Railway storage)

**Total CPU Usage:** Very low (most syncs skip processing)

---

## ✅ Summary

**Dashboard manages:**
- ✅ All RAG entries
- ✅ All auto-responses
- ✅ Bot settings
- ✅ Leaderboard data

**Bot syncs:**
- ✅ Every 6 hours automatically
- ✅ On startup
- ✅ On `/reload_data` command

**Pinecone stores:**
- ✅ All RAG embeddings
- ✅ All vector data

**Result:**
- ✅ Everything managed in dashboard
- ✅ Bot stays in sync automatically
- ✅ Minimal Railway CPU usage
- ✅ Cost-effective solution

Your bot is fully configured to get everything from the dashboard! 🎉

