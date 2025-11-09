# ✅ New Command Added: `/set_ping_high_priority_interval`

## What It Does

This command allows you to configure **how often** the bot checks for old unsolved posts that need to be escalated to High Priority status.

---

## 🎯 Usage

```
/set_ping_high_priority_interval hours:0.5
```

**Parameters:**
- `hours` (float): Check interval in hours
  - Minimum: `0.25` (15 minutes)
  - Maximum: `24` (24 hours)
  - Default: `1.0` (1 hour)

---

## 📊 Examples

### Check Every 15 Minutes (Very Fast)
```
/set_ping_high_priority_interval hours:0.25
```
✅ Good for: High-traffic support servers that need immediate escalation

### Check Every 30 Minutes (Fast)
```
/set_ping_high_priority_interval hours:0.5
```
✅ Good for: Active servers with quick response times

### Check Every Hour (Balanced - Default)
```
/set_ping_high_priority_interval hours:1.0
```
✅ Good for: Most servers (balanced between speed and performance)

### Check Every 2 Hours (Slower)
```
/set_ping_high_priority_interval hours:2
```
✅ Good for: Smaller servers or when resources are limited

---

## 🔄 How It Works

1. **Background Task**: The bot runs a background task that checks for old posts
2. **Check Interval**: This command sets how often that task runs
3. **Inactivity Threshold**: Posts older than the threshold (set with `/set_post_inactivity_time`) get escalated
4. **Notification**: When a post is escalated, support gets notified in the configured channel

### Example Flow:
```
Setting: Check Interval = 30 minutes
Setting: Inactivity Threshold = 12 hours

Timeline:
- 00:00 - User creates post
- 12:00 - Post is now 12 hours old
- 12:30 - Bot's next check (30min interval) detects it
- 12:30 - Post escalated to High Priority
- 12:30 - Support team gets pinged in notification channel
```

---

## ⚙️ Related Commands

### Set How Long Before Escalation
```
/set_post_inactivity_time hours:12
```
Sets how many hours a post must be open before it's escalated.

### Set Support Role
```
/set_support_role role:@Support
```
Sets which role gets pinged when posts are escalated.

### Set Notification Channel
```
/set_support_notification_channel channel:#alerts
```
Sets where high priority notifications are sent.

### List High Priority Posts
```
/list_high_priority_posts
```
Shows all posts currently marked as High Priority.

---

## 🎯 Recommended Intervals

| Server Size | Posts/Day | Recommended Interval | Reasoning |
|-------------|-----------|---------------------|-----------|
| Small (< 10 posts/day) | < 10 | 2-4 hours | Lower volume, less urgent |
| Medium (10-50 posts/day) | 10-50 | 1 hour (default) | Balanced approach |
| Large (50+ posts/day) | 50+ | 15-30 minutes | High volume needs fast response |

---

## ⚡ Performance Considerations

### Lower Intervals (15-30 min)
**Pros:**
- ✅ Faster detection of old posts
- ✅ Quicker support response
- ✅ Better for high-traffic servers

**Cons:**
- ⚠️ More frequent API calls
- ⚠️ Slightly higher resource usage
- ⚠️ More frequent notifications

### Higher Intervals (2-24 hours)
**Pros:**
- ✅ Less frequent checks
- ✅ Lower resource usage
- ✅ Fewer notifications

**Cons:**
- ⚠️ Slower detection
- ⚠️ Longer wait for escalation
- ⚠️ Support may miss urgent issues

---

## 🛠️ Configuration

The setting is stored in `bot_settings.json` and persists across bot restarts:

```json
{
  "high_priority_check_interval_hours": 1.0,
  "post_inactivity_hours": 12,
  "support_notification_channel_id": 1405246916760961125,
  "support_role_id": null
}
```

---

## 📝 What Was Updated

### Code Changes:
1. ✅ Added `high_priority_check_interval_hours` to `BOT_SETTINGS`
2. ✅ Created `/set_ping_high_priority_interval` command in `bot.py`
3. ✅ Command dynamically changes the `check_old_posts` task interval
4. ✅ Updated log messages to show current interval

### Documentation Updated:
1. ✅ `HIGH_PRIORITY_NOTIFICATIONS.md` - Added command documentation
2. ✅ `SETUP_HIGH_PRIORITY_ALERTS.md` - Added setup instructions
3. ✅ `ADMIN_COMMANDS_GUIDE.md` - Added to command list and detailed guide
4. ✅ `NEW_COMMAND_SET_PING_INTERVAL.md` - This file!

---

## 🚀 Quick Start

1. **Restart your bot** to load the new command
2. **Set your preferred interval:**
   ```
   /set_ping_high_priority_interval hours:1
   ```
3. **Verify the setting:**
   ```
   /status
   ```
   Look for "Post Inactivity" in the output
4. **Test it by listing current high priority posts:**
   ```
   /list_high_priority_posts
   ```

---

## ✅ Complete Setup Example

Here's a complete setup for a typical support server:

```bash
# Step 1: Set support role
/set_support_role role:@Support Team

# Step 2: Set notification channel
/set_support_notification_channel channel:#high-priority-alerts

# Step 3: Set how long before escalation (12 hours)
/set_post_inactivity_time hours:12

# Step 4: Set how often to check (30 minutes)
/set_ping_high_priority_interval hours:0.5

# Step 5: Verify settings
/status
```

**Result:**
- Bot checks every 30 minutes for posts older than 12 hours
- When found, posts are escalated to High Priority
- @Support Team gets pinged in #high-priority-alerts
- High priority posts appear at the top of the dashboard

---

## 🎉 Summary

You now have full control over how fast your support team responds to old posts!

- ⚡ **Faster intervals** = Quicker support
- 🎯 **Default (1 hour)** = Good balance
- 💤 **Slower intervals** = Less resource usage

Choose what works best for your server! 🚀

