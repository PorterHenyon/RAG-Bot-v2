# Vercel Storage Optimization Guide 💾

## Current Situation

Vercel KV (Redis) has storage limits:
- **Free Tier**: 256 MB storage, 10,000 reads/day
- **Hobby Tier**: 1 GB storage, 100,000 reads/day ($20/month)
- **Pro Tier**: 10 GB storage, 1M reads/day ($20/month + usage)

If you've run out of storage, here are your options:

## Option 1: Optimize Current Vercel KV Usage (Recommended First Step)

### 1. Clean Up Old Data
The bot already has automatic cleanup, but you can manually reduce storage:

1. **Delete old forum posts**: Old solved posts are automatically cleaned up based on `solved_post_retention_days` setting
2. **Remove unused RAG entries**: Delete entries that are no longer relevant
3. **Clear old auto-responses**: Remove outdated auto-responses

### 2. Reduce Data Size
- **Compress RAG entries**: Remove unnecessary content from RAG entries
- **Limit forum post history**: Reduce `solved_post_retention_days` in bot settings
- **Clean up pending RAG entries**: Review and approve/reject pending entries

### 3. Check Storage Usage
You can check your Vercel KV storage usage in the Vercel dashboard:
1. Go to your project → **Storage** tab
2. Click on your KV database
3. View storage usage and keys

## Option 2: Use External Redis (Cheaper Alternative)

### Redis Cloud (Recommended)
- **Free Tier**: 30 MB storage (enough for small bots)
- **Fixed Plan**: $5/month for 100 MB
- **Flexible Plan**: Pay-as-you-go

**Setup:**
1. Sign up at https://redis.com/try-free/
2. Create a free database
3. Get connection URL
4. Add `REDIS_URL` environment variable to Vercel
5. The bot will automatically use it (already configured!)

### Upstash Redis
- **Free Tier**: 10,000 commands/day, 256 MB storage
- **Pay-as-you-go**: Very affordable

**Setup:**
1. Sign up at https://upstash.com/
2. Create Redis database
3. Get REST API URL and token
4. Use as `REDIS_URL` or configure as Vercel KV alternative

## Option 3: Use Supabase (Alternative to Vercel KV)

Supabase offers PostgreSQL with generous free tier:
- **Free Tier**: 500 MB database, unlimited API requests
- **Pro Tier**: $25/month for 8 GB

**Migration Steps:**
1. Create Supabase project
2. Create tables for RAG entries, auto-responses, forum posts
3. Update `api/data.ts` to use Supabase client
4. Add `SUPABASE_URL` and `SUPABASE_KEY` to Vercel env vars

## Option 4: Use Railway PostgreSQL (If Already Using Railway)

If you're already using Railway for the bot, you can add PostgreSQL:
- **Starter Plan**: $5/month for 1 GB storage
- **Pro Plan**: $20/month for 8 GB storage

**Benefits:**
- Same platform as your bot
- Easy integration
- Reliable and fast

## Option 5: Hybrid Approach (Best of Both Worlds)

Use **Vercel KV for active data** (RAG entries, auto-responses) and **external storage for forum posts**:
- Keep RAG entries in Vercel KV (small, frequently accessed)
- Store forum posts in external Redis/PostgreSQL (larger, less frequently accessed)

## Recommended Action Plan

1. **Immediate**: Check Vercel KV storage usage and clean up old data
2. **Short-term**: Set up Redis Cloud (free tier) as backup/alternative
3. **Long-term**: Consider migrating forum posts to external storage if they're taking too much space

## Storage Usage Breakdown

Typical storage per item:
- **RAG Entry**: ~1-5 KB (title, content, keywords)
- **Auto-Response**: ~0.5-2 KB (trigger, response)
- **Forum Post**: ~2-10 KB (title, content, metadata)
- **Bot Settings**: ~1 KB

**Example**: 1000 RAG entries + 100 auto-responses + 500 forum posts ≈ 5-10 MB

## Cost Comparison

| Service | Free Tier | Paid Tier | Best For |
|---------|-----------|-----------|----------|
| Vercel KV | 256 MB | $20/month (1 GB) | Small bots, active data |
| Redis Cloud | 30 MB | $5/month (100 MB) | Medium bots, cost-effective |
| Upstash | 256 MB | Pay-as-you-go | Flexible usage |
| Supabase | 500 MB | $25/month (8 GB) | Large bots, relational data |
| Railway PostgreSQL | - | $5/month (1 GB) | If already using Railway |

## Quick Fix: Increase Cleanup Frequency

You can reduce storage by cleaning up old data more aggressively:

1. **Reduce retention days**: Set `solved_post_retention_days` to 7-14 days (default is 30)
2. **Enable aggressive cleanup**: The bot already cleans up old threads every 3 hours
3. **Manual cleanup**: Use `/status` command to see current data sizes

---

**Need help?** Check the bot logs for storage-related warnings or errors.

