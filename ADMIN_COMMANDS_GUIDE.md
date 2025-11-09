# 🎮 Admin Commands Guide

All commands require **Administrator** permissions in Discord.

---

## 📋 **All Available Commands**

| Command | Purpose | Category |
|---------|---------|----------|
| `/status` | Check bot status | 🔍 Debugging |
| `/check_rag_entries` | List RAG entries | 🔍 Debugging |
| `/check_auto_entries` | List auto-responses | 🔍 Debugging |
| `/ask` | Query knowledge base | 🧪 Testing |
| `/reload` | Reload data from API | 🔄 Maintenance |
| `/stop` | Stop the bot | 🔄 Maintenance |
| `/mark_as_solve` | Mark thread solved | 📚 Knowledge |
| `/set_forums_id` | Set forum channel | ⚙️ Configuration |
| `/set_satisfaction_delay` | Set timer delay | ⚙️ Configuration |
| `/set_temperature` | Set AI creativity | ⚙️ Configuration |
| `/set_max_tokens` | Set response length | ⚙️ Configuration |
| `/set_post_inactivity_time` | Set hours before escalation | 🚨 High Priority |
| `/set_ping_high_priority_interval` | Set check interval | 🚨 High Priority |
| `/set_support_role` | Set support role to ping | 🚨 High Priority |
| `/set_support_notification_channel` | Set notification channel | 🚨 High Priority |
| `/set_high_priority_channel_id` | Set notification channel by ID | 🚨 High Priority |
| `/list_high_priority_posts` | List all high priority posts | 🚨 High Priority |
| `/ping_high_priority_now` | Manually send high priority summary | 🚨 High Priority |

---

## 🔍 **Debugging Commands**

### `/status`
**Purpose:** See everything about the bot at a glance

**Usage:**
```
/status
```

**Shows:**
```
🤖 Revolution Macro Bot Status

📊 Data Loaded
RAG Entries: 8
Auto-Responses: 3

⚙️ AI Settings
Temperature: 1.0
Max Tokens: 2048

⏱️ Timers
Satisfaction Delay: 15s
Active Timers: 2

📺 Forum Channel
support-forum (ID: 1234567890)

📡 API Connection
✅ Connected
https://your-app.vercel.app/api/data

🧠 System Prompt
Using custom prompt (1245 characters)
```

**Perfect for:** Quick overview of bot health

---

### `/check_rag_entries`
**Purpose:** List all knowledge base entries loaded

**Usage:**
```
/check_rag_entries
```

**Shows:**
```
📚 Knowledge Base Entries
Currently loaded: 8 entries

1. Character Resets Instead of Converting Honey
   Keywords: honey, pollen, convert, reset, resets
   ID: RAG-001

2. Error: "Failed to Initialize" on Startup
   Keywords: initialize, error, update, fix
   ID: RAG-002

[... shows first 10 entries ...]
```

**Perfect for:** 
- Verifying entries loaded from dashboard
- Checking if new entries synced
- Debugging why bot isn't matching questions

---

### `/check_auto_entries`
**Purpose:** List all auto-responses loaded

**Usage:**
```
/check_auto_entries
```

**Shows:**
```
⚡ Auto-Responses
Currently loaded: 3 responses

1. Password Reset
   Triggers: password, reset, forgot, lost account
   Response: You can reset your password by...
   ID: AR-001

2. Check Server Status
   Triggers: down, offline, server status
   Response: You can check our server status...
   ID: AR-002
```

**Perfect for:**
- Verifying auto-responses loaded
- Checking trigger keywords
- Debugging why auto-response didn't fire

---

## 🧪 **Testing Commands**

### `/ask`
**Purpose:** Test the bot's knowledge base without creating a forum post

**Usage:**
```
/ask question: How do I fix honey conversion issues?
```

**Shows:**
- ✅ AI response with RAG matches (if found)
- 💬 Auto-response (if keyword matches)
- ⚠️ No match found (if nothing in knowledge base)

