# Add New Forum Channel to Bot

## Quick Instructions

To make your bot monitor the new forum channel `1435245345448656916`:

### Update Your `.env` File:

Open your `.env` file and change:

```env
SUPPORT_FORUM_CHANNEL_ID=old_channel_id_here
```

To:

```env
SUPPORT_FORUM_CHANNEL_ID=1435245345448656916
```

### Then Restart the Bot:

```bash
# Stop the bot (Ctrl+C)
python bot.py
```

The bot will now monitor the new forum channel!

---

## Verify It's Working:

When the bot starts, you should see:
```
✓ Monitoring channel: YourChannelName (ID: 1435245345448656916)
```

That's it! The bot will now respond to posts in this forum channel.

