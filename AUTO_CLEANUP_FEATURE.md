# 🧹 Auto-Cleanup Feature - Solved Post Deletion

## ✅ What Was Added

### New Feature: Automatic deletion of old solved/closed posts

**Purpose:** Keep your dashboard clean and performant by automatically removing old solved posts that no longer need to be tracked.

---

## 🎯 How It Works

### Background Task:
- **Runs:** Every 24 hours (daily)
- **Checks:** All posts with status "Solved" or "Closed"
- **Deletes:** Posts older than the retention threshold
- **Default:** 30 days retention

### What Gets Deleted:
✅ Posts with status "Solved"  
✅ Posts with status "Closed"  
❌ Never deletes: "Unsolved", "AI Response", "Human Support", "High Priority"

---

## 🎮 New Slash Command

### `/set_solved_post_retention days:`

**Purpose:** Configure how long to keep solved posts before deletion

**Usage:**
```
/set_solved_post_retention days: 30
```

**Parameters:**
- `days` - Number of days to retain solved posts (1-365)

**Examples:**
```
/set_solved_post_retention days: 7   ← Keep for 1 week
/set_solved_post_retention days: 30  ← Keep for 1 month (default)
/set_solved_post_retention days: 90  ← Keep for 3 months
```

**Response:**
```
✅ Solved post retention updated to 30 days!

Posts with status Solved or Closed older than 30 days will be automatically deleted.
The cleanup task runs daily to check for old posts.

💡 This helps keep your dashboard clean and improves performance.
```

---

## 📊 Configuration

### Bot Settings (`bot_settings.json`):
```json
{
  "solved_post_retention_days": 30,
  ...
}
```

### View in `/status` Command:
```
⏱️ Timers & Cleanup
Satisfaction Delay: 15s
Active Timers: 2
Post Inactivity: 12h
Post Retention: 30d  ← NEW!
```

---

## 🔄 Background Task Schedule

| Task | Frequency | Purpose |
|------|-----------|---------|
| `sync_data_task` | Every 1 hour | Sync RAG/Auto-responses from dashboard |
| `check_old_posts` | Every 1 hour | Escalate inactive posts to High Priority |
| `cleanup_old_solved_posts` | Every 24 hours | **NEW! Delete old solved posts** |

---

## 📝 Console Output

### On Bot Startup:
```
✓ Started background task: check_old_posts (runs every hour)
✓ Started background task: cleanup_old_solved_posts (runs daily)  ← NEW!
```

### When Cleanup Runs:
```
🧹 Cleaning up solved posts older than 30 days...
🗑️ Deleting old post: 'Fix for honey conversion issue' (35.2 days old)
✅ Deleted: 'Fix for honey conversion issue'
🗑️ Deleting old post: 'License activation help' (42.1 days old)
✅ Deleted: 'License activation help'
✅ Cleanup complete: Deleted 2 old post(s)
```

### When No Cleanup Needed:
```
🧹 Cleaning up solved posts older than 30 days...
✓ No old posts found (retention: 30 days)
```

---

## 🧪 Testing

### Test 1: Set Retention Time
```bash
1. Run: /set_solved_post_retention days: 1
2. Check: Bot responds with success message
3. Verify: bot_settings.json shows "solved_post_retention_days": 1
4. Run: /status
5. Verify: Shows "Post Retention: 1d"
```

### Test 2: Manual Trigger (for testing)
Since the task runs daily, you can test it by:
```bash
1. Set very short retention: /set_solved_post_retention days: 1
2. Create test posts and mark them as solved
3. Wait 24 hours OR restart bot (tasks run on startup too)
4. Check console logs for cleanup messages
5. Verify dashboard shows posts are gone
```

### Test 3: Verify Only Solved/Closed Posts Deleted
```bash
1. Create posts with different statuses
2. Mark some as "Solved", some as "Unsolved", some as "Human Support"
3. Wait for cleanup to run
4. Verify: Only "Solved" and "Closed" posts get deleted
5. Other statuses remain untouched
```

---

## ⚙️ Technical Details

### Post Age Calculation:
```python
age_days = (now - created_at).total_seconds() / 86400
```

### Deletion Criteria:
```python
# Only delete if:
1. Status is "Solved" OR "Closed"
2. Age in days > retention threshold
```

### API Call:
```python
delete_payload = {
    'action': 'delete',
    'postId': 'POST-1234567890'
}
```

---

## 💡 Why This Feature?

### Benefits:
1. **Cleaner Dashboard** - Only see relevant, active posts
2. **Better Performance** - Fewer posts to load and display
3. **Easier Management** - Focus on current issues, not old history
4. **Scalability** - Dashboard won't slow down over time

### Use Cases:
- **High Volume Support** - Delete after 7-14 days to keep dashboard fast
- **Archive Mode** - Set to 90-180 days to keep longer history
- **Minimal Retention** - Set to 1-3 days for ultra-clean dashboard

---

## 🚨 Important Notes

### What Happens to Deleted Posts:
- ❌ **Dashboard:** Post is completely removed
- ✅ **Discord:** Thread remains unchanged (locked/archived)
- ✅ **RAG Entries:** Any RAG entries created remain in knowledge base

### Manual Deletion Still Works:
- You can still manually delete posts from the dashboard anytime
- This feature only affects **automatic** deletion

### No Undo:
- Once deleted by cleanup task, posts cannot be recovered
- Consider your retention period carefully

---

## 📋 Updated Command List

Now **14 total commands**:

| # | Command | Purpose |
|---|---------|---------|
| 1 | `/reload` | Reload data from dashboard |
| 2 | `/stop` | Stop bot gracefully |
| 3 | `/ask` | Test knowledge base |
| 4 | `/mark_as_solve` | Create pending RAG entry |
| 5 | `/mark_as_solve_no_review` | Close without RAG |
| 6 | `/set_forums_id` | Set forum channel |
| 7 | `/set_ignore_post_id` | Ignore specific posts |
| 8 | `/set_satisfaction_delay` | Set satisfaction timer |
| 9 | `/set_temperature` | Set AI creativity |
| 10 | `/set_max_tokens` | Set response length |
| 11 | `/status` | Check bot status |
| 12 | `/check_rag_entries` | List RAG entries |
| 13 | `/check_auto_entries` | List auto-responses |
| 14 | `/api_info` | View API config (private) |
| 15 | `/set_post_inactivity_time` | Set escalation time |
| **16** | **`/set_solved_post_retention`** | **⭐ NEW! Set cleanup time** |

---

## 🔮 Future Enhancement Ideas

As you mentioned, compression could be added later:

### Potential Compression Feature:
Instead of deleting, could compress old posts:
- Archive to JSON file
- Compress with gzip
- Store locally or in cloud storage
- Option to restore if needed

**Implementation Priority:** Low (deletion works well for most use cases)

---

## ✅ Summary

### What's New:
- ✅ `/set_solved_post_retention` command (1-365 days)
- ✅ Daily background task to delete old solved posts
- ✅ Configurable retention period
- ✅ Shows in `/status` command
- ✅ Saves to `bot_settings.json`
- ✅ Shows in dashboard Slash Commands view

### Files Modified:
- `bot.py` - Added command, background task, and logic
- `api/data.ts` - Added command to slash commands list
- `hooks/useMockData.ts` - Added command to initial data

### Ready to Use:
1. Restart bot
2. Type `/set_solved_post_retention days: 30`
3. Cleanup runs automatically every 24 hours!

---

**Keeps your dashboard clean automatically!** 🎉