**Perfect for:**
- Testing new RAG entries
- Verifying bot understands questions
- Quick answers for staff

---

## ⚙️ **Configuration Commands**

### `/set_forums_id`
**Purpose:** Change which Discord channel the bot monitors

**Usage:**
```
/set_forums_id channel_id: 1234567890
```

**How to get channel ID:**
1. Right-click forum channel in Discord
2. Click "Copy Channel ID"
3. Use in command

**Saves to:** `bot_settings.json`

**Perfect for:**
- Switching to different support forum
- Testing on test channel
- No need to edit `.env` file

---

### `/set_satisfaction_delay`
**Purpose:** Change how long bot waits before analyzing user satisfaction

**Usage:**
```
/set_satisfaction_delay seconds: 10
```

**Range:** 5-300 seconds  
**Default:** 15 seconds

**Examples:**
- `seconds: 5` - Quick analysis (good for testing)
- `seconds: 15` - Default (balanced)
- `seconds: 30` - Patient (gives users more time)

**Saves to:** `bot_settings.json`

**Perfect for:**
- Testing satisfaction detection quickly
- Adjusting for your users' typing speed
- Fine-tuning user experience

---

### `/set_temperature`
**Purpose:** Control AI response creativity/consistency

**Usage:**
```
/set_temperature temperature: 0.7
```

**Range:** 0.0-2.0  
**Default:** 1.0

**Examples:**
- `temperature: 0.3` - Very consistent, same answers
- `temperature: 1.0` - Balanced (default)
- `temperature: 1.5` - More creative, varied answers

**Effect:**
- **Lower (0.0-0.7):** More deterministic, focused, repetitive
- **Medium (0.7-1.3):** Balanced creativity
- **Higher (1.3-2.0):** More creative, varied, unpredictable

**Saves to:** `bot_settings.json`

**Perfect for:**
- Making bot more consistent
- Adding variety to responses
- A/B testing response styles

---

### `/set_max_tokens`
**Purpose:** Control maximum length of AI responses

**Usage:**
```
/set_max_tokens max_tokens: 1024
```

**Range:** 100-8192  
**Default:** 2048

**Approximate Word Count:**
- `max_tokens: 512` ≈ 128 words (very short)
- `max_tokens: 1024` ≈ 256 words (short)
- `max_tokens: 2048` ≈ 512 words (medium, default)
- `max_tokens: 4096` ≈ 1024 words (long)

**Saves to:** `bot_settings.json`

**Perfect for:**
- Keeping responses concise
- Allowing detailed explanations
- Controlling response length

---

## 🔄 **Maintenance Commands**

### `/reload`
**Purpose:** Refresh data from dashboard without restarting bot

**Usage:**
```
/reload
```

**Reloads:**
- ✅ RAG entries
- ✅ Auto-responses
- ✅ System prompt
- ✅ Slash commands
- ✅ Downloads to localrag/

**Perfect for:**
- After adding entries in dashboard
- After editing system prompt
- Testing changes immediately

---

### `/mark_as_solve`
**Purpose:** Manually mark thread as solved and create RAG entry

**Usage:**
```
/mark_as_solve
```
(Must be used inside a forum thread)

**Does:**
1. ✅ Analyzes entire conversation
2. ✅ Creates RAG entry with AI
3. ✅ Saves to knowledge base
4. ✅ Marks thread as "Solved" in dashboard
5. ✅ Locks and archives thread

**Perfect for:**
- Converting successful conversations to knowledge
- Building knowledge base manually
- Quality control (vs automatic)

---

### `/stop`
**Purpose:** Gracefully shut down the bot

**Usage:**
```
/stop
```

**Does:**
- Closes bot connection
- Saves all timers
- Clean shutdown

**Perfect for:** Maintenance, updates, restarts

---

## 💾 **Settings Storage**

All configuration commands save to `bot_settings.json`:

