# Auto-run setup (no Railway)

Everything runs automatically after one-time setup below.

| What | How | When |
|------|-----|------|
| **Daily DM to Liam** | GitHub Actions | Every day at 9:00 AM Mountain Time |
| **Slash commands** (`/daily_summary`, `/scan`) | Bot on your PC | Starts when you log in to Windows |

## One-time setup (do this once after push)

### 1. GitHub secrets (daily auto-DM — works even when your PC is off)

GitHub → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Required |
|--------|----------|
| `DISCORD_BOT_TOKEN` | Yes |
| `SUPPORT_FORUM_CHANNEL_ID` | Yes |
| `DISCORD_GUILD_ID` | Yes |
| `LIAM_USER_ID` | No (defaults to Liam) |
| `STAFF_ROLE_ID` | No |

After secrets are saved, the workflow runs every day automatically. Test it: **Actions → Daily Ticket Summary → Run workflow**.

### 2. Windows auto-start (slash commands)

Run once in PowerShell from the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File install_autostart.ps1
```

The bot starts in the background when you log in. Logs: `logs/bot.log`.

Your `.env` file must exist locally (same values as GitHub secrets).

## Commands

- `/daily_summary` — send summary to Liam now (admin, bot must be online)
- `/scan` — preview ticket counts without DM (admin)