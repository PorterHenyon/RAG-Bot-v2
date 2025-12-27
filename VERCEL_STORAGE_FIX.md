# Vercel Storage Fix - Quick Action Guide 🚨

## Immediate Problem
You've run out of storage on Vercel KV. Here are your options, ranked by speed and cost:

---

## ⚡ **Option 1: Quick Cleanup (FREE - Do This First!)**

### Step 1: Check Current Storage Usage
1. Go to Vercel Dashboard → Your Project → **Storage** tab
2. Click on your KV database
3. Check the storage usage bar

### Step 2: Clean Up Old Data via API
I've created a cleanup endpoint. You can use it via curl or your dashboard:

**Clean up old forum posts (keeps last 7 days):**
```bash
curl -X POST https://your-vercel-app.vercel.app/api/cleanup-storage \
  -H "Content-Type: application/json" \
  -d '{"action": "cleanup_forum_posts", "options": {"retentionDays": 7}}'
```

**Clear all pending RAG entries:**
```bash
curl -X POST https://your-vercel-app.vercel.app/api/cleanup-storage \
  -H "Content-Type: application/json" \
  -d '{"action": "cleanup_pending_rag"}'
```

**Check storage usage:**
```bash
curl https://your-vercel-app.vercel.app/api/cleanup-storage
```

### Step 3: Reduce Retention in Bot Settings
1. Go to your dashboard → Settings
2. Set `solved_post_retention_days` to **7-14 days** (default is 30)
3. This will automatically clean up old posts more aggressively

---

## 💰 **Option 2: Switch to External Redis (RECOMMENDED - $0-5/month)**

Your code already supports external Redis! This is cheaper than Vercel KV.

### Redis Cloud (Free Tier Available)
1. **Sign up**: https://redis.com/try-free/
2. **Create database**: Choose free tier (30 MB) or fixed plan ($5/month for 100 MB)
3. **Get connection URL**: Copy the Redis URL (format: `redis://default:password@host:port`)
4. **Add to Vercel**:
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add: `REDIS_URL` = your Redis connection URL
   - Select: Production, Preview, Development
   - Click Save
5. **Redeploy**: The bot will automatically use Redis instead of Vercel KV

### Upstash Redis (Alternative)
1. **Sign up**: https://upstash.com/
2. **Create database**: Free tier (256 MB, 10k commands/day)
3. **Get REST API URL and token**
4. **Add to Vercel**:
   - `REDIS_URL` = your Upstash Redis URL
   - Or use `KV_REST_API_URL` and `KV_REST_API_TOKEN` format

**Benefits:**
- ✅ Cheaper than Vercel KV ($0-5/month vs $20/month)
- ✅ More storage (30-256 MB free vs 256 MB on Vercel)
- ✅ Already supported in your code (no code changes needed!)
- ✅ Same Redis protocol, works seamlessly

---

## 📈 **Option 3: Upgrade Vercel Plan**

If you want to stay on Vercel KV:
- **Hobby Plan**: $20/month → 1 GB storage
- **Pro Plan**: $20/month + usage → 10 GB storage

**To upgrade:**
1. Go to Vercel Dashboard → Settings → Billing
2. Upgrade to Hobby or Pro plan
3. Your KV storage limit increases automatically

---

## 🔄 **Option 4: Hybrid Approach (Best Long-term)**

Use **Vercel KV for small, frequently accessed data** and **external Redis for large data**:

- **Vercel KV**: RAG entries, auto-responses, bot settings (small, < 10 MB)
- **External Redis**: Forum posts (large, can grow to 100+ MB)

This requires code changes to split storage, but maximizes cost efficiency.

---

## 📊 **Storage Usage Breakdown**

Typical sizes:
- **RAG Entry**: ~1-5 KB each
- **Auto-Response**: ~0.5-2 KB each
- **Forum Post**: ~2-10 KB each
- **Bot Settings**: ~1 KB

**Example**: 
- 1000 RAG entries = ~5 MB
- 100 auto-responses = ~0.2 MB
- 500 forum posts = ~5 MB
- **Total**: ~10 MB

If you have 2000+ forum posts, that's likely your storage issue.

---

## ✅ **Recommended Action Plan**

1. **RIGHT NOW** (5 minutes):
   - Run cleanup API to delete old forum posts
   - Clear pending RAG entries
   - Check storage usage

2. **TODAY** (30 minutes):
   - Set up Redis Cloud (free tier)
   - Add `REDIS_URL` to Vercel environment variables
   - Redeploy

3. **THIS WEEK**:
   - Monitor storage usage
   - Adjust retention settings if needed
   - Consider upgrading if still hitting limits

---

## 🛠️ **Troubleshooting**

**"Cleanup didn't free enough space"**
- Reduce retention days further (try 3-5 days)
- Manually delete old RAG entries from dashboard
- Check if forum posts are the main issue

**"Redis connection failed"**
- Verify `REDIS_URL` is correct
- Check Redis Cloud dashboard for connection status
- Make sure Redis allows connections from Vercel IPs (most do by default)

**"Still using Vercel KV after adding Redis"**
- Make sure you redeployed after adding environment variable
- Check Vercel logs to see which storage is being used
- The code prefers Redis if `REDIS_URL` is set

---

## 💡 **Pro Tips**

1. **Monitor storage**: Set up alerts in Redis Cloud dashboard
2. **Regular cleanup**: Run cleanup API weekly/monthly
3. **Archive old data**: Export old forum posts to JSON before deleting
4. **Optimize RAG entries**: Remove unnecessary content from entries

---

**Need help?** Check the bot logs or Vercel function logs for storage-related errors.