```json
{
  "support_forum_channel_id": 1234567890,
  "satisfaction_delay": 15,
  "ai_temperature": 1.0,
  "ai_max_tokens": 2048,
  "last_updated": "2024-11-03T18:30:00.000Z"
}
```

**Benefits:**
- ✅ Persists across bot restarts
- ✅ Not committed to git (in `.gitignore`)
- ✅ Can be edited manually if needed
- ✅ Changes apply immediately

---

## 🧪 **Testing Workflow**

### Test 1: Verify Bot is Working
```
1. Run: /status
2. Check: RAG entries > 0
3. Check: Auto-responses > 0
4. Check: API connected
```

### Test 2: Check Data Loaded
```
1. Run: /check_rag_entries
2. Verify: Sees your entries from dashboard
3. Run: /check_auto_entries
4. Verify: Sees your auto-responses
```

### Test 3: Test Knowledge Base
```
1. Run: /ask question: How do I fix honey conversion?
2. Verify: Gets RAG-based answer
3. Check: References correct documentation
```

### Test 4: Adjust Timing for Testing
```
1. Run: /set_satisfaction_delay seconds: 5
2. Create test forum post
3. Reply with "thanks"
4. Wait only 5 seconds
5. Verify: Bot marks as solved quickly
```

### Test 5: Fine-Tune AI Responses
```
1. Run: /set_temperature temperature: 0.5
2. Test a question
3. Note response style
4. Run: /set_temperature temperature: 1.5
5. Test same question
6. Compare responses (should be more varied)
```

---

## 📊 **Command Summary Table**

| Command | Parameters | Saves to File | Effect |
|---------|-----------|---------------|--------|
| `/status` | None | ❌ | Shows info |
| `/check_rag_entries` | None | ❌ | Lists entries |
| `/check_auto_entries` | None | ❌ | Lists responses |
| `/ask` | question | ❌ | Tests KB |
| `/reload` | None | ❌ | Syncs data |
| `/stop` | None | ❌ | Shuts down |
| `/mark_as_solve` | None | ❌ | Creates RAG |
| `/set_forums_id` | channel_id | ✅ | Changes forum |
| `/set_satisfaction_delay` | seconds (5-300) | ✅ | Changes timer |
| `/set_temperature` | temperature (0-2) | ✅ | Changes AI |
| `/set_max_tokens` | max_tokens (100-8192) | ✅ | Changes length |

---

## 🚨 **High Priority Commands**

### `/set_post_inactivity_time`
**Purpose:** Set how long a post must be open before it's escalated to High Priority

**Usage:**
```
/set_post_inactivity_time hours:24
```

**Parameters:**
- `hours`: Number of hours (1-168)

**Example:**
```
/set_post_inactivity_time hours:12
✅ Post inactivity threshold updated to 12 hours!
Posts older than 12 hours will be escalated to High Priority.
```

---

### `/set_ping_high_priority_interval`
**Purpose:** Set how often the bot checks for old posts that need escalation

**Usage:**
```
/set_ping_high_priority_interval hours:0.5
```

**Parameters:**
- `hours`: Check interval in hours (0.25-24)
  - `0.25` = 15 minutes
  - `0.5` = 30 minutes
  - `1.0` = 1 hour
  - `2.0` = 2 hours

**Example:**
```
/set_ping_high_priority_interval hours:0.5
✅ High priority check interval updated to 30 minutes!

📊 Current Settings:
• Check Interval: Every 30 minutes
• Escalation Threshold: 12 hours of inactivity
• Notification Channel: #high-priority-alerts

💡 Tip: Shorter intervals mean faster response to old posts, but check your server load!
```

**Why This Matters:**
- Lower values = Faster detection of old posts
- Higher values = Less frequent checks (better for server performance)
- Default is 1 hour (good balance for most servers)

---

### `/set_support_role`
**Purpose:** Set which role gets pinged when posts are escalated to High Priority

