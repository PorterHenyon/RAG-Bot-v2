# Database Setup Guide for Automatic Sync

Currently, the bot syncs with your dashboard **every 30 seconds** automatically. However, data is stored in-memory on Vercel, which means it resets when the server restarts.

For **persistent storage** and better reliability, you'll want to use a database. Here are your options:

## Option 1: Supabase (Recommended - Free Tier Available)

### Setup:
1. Go to https://supabase.com and create a free account
2. Create a new project
3. Get your connection string (Settings → Database → Connection String)

### Why Supabase:
- ✅ Free tier with 500MB database
- ✅ Real-time updates (perfect for automatic sync)
- ✅ Easy REST API
- ✅ PostgreSQL (industry standard)

## Option 2: MongoDB Atlas (Free Tier Available)

### Setup:
1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free account (M0 tier is free)
3. Create a cluster
4. Get your connection string

### Why MongoDB:
- ✅ Free tier with 512MB storage
- ✅ JSON-based (easy to work with)
- ✅ NoSQL flexibility

## Option 3: Vercel Postgres (Easiest for Vercel)

### Setup:
1. In your Vercel dashboard
2. Go to Storage → Create Database → Postgres
3. Free tier available

### Why Vercel Postgres:
- ✅ Integrated with Vercel
- ✅ No separate account needed
- ✅ Free tier available

## Option 4: DigitalOcean Droplet (Your Friend's Suggestion)

If your friend has a DigitalOcean Droplet, you can:

### Setup:
1. Install MongoDB or PostgreSQL on the droplet
2. Configure firewall rules to allow connections
3. Use the droplet's IP address in your connection string

### Why Droplet:
- ✅ Full control over the database
- ✅ Can host other services too
- ✅ More flexible than managed services

## Current Automatic Sync (Works Now!)

**Right now, without a database, you have:**

✅ **RAG Entries**: Auto-sync every **30 seconds** from dashboard → bot
✅ **Forum Posts**: Auto-sync every **10 seconds** from bot → dashboard
✅ **Real-time Updates**: Bot listens to Discord messages and updates posts immediately

**How it works:**
1. You add a RAG entry on the website → Saves to API immediately
2. Bot polls API every 30 seconds → Gets new RAG entry
3. Bot uses new RAG entry in responses automatically

**For Forum Posts:**
1. User creates forum post in Discord → Bot sends to API immediately
2. Dashboard polls API every 10 seconds → Shows new post
3. User sends message in thread → Bot updates API immediately
4. Dashboard shows updated conversation

## Next Steps

### Without Database (Current Setup):
- ✅ Works great for development and testing
- ✅ Automatic sync every 30 seconds
- ✅ All Discord data shows in dashboard
- ⚠️ Data resets if Vercel restarts (not persistent)

### With Database (Production):
1. Choose one of the options above
2. I can help you integrate it into the API
3. Data will persist permanently
4. Sync will be even faster

## Questions?

- **"Will RAG entries automatically go to the bot?"** → Yes! Every 30 seconds
- **"Will forum posts show Discord info?"** → Yes! Immediately with full user info
- **"Do I need a database?"** → Not for testing, but recommended for production

Would you like me to set up database integration? Just tell me which option you prefer!

