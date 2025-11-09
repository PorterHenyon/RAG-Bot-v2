# ⚡ Quick Setup: High Priority Alerts

## ✅ What's Already Done

I've implemented a complete high priority notification system for your bot!

### Changes Made:

1. **Dashboard Now Prioritizes High Priority Posts**
   - High priority posts always appear at the top
   - Works across all filters and searches
   - Located in: `components/views/ForumPostsView.tsx`

2. **Bot Sends Notifications to Support Channel**
   - Channel ID: `1405246916760961125` (already configured!)
   - Sends rich embed notifications with post details
   - Includes clickable links to posts
   - Located in: `bot.py` (added `notify_support_channel()` function)

3. **New Admin Commands Added**
   - `/set_support_role` - Configure which role to ping
   - `/set_support_notification_channel` - Change notification channel
   - `/list_high_priority_posts` - View all high priority posts

---

## 🚀 Quick Setup (2 minutes)

### Step 1: Restart Your Bot
```bash
# Stop the bot if running (Ctrl+C)
python bot.py
```

The bot will load the new settings automatically.

### Step 2: Set Your Support Role (Optional but Recommended)
In Discord, run:
```
/set_support_role role:@Support
```
Replace `@Support` with whatever role should be pinged for urgent issues.

### Step 3: Test It!
```
/list_high_priority_posts
```
This will show you if there are any current high priority posts.

---

## 📋 What Happens Now

### When a Post Becomes High Priority:

1. **In the Thread:**
   ```
   🚨 Support Team Notified
   This post has been open for 15 hours. Our support team has been pinged and will help you soon.
   ```

2. **In Channel 1436918674069000212:**
   ```
   @Support Staff

   High Priority Posts:

   1. [Post Title 1](link to post)
   2. [Post Title 2](link to post)
   3. [Post Title 3](link to post)
   ```

3. **In Dashboard:**
   - Post appears at the very top of the list
   - Marked with "High Priority" badge
   - Remains at top regardless of filters

---

## ⚙️ Current Settings

```
Support Notification Channel: 1436918674069000212 ✅
Support Role: Not set yet (run /set_support_role)
Auto-Escalation Threshold: 12 hours
Background Check: Every 1 hour
Notification Format: Summary list of all high priority posts
```

---

## 🎯 How to Change Settings

### Change Which Channel Gets Notifications
```
/set_support_notification_channel channel:#alerts
```

### Change Which Role Gets Pinged
```
/set_support_role role:@Your-Support-Team
```

### Change How Long Before Auto-Escalation
```
/set_post_inactivity_time hours:24
```
Default is 12 hours. You can set it anywhere from 1 to 168 hours.

### Change How Often Bot Checks for High Priority Posts
```
/set_ping_high_priority_interval hours:0.5
```
Default is 1 hour. You can set it anywhere from 0.25 hours (15 minutes) to 24 hours. Lower values mean faster detection of old posts but more frequent checks.

---

## 🧪 Testing the System

### Method 1: Wait for Auto-Escalation
- Wait for a post to be open longer than 12 hours
- The background task runs every hour and will auto-escalate it

### Method 2: Manual Testing
- Go to your dashboard
- Open a forum post
- Change its status to "High Priority"
- Check channel `1405246916760961125` for the notification

### Method 3: Check Current Status
```
/list_high_priority_posts
```
Shows all posts currently marked as high priority.

---

## 📖 Full Documentation

See `HIGH_PRIORITY_NOTIFICATIONS.md` for:
- Complete technical details
- Troubleshooting guide
- Best practices
- Data flow diagrams

---

## ✨ You're All Set!

The system is now active and monitoring your forum posts. Here's what will happen automatically:

1. ⏰ Every hour, the bot checks for old posts
2. 🚨 Posts older than 12 hours get escalated to High Priority
3. 📢 Support gets notified in channel `1405246916760961125`
4. 👥 If configured, your support role gets pinged
5. 📊 Dashboard shows these posts at the top

**Recommended Next Step:** 
Run `/set_support_role role:@YourSupportTeam` to enable role pings!