**Usage:**
```
/set_support_role role:@Support
```

**Parameters:**
- `role`: The Discord role to mention

**Example:**
```
/set_support_role role:@Support Team
✅ Support role set to @Support Team!

This role will be pinged in #high-priority-alerts
whenever a post is escalated to High Priority.
```

---

### `/set_support_notification_channel`
**Purpose:** Set which channel receives high priority notifications

**Usage:**
```
/set_support_notification_channel channel:#alerts
```

**Parameters:**
- `channel`: The Discord channel for notifications

**Example:**
```
/set_support_notification_channel channel:#high-priority-alerts
✅ Support notification channel set to #high-priority-alerts!

Current Support Role: @Support Team
High priority posts will be announced in #high-priority-alerts.

Use /set_support_role to configure which role gets pinged.
```

---

### `/list_high_priority_posts`
**Purpose:** List all posts currently marked as High Priority

**Usage:**
```
/list_high_priority_posts
```

**Shows:**
```
🚨 High Priority Posts (3)
These posts need immediate attention from the support team:

1. Macro not working after update
   User: JohnDoe#1234
   [View Post](link)

2. License activation failed
   User: JaneSmith#5678
   [View Post](link)

3. Game crashes on startup
   User: BobJones#9012
   [View Post](link)
```

---

### `/set_high_priority_channel_id`
**Purpose:** Set the high priority notification channel using a channel ID

**Usage:**
```
/set_high_priority_channel_id channel_id:1436918674069000212
```

**Parameters:**
- `channel_id`: The Discord channel ID (as a number string)

**Example:**
```
/set_high_priority_channel_id channel_id:1436918674069000212
✅ Support notification channel set to #high-priority-alerts!

Channel ID: 1436918674069000212
Current Support Role: @Support Staff

High priority posts will be announced in #high-priority-alerts.
Use /set_support_role to configure which role gets pinged.
```

**Why Use This Instead of `/set_support_notification_channel`?**
- Useful when you can't select the channel in the dropdown
- Works for any channel the bot can access
- Easier to copy/paste channel IDs

---

### `/ping_high_priority_now`
**Purpose:** Manually send a summary of all high priority posts to the notification channel

**Usage:**
```
/ping_high_priority_now
```

**What It Sends:**
```
@Support Staff

High Priority Posts:

1. [Macro not starting after update](https://discord.com/channels/.../thread1)
2. [License key not working](https://discord.com/channels/.../thread2)
3. [Game crashes on launch](https://discord.com/channels/.../thread3)
```

**When to Use:**
- Check on high priority posts immediately (don't wait for auto-check)
- Alert support team manually
- After making configuration changes
- For testing the notification system

**Example:**
```
/ping_high_priority_now
✅ High priority summary sent to #high-priority-alerts!

Check the channel for the list of all current high priority posts.
```

---

## 🎯 **Recommended Settings**

### For Production:
```
/set_satisfaction_delay seconds: 15
/set_temperature temperature: 1.0
/set_max_tokens max_tokens: 2048
```

### For Testing:
```
/set_satisfaction_delay seconds: 5  ← Quick testing
/set_temperature temperature: 0.7   ← Consistent responses
/set_max_tokens max_tokens: 1024    ← Shorter for speed
```

### For Detailed Support:
```
/set_satisfaction_delay seconds: 30  ← Patient
/set_temperature temperature: 0.8   ← Focused
/set_max_tokens max_tokens: 4096    ← Detailed responses
```

---

## ✅ **What's Been Added:**

✅ **16+ admin commands total**  
✅ **All require admin permissions**  
✅ **Settings persist in bot_settings.json**  
✅ **No code editing needed**  
✅ **Perfect for testing and tuning**  
✅ **All commands in dashboard documentation**  
✅ **High priority notification system**  
✅ **Configurable check intervals**  

---

**Everything is ready to use!** 🎉

Just restart the bot and type `/` in Discord to see all commands!

