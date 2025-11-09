# 🐛 Bug Fix: Post Deletion Issue

## ✅ FIXED - Pushed to Git & Auto-Deploying on Railway

---

## 🔍 The Bug

**Problem:** Posts were being deleted immediately after being marked as "Solved", not after the configured retention period (14 days).

**What Was Happening:**
- You mark a post as "Solved" today
- The cleanup task checks when the post was **created** (e.g., 15 days ago)
- Since 15 days > 14 days retention → **DELETED immediately!** ❌

---

## 🔧 The Fix

**Changed:** Cleanup now checks `updatedAt` (when post was solved) instead of `createdAt` (when post was created)

**Before:**
```python
created_at_str = post.get('createdAt')  # ❌ Wrong!
age_days = (now - created_at).total_seconds() / 86400
```

**After:**
```python
updated_at_str = post.get('updatedAt') or post.get('createdAt')  # ✅ Correct!
age_days = (now - updated_at).total_seconds() / 86400
```

---

## 📊 How It Works Now

### Example Timeline:
1. **Day 1:** User creates forum post
2. **Day 15:** Post gets marked as "Solved"
3. **Day 15-29:** Post stays in dashboard (14 day retention)
4. **Day 29:** ✅ Cleanup task deletes post (14 days after being solved)

**Before the fix:**
- Post would be deleted immediately on Day 15 (because it was created 15 days ago)

**After the fix:**
- Post is deleted on Day 29 (14 days after being marked solved)

---

## ⚙️ Current Settings

Your bot is configured with:
- **Retention period:** 14 days (from `bot_settings.json`)
- **Cleanup frequency:** Daily (runs every 24 hours)
- **Affects:** Only posts with status "Solved" or "Closed"

---

## 🎯 What's Changed in the Code

### Line 1011-1013:
```python
# Check post age - Use updatedAt (when it was solved) NOT createdAt
# This prevents immediate deletion of old posts that were just solved
updated_at_str = post.get('updatedAt') or post.get('createdAt')
```

### Line 1031:
```python
print(f"🗑️ Deleting post that was solved {age_days:.1f} days ago: '{post_title}'")
```

---

## 🚀 Deployment Status

✅ **Committed to Git**
✅ **Pushed to GitHub**  
✅ **Railway auto-deploying now** (2-3 minutes)

**Check Railway dashboard to see:**
```
✅ SUCCESS - "Fix post deletion bug: use updatedAt instead..."
```

---

## 🛠️ How to Adjust Retention Period

If you want to change how long solved posts are kept:

### Option 1: Discord Command (Easiest)
```
/set_solved_post_retention days:30
```

### Option 2: Edit bot_settings.json
```json
{
  "solved_post_retention_days": 30
}
```

Then restart bot or it will update on next daily sync.

---

## ✅ Testing

To verify the fix is working:

1. **Mark a post as solved** (use `/mark_as_solve` or satisfaction buttons)
2. **Check the post stays in dashboard** for 14 days
3. **After 14 days**, cleanup task will remove it
4. **Logs will show:** `🗑️ Deleting post that was solved 14.X days ago: '[post title]'`

---

## 📝 Notes

- The bug only affected the **dashboard** (API storage), not Discord threads
- Discord threads are immediately locked when marked as solved (by design)
- Cleanup task runs once every 24 hours
- Deleted posts are removed from dashboard, but Discord threads remain (archived & locked)

---

**Bug is now fixed!** ✅ Railway will deploy the update automatically in ~2-3 minutes.

