# 📋 High Priority Notification Format Example

## What You'll See in Channel 1436918674069000212

When the bot detects high priority posts, it sends a message that looks like this:

---

### Example with Support Role:

```
@Support Staff

High Priority Posts:

1. [Macro keeps crashing on startup](https://discord.com/channels/1265864190883532872/1407123456789012345)
2. [License key not activating](https://discord.com/channels/1265864190883532872/1407234567890123456)
3. [Bot not responding to commands](https://discord.com/channels/1265864190883532872/1407345678901234567)
```

### Example without Support Role:

```
High Priority Posts:

1. [Macro keeps crashing on startup](https://discord.com/channels/1265864190883532872/1407123456789012345)
2. [License key not activating](https://discord.com/channels/1265864190883532872/1407234567890123456)
3. [Bot not responding to commands](https://discord.com/channels/1265864190883532872/1407345678901234567)
```

---

## 📊 Features

### Clickable Links
Every post title is a **clickable link** that takes you directly to the thread:
- Click on `[Macro keeps crashing on startup]` → Opens that thread
- Click on `[License key not activating]` → Opens that thread
- And so on...

### Numbered List
Posts are numbered for easy reference:
- Support can say "I'll handle #2"
- Easy to track which posts are being worked on

### Role Mention
If you've configured a support role with `/set_support_role`:
- The role gets mentioned at the top
- Everyone with that role gets a notification
- They can immediately see what needs attention

### Automatic Updates
Every time the background task runs and finds new high priority posts:
- A new summary is sent
- Shows ALL current high priority posts
- Up to 10 posts (with count if more)

---

## 🎯 When Notifications Are Sent

### Automatic (Background Task):
- Runs every X hours (configure with `/set_ping_high_priority_interval`)
- Default: Every 1 hour
- Only sends if new posts were escalated in that check

### Manual (On Demand):
```
/ping_high_priority_now
```
- Sends summary immediately
- Shows all current high priority posts
- Useful for testing or immediate alerts

---

## 🔧 How to Configure

### Set the Support Role:
```
/set_support_role role:@Support Staff
```
This role gets pinged in the notification.

### Set the Channel (Already Done!):
```
/set_high_priority_channel_id channel_id:1436918674069000212
```
Current channel is already set to this ID.

### Test the Notification:
```
/ping_high_priority_now
```
Sends the summary immediately to test the format.

---

## 💡 What Makes This Format Great

### For Support Staff:
✅ See ALL high priority posts at once  
✅ Click directly to any thread  
✅ Easy to divide work among team  
✅ Clean, scannable format  
✅ No spam from individual notifications  

### For Users:
✅ Still get notified in their thread  
✅ Know support has been alerted  
✅ Can see the "🚨 Support Team Notified" message  

### For Admins:
✅ One notification per check cycle (not per post)  
✅ Easy to adjust frequency  
✅ Manual trigger available  
✅ Fully configurable  

---

## 📱 Discord Formatting

The message uses Discord's native markdown:
- `@Support Staff` - Mentions the role
- `[Title](URL)` - Creates clickable links
- Numbered lists work naturally
- Clean and professional appearance

---

## 🧪 Test It Now!

1. **Restart your bot** to load the new code
2. **Set your support role:**
   ```
   /set_support_role role:@Support Staff
   ```
3. **Send a test notification:**
   ```
   /ping_high_priority_now
   ```
4. **Check channel 1436918674069000212** to see the format!

If there are no high priority posts, it won't send anything (which is good!).

---

## 🎉 You're All Set!

Your high priority notification system now:
- ✅ Uses channel `1436918674069000212`
- ✅ Sends clean summary lists
- ✅ Pings your support staff
- ✅ Shows all high priority posts at once
- ✅ Has manual trigger available
- ✅ Fully configurable intervals

**The format you requested is now live!** 🚀

