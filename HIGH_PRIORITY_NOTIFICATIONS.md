# 🚨 High Priority Post Notifications

## What This Feature Does

When a forum post is escalated to **High Priority** status, the bot will automatically:

1. ✅ **Sort it to the top** of the dashboard forum posts view
2. ✅ **Send a summary list** to a designated support channel (ID: `1436918674069000212`)
3. ✅ **Ping support staff** (if a support role is configured)
4. ✅ **Post in the thread** to notify the user that support has been alerted

---

## 📋 How It Works

### Dashboard Sorting
High priority posts now **always appear first** in your dashboard's Forum Posts view, regardless of:
- Which filter you're using (All, In Progress, etc.)
- What you're searching for
- When they were created

Other posts are sorted by date (newest first) below the high priority ones.

### Auto-Escalation
Posts are automatically escalated to High Priority when:
- A post has been open for longer than the configured threshold (default: 12 hours)
- The post is not already Solved, Closed, or High Priority
- The background task runs (every hour)

### Support Notifications
When a post is escalated, the bot sends a rich embed notification to the support channel:

```
🚨 High Priority Support Needed
Post: [Title with clickable link]
User: Username
Open For: X hours

This post needs attention from the support team!
```

---

## ⚙️ Configuration

### Current Default Settings
These are configured in `BOT_SETTINGS`:

```python
'support_notification_channel_id': 1436918674069000212  # Your support channel
'support_role_id': None  # Not set yet - configure with slash command
'post_inactivity_hours': 12  # Hours before auto-escalation
'high_priority_check_interval_hours': 1.0  # How often to check (1 hour)
```

### Slash Commands (Admin Only)

#### 1. Set Support Role
Configure which role gets pinged for high priority posts:
```
/set_support_role role:@Support
```

#### 2. Set Support Notification Channel
Change the channel where notifications are sent:
```
/set_support_notification_channel channel:#support-alerts
```

#### 3. List High Priority Posts
View all current high priority posts:
```
/list_high_priority_posts
```
Shows up to 10 high priority posts with clickable links.

#### 4. Set Inactivity Threshold
Change how long before posts are escalated:
```
/set_post_inactivity_time hours:24
```
Valid range: 1-168 hours (1 hour to 7 days)

#### 5. Set Check Interval
Change how often the bot checks for high priority posts:
```
/set_ping_high_priority_interval hours:0.5
```
Valid range: 0.25-24 hours (15 minutes to 24 hours). Use `0.25` for 15 minutes, `0.5` for 30 minutes, `1.0` for 1 hour, etc.

---

## 🎯 Recommended Setup

### Step 1: Set Support Role
```
/set_support_role role:@Support Team
```
This role will be mentioned in every high priority notification.

### Step 2: Verify Channel
The support notification channel is already set to ID `1405246916760961125`.
If you need to change it:
```
/set_support_notification_channel channel:#your-channel
```

### Step 3: Test It
You can:
- Wait for a post to be auto-escalated (takes time based on your threshold)
- Manually change a post's status to "High Priority" in the dashboard
- Use `/list_high_priority_posts` to see current high priority posts

---

## 📊 What Gets Logged

The bot console will show:
```
⚠ Found old post: 'Title' (15.2 hours old, threshold: 12h)
✅ Escalated to High Priority: 'Title'
📢 Sent high priority notification to thread 123456789
✅ Notified support channel with role ping for: Title
```

---

## 🔧 Troubleshooting

### Notifications Not Sending?

1. **Check bot permissions** - Bot needs permission to send messages in the notification channel
2. **Verify channel ID** - Run `/set_support_notification_channel` to confirm it's correct
3. **Check bot console** - Look for error messages about the notification channel

### Role Not Getting Pinged?

1. **Set the support role** - Run `/set_support_role role:@YourRole`
2. **Check role permissions** - Make sure the bot can mention the role
3. **Verify bot settings** - The role might not be configured yet

### Posts Not Auto-Escalating?

1. **Check threshold** - Run `/set_post_inactivity_time` to see/change the current setting
2. **Background task timing** - The task runs every hour, so there's a delay
3. **Check post status** - Posts already marked as Solved/Closed won't escalate

---

## 💡 Best Practices

### For Support Teams
- **Set a reasonable threshold**: 12 hours is a good default for most communities
- **Configure role pings**: Ensures the right people get notified immediately
- **Use the list command**: Regularly check `/list_high_priority_posts` for overview
- **Monitor the channel**: The notification channel becomes your high-priority queue

### For Managing Load
If you're getting too many escalations:
- **Increase the threshold**: `/set_post_inactivity_time hours:24`
- **Respond faster**: Posts that get responses within the threshold won't escalate

If you're not getting enough escalations:
- **Decrease the threshold**: `/set_post_inactivity_time hours:6`
- **Check for solved posts**: Make sure to mark posts as Solved when issues are resolved

---

## 📝 Technical Details

### Files Modified
- `bot.py`:
  - Added `support_notification_channel_id` to BOT_SETTINGS
  - Added `support_role_id` to BOT_SETTINGS
  - Created `notify_support_channel()` function
  - Updated escalation logic to call notification function
  - Added `/set_support_role` command
  - Added `/set_support_notification_channel` command
  - Added `/list_high_priority_posts` command

- `components/views/ForumPostsView.tsx`:
  - Added sorting logic to prioritize High Priority posts
  - High priority posts always appear first, then sorted by date

### Data Flow
```
Background Task (every hour)
  ↓
Check all posts for age > threshold
  ↓
Update post status to "High Priority"
  ↓
Send to Dashboard API
  ↓
[Parallel Actions]
  ├─→ Send embed to thread (notify user)
  └─→ Send notification to support channel (ping support role)
```

---

## 🎉 Summary

You now have a complete high priority notification system that:
- ✅ Automatically detects posts that need attention
- ✅ Escalates them to high priority status
- ✅ Notifies support staff in a dedicated channel
- ✅ Sorts them to the top of the dashboard
- ✅ Gives you full control over thresholds and notifications

**Next Steps:**
1. Run `/set_support_role` to configure which role gets pinged
2. Test the system with `/list_high_priority_posts`
3. Adjust the inactivity threshold if needed with `/set_post_inactivity_time`

