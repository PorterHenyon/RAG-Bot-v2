# Resource Optimization Plan

## Current Resource Usage Analysis

### 🤖 AI/Gemini API Calls (Most Expensive)
**Current:**
- Satisfaction analysis: Every thread after 15s delay
- AI responses: Every user question
- RAG entry analysis: Manual command only
- Translation: Per command

**Costs:**
- Free tier: 1,500 requests/day per key
- Current: ~50-200 requests/day (estimated)

**Optimization opportunities:**
1. ✅ Satisfaction analysis already has toggle (`satisfaction_analysis_enabled`)
2. ⚠️ Increase default satisfaction delay from 15s to 30s (less false triggers)
3. ⚠️ Add cache for similar questions (deduplicate)
4. ⚠️ Skip AI response if RAG has exact match

---

### 🚂 Railway Resources
**Current:**
- Memory: Python bot process
- CPU: Discord event handling, background tasks
- Bandwidth: Discord API, Vercel API

**Background tasks:**
- `sync_data_task`: Every 6 hours ✅ Good
- `cleanup_processed_threads`: Every 6 hours ✅ Good
- `cleanup_old_solved_posts`: Every 24 hours ✅ Good
- `check_old_posts`: Every 1 hour ⚠️ **Could increase to 2-3 hours**
- `check_leaderboard_reset`: Every 24 hours ✅ Good

**Optimization opportunities:**
1. ⚠️ Reduce `check_old_posts` to every 2-3 hours
2. ✅ Already using connection pooling
3. ⚠️ Add request deduplication

---

### ☁️ Vercel API Calls
**Current:**
- Bot syncs: Every 6 hours
- Dashboard syncs: On every data change (5s debounce)
- Forum posts: Real-time updates

**Bandwidth:**
- ~2-5 KB per sync (compressed)
- ~100-200 syncs/day

**Optimization opportunities:**
1. ⚠️ Skip sync if data hasn't changed (hash check)
2. ✅ Already using 5s debounce
3. ⚠️ Compress large payloads (gzip)
4. ⚠️ Only sync changed fields, not entire dataset

---

### 💬 Discord API Calls
**Current:**
- Message history fetching: On every thread response
- Forum post tracking: Real-time
- Command responses: Immediate

**Rate limits:**
- 50 requests/second (global)
- Current: Well within limits

**Optimization opportunities:**
1. ⚠️ Cache message history (avoid re-fetching)
2. ⚠️ Batch status updates
3. ✅ Already using deferred responses

---

## Priority Optimizations

### 🔴 High Priority (Implement Now)

#### 1. Reduce High Priority Check Frequency
**Change:** `check_old_posts` from 1 hour → 2 hours
**Savings:** 50% reduction in API calls for this task
**Impact:** Minimal (posts still escalated within 2 hours)

#### 2. Increase Satisfaction Delay Default
**Change:** Default from 15s → 30s
**Savings:** Reduces false-positive satisfaction checks
**Impact:** More time for users to respond, fewer wasted API calls

#### 3. Add Data Change Detection
**Change:** Skip Vercel sync if data hash unchanged
**Savings:** ~30-50% reduction in unnecessary syncs
**Impact:** None (only syncs when data actually changes)

#### 4. Add Response Caching
**Change:** Cache AI responses for similar questions (1 hour TTL)
**Savings:** ~10-20% reduction in Gemini calls
**Impact:** Faster responses for duplicate questions

---

### 🟡 Medium Priority (Implement Soon)

#### 5. Compress API Payloads
**Change:** Gzip large RAG database syncs
**Savings:** ~60-70% bandwidth reduction
**Impact:** Faster syncs, lower costs

#### 6. Message History Caching
**Change:** Cache thread message history for 5 minutes
**Savings:** Reduces Discord API calls
**Impact:** Faster analysis, less rate limit risk

#### 7. Batch Dashboard Updates
**Change:** Batch multiple forum post updates
**Savings:** Reduces number of Vercel calls
**Impact:** Slightly delayed updates (acceptable)

---

### 🟢 Low Priority (Nice to Have)

#### 8. Smart RAG Matching
**Change:** Skip AI if RAG confidence > 90%
**Savings:** ~5-10% Gemini calls
**Impact:** Faster responses for exact matches

#### 9. Lazy Load Forum Posts
**Change:** Only fetch recent posts on dashboard
**Savings:** Smaller API responses
**Impact:** Faster dashboard loads

---

## Implementation Order

1. ✅ **Reduce `check_old_posts` to 2 hours** (5 minutes)
2. ✅ **Increase satisfaction delay to 30s** (2 minutes)
3. ✅ **Add data hash checking** (15 minutes)
4. ✅ **Add AI response cache** (20 minutes)
5. 🔄 **Compress large payloads** (Optional - if needed)

---

## Expected Savings

### Before Optimization:
- Gemini API: ~150 calls/day
- Vercel syncs: ~150 syncs/day
- Background tasks: ~40 checks/day

### After Optimization:
- Gemini API: ~100-120 calls/day (**20-30% reduction**)
- Vercel syncs: ~75-100 syncs/day (**33-50% reduction**)
- Background tasks: ~28 checks/day (**30% reduction**)

### Cost Impact:
- **Railway:** Minimal (already efficient)
- **Vercel:** ~40% reduction in function calls
- **Gemini:** ~25% reduction in API usage
- **Overall:** Should stay comfortably within free tiers

---

## Monitoring

### Key Metrics to Track:
- Gemini API calls per day (via bot logs)
- Vercel function invocations (via Vercel dashboard)
- Railway memory/CPU usage (via Railway dashboard)
- Discord rate limit hits (should be zero)

### Success Criteria:
- ✅ Stay under 1,000 Gemini calls/day
- ✅ Stay under 100 Vercel calls/day
- ✅ Railway memory < 256 MB
- ✅ No rate limit errors

---

**Ready to implement the high-priority optimizations!** 🚀

