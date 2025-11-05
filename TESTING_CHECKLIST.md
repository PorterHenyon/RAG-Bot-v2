# 🧪 Testing Checklist - New Features

## ✅ Before You Start

1. **Stop your bot** if it's running (Ctrl+C)
2. **Restart the bot:** `python bot.py`
3. **Wait for commands to sync** (you'll see "✓ Slash commands synced" message)

---

## Test 1: New `/set_post_inactivity_time` Command

### Steps:
```
1. In Discord, type: /set_post_inactivity_time hours: 6
2. Bot should respond: "✅ Post inactivity threshold updated to 6 hours!"
```

### Verify:
- ✅ Command appears in Discord (type `/` and see it in the list)
- ✅ Bot responds with success message
- ✅ Check `bot_settings.json` file → should show `"post_inactivity_hours": 6`
- ✅ Run `/status` → should show "Post Inactivity: 6h" in Timers section

### Dashboard Check:
- ✅ Open dashboard → Slash Commands view
- ✅ Should see `set_post_inactivity_time` in the list
- ✅ Description should mention "1-168 hours"

---

## Test 2: `/mark_as_solve_no_review` Doesn't Create RAG

### Setup:
```
1. Create a test forum post in your support channel
2. Bot will auto-respond
3. Reply as the user: "Thanks! This helped!"
4. Wait 5 seconds (let satisfaction timer start)
5. QUICKLY run: /mark_as_solve_no_review
```

### Expected Result:
- ✅ Bot says: "✅ Thread marked as Solved and locked!"
- ✅ Bot says: "📋 No RAG entry created (as requested)."
- ✅ Thread is locked and archived
- ✅ Console logs show: "🚫 Thread XXXXX marked as no_review - will not create RAG entry"
- ✅ Console logs show: "⏰ Cancelled satisfaction timer for no_review thread XXXXX"

### Dashboard Check (CRITICAL):
```
1. Open dashboard
2. Go to RAG Management
3. Check "Pending Review" section
4. Should be EMPTY (no entry created) ✅
```

### If pending entry appears:
- ❌ Bug still exists - the timer fired before command was used
- Try again but use `/mark_as_solve_no_review` FASTER (within 1-2 seconds of user reply)

---

## Test 3: `/mark_as_solve` DOES Create RAG

### Setup:
```
1. Create another test forum post
2. Bot auto-responds
3. Reply as user: "Perfect, thank you!"
4. Wait 20 seconds (let satisfaction analysis complete)
5. Run: /mark_as_solve
```

### Expected Result:
- ✅ Bot says: "✅ Thread marked as solved and RAG entry submitted for review!"
- ✅ Shows the RAG entry title and ID
- ✅ Thread is locked and archived

### Dashboard Check:
```
1. Open dashboard → RAG Management
2. Should see 1 pending entry in "Pending Review" section ✅
3. Entry should have:
   - Yellow border
   - "Pending Review" badge
   - Source: "Staff (YourName) via /mark_as_solve"
   - Approve and Reject buttons
4. Click "Reject" → Entry disappears ✅
5. Check that it's truly gone from the list
```

---

## Test 4: Auto-Satisfaction Still Works (When Not Using no_review)

### Setup:
```
1. Create a forum post
2. Bot responds
3. User says: "thanks this worked!"
4. DON'T use any commands
5. Wait 15 seconds (default satisfaction delay)
```

### Expected Result:
- ✅ Bot analyzes satisfaction automatically
- ✅ If satisfied, bot creates pending RAG entry
- ✅ Dashboard shows entry in "Pending Review"
- ✅ Thread marked as "Solved" automatically

---

## Test 5: Post Inactivity Escalation

### Setup (requires time):
```
1. Set low threshold: /set_post_inactivity_time hours: 1
2. Create a test forum post
3. DON'T solve it
4. Wait 1 hour
```

### Expected Result:
- ✅ Background task runs (every hour)
- ✅ Console logs: "🔍 Checking for old unsolved posts (>1 hours)..."
- ✅ Console logs: "⚠ Found old post: 'Your Test Post' (1.2 hours old, threshold: 1h)"
- ✅ Post status changes to "High Priority"
- ✅ Dashboard shows post as "High Priority"

---

## 🐛 Troubleshooting

### Commands don't appear in Discord:
```bash
# Re-invite bot with applications.commands scope
# OR
# Wait a few minutes for Discord to sync
# OR
# Restart bot: python bot.py
```

### `/mark_as_solve_no_review` still creates RAG:
```bash
# Check console for this message:
# "🚫 Thread XXXXX marked as no_review - skipping auto-RAG creation"
# If you don't see it, the timer fired BEFORE you ran the command
# Solution: Run command faster (within 1-2 seconds of user reply)
```

### Dashboard doesn't show new command:
```bash
# 1. Check if dashboard is using latest code
# 2. Refresh browser (Ctrl+Shift+R)
# 3. Check Slash Commands view (not RAG Management)
```

### Post inactivity not working:
```bash
# 1. Check bot_settings.json has "post_inactivity_hours"
# 2. Background task runs every HOUR (not immediately)
# 3. Set threshold low (1-2 hours) for testing
# 4. Posts must be "Unsolved", "AI Response", or "Human Support" status
```

---

## ✅ Success Criteria

All these should be true:

- ✅ `/set_post_inactivity_time` command exists and works
- ✅ `/mark_as_solve_no_review` truly doesn't create RAG entries
- ✅ `/mark_as_solve` still creates pending RAG entries
- ✅ Auto-satisfaction creates RAG when using neither command
- ✅ Dashboard shows new command in Slash Commands view
- ✅ `/status` shows post inactivity setting
- ✅ bot_settings.json has `post_inactivity_hours` field

---

## 📸 What to Look For

### Console Output (Good):
```
✓ Loaded bot settings: satisfaction_delay=15s, temperature=1.0, max_tokens=2048, post_inactivity_hours=12h
✓ Slash commands synced to guild 1234567890 (13 commands).  ← Should be 13 now!
🚫 Thread 1234567890 marked as no_review - will not create RAG entry
⏰ Cancelled satisfaction timer for no_review thread 1234567890
🔍 Checking for old unsolved posts (>12 hours)...
```

### Dashboard (Good):
```
Slash Commands View:
- Shows 13 commands total (was 12)
- set_post_inactivity_time listed
- Description mentions "1-168 hours"

RAG Management:
- When using /mark_as_solve_no_review → NO pending entries
- When using /mark_as_solve → YES pending entry appears
- Reject button works (entry disappears)
```

---

**All tests passing = You're ready to use the new features!** 🎉

