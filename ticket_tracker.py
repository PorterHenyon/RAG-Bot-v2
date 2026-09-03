"""
Support forum ticket tracker — monitors forum posts and sends Liam detailed daily DMs.

No auto-responding, no RAG, no dashboard. Just reads tickets and reports.
"""

import asyncio
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SUPPORT_FORUM_CHANNEL_ID = int(os.getenv("SUPPORT_FORUM_CHANNEL_ID", "0"))
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
LIAM_USER_ID = int(os.getenv("LIAM_USER_ID", "910980823132561428"))
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "1422106035337826315"))
STALE_HOURS = int(os.getenv("STALE_HOURS", "12"))
NEW_HOURS = int(os.getenv("NEW_HOURS", "24"))
SOLVED_TAG_ID = os.getenv("SOLVED_TAG_ID")
UNSOLVED_TAG_ID = os.getenv("UNSOLVED_TAG_ID")

LOG_EXTENSIONS = {".log", ".txt", ".dmp", ".crash"}
LOG_NAME_PATTERN = re.compile(r"log|crash|dump|error|debug", re.IGNORECASE)


@dataclass
class Ticket:
    thread_id: int
    title: str
    url: str
    created_at: datetime
    age: timedelta
    owner_name: str
    preview: str
    has_logs: bool = False
    log_files: list[str] = field(default_factory=list)
    has_staff_reply: bool = False
    staff_replied_by: list[str] = field(default_factory=list)
    is_resolved: bool = False
    tags: list[str] = field(default_factory=list)
    message_count: int = 0

    @property
    def age_label(self) -> str:
        total_hours = int(self.age.total_seconds() // 3600)
        if total_hours < 1:
            mins = int(self.age.total_seconds() // 60)
            return f"{mins}m"
        if total_hours < 48:
            return f"{total_hours}h"
        days = total_hours // 24
        rem = total_hours % 24
        return f"{days}d {rem}h" if rem else f"{days}d"

    @property
    def is_new(self) -> bool:
        return self.age <= timedelta(hours=NEW_HOURS)

    @property
    def is_stale(self) -> bool:
        return not self.is_resolved and self.age >= timedelta(hours=STALE_HOURS)

    @property
    def is_unseen(self) -> bool:
        return not self.has_staff_reply and not self.is_resolved


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_log_file(filename: str) -> bool:
    lower = filename.lower()
    ext = os.path.splitext(lower)[1]
    if ext in LOG_EXTENSIONS and ("log" in lower or ext == ".log" or ext == ".dmp"):
        return True
    if ext == ".txt" and LOG_NAME_PATTERN.search(lower):
        return True
    if ext in {".zip", ".rar", ".7z"} and LOG_NAME_PATTERN.search(lower):
        return True
    return ext == ".log" or (ext == ".txt" and "log" in lower)


def is_staff(member: discord.Member) -> bool:
    if member.bot:
        return False
    if member.guild_permissions.administrator:
        return True
    if member.id == LIAM_USER_ID:
        return True
    return any(role.id == STAFF_ROLE_ID for role in member.roles)


def tag_is_resolved(tag: discord.ForumTag) -> bool:
    if SOLVED_TAG_ID and str(tag.id) == str(SOLVED_TAG_ID):
        return True
    name = tag.name.lower()
    return any(k in name for k in ("solved", "resolved", "fixed", "closed"))


def tag_is_unsolved(tag: discord.ForumTag) -> bool:
    if UNSOLVED_TAG_ID and str(tag.id) == str(UNSOLVED_TAG_ID):
        return True
    name = tag.name.lower()
    return any(k in name for k in ("unsolved", "open", "pending", "waiting"))


def format_ticket_line(ticket: Ticket, extras: str = "") -> str:
    badges = []
    if ticket.has_logs:
        badges.append("📎 logs")
    if ticket.is_unseen:
        badges.append("👀 unseen")
    if ticket.is_stale:
        badges.append(f"⏰ {ticket.age_label}")
    badge_str = f" · {' · '.join(badges)}" if badges else ""
    extra_str = f" · {extras}" if extras else ""
    tag_str = f" · 🏷 {', '.join(ticket.tags[:2])}" if ticket.tags else ""
    preview = ticket.preview[:80] + "…" if len(ticket.preview) > 80 else ticket.preview
    return (
        f"**[{ticket.title[:70]}]({ticket.url})**\n"
        f"└ {ticket.age_label} old · by {ticket.owner_name}{badge_str}{tag_str}{extra_str}\n"
        f"   _{preview}_"
    )


def chunk_lines(lines: list[str], max_len: int = 950) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for line in lines:
        line_len = len(line) + 2
        if current and length + line_len > max_len:
            chunks.append("\n\n".join(current))
            current = []
            length = 0
        current.append(line)
        length += line_len
    if current:
        chunks.append("\n\n".join(current))
    return chunks or ["_None_"]


class TicketTrackerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        if DISCORD_GUILD_ID:
            guild = discord.Object(id=DISCORD_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✓ Synced slash commands to guild {DISCORD_GUILD_ID}")
        else:
            await self.tree.sync()
            print("✓ Synced slash commands globally")


bot = TicketTrackerBot()


async def get_forum_channel() -> Optional[discord.ForumChannel]:
    if not SUPPORT_FORUM_CHANNEL_ID:
        print("⚠ SUPPORT_FORUM_CHANNEL_ID not set")
        return None
    channel = bot.get_channel(SUPPORT_FORUM_CHANNEL_ID)
    if channel is None:
        channel = await bot.fetch_channel(SUPPORT_FORUM_CHANNEL_ID)
    if not isinstance(channel, discord.ForumChannel):
        print(f"⚠ Channel {SUPPORT_FORUM_CHANNEL_ID} is not a forum channel")
        return None
    return channel


async def analyze_thread(thread: discord.Thread) -> Optional[Ticket]:
    guild_id = thread.guild.id if thread.guild else DISCORD_GUILD_ID
    url = f"https://discord.com/channels/{guild_id}/{thread.id}"

    created_at = _as_utc(thread.created_at or _utcnow())
    age = _utcnow() - created_at

    owner_name = "Unknown"
    if thread.owner_id:
        try:
            owner = await bot.fetch_user(thread.owner_id)
            owner_name = owner.display_name or owner.name
        except discord.HTTPException:
            owner_name = f"User {thread.owner_id}"

    applied = list(getattr(thread, "applied_tags", []) or [])
    tag_names = [t.name for t in applied]
    is_resolved = any(tag_is_resolved(t) for t in applied)

    has_logs = False
    log_files: list[str] = []
    has_staff_reply = False
    staff_names: list[str] = []
    preview = ""
    message_count = 0

    try:
        async for msg in thread.history(limit=50, oldest_first=True):
            message_count += 1
            if not preview and msg.content:
                preview = msg.content.replace("\n", " ").strip()

            for att in msg.attachments:
                if is_log_file(att.filename):
                    has_logs = True
                    if att.filename not in log_files:
                        log_files.append(att.filename)

            if isinstance(msg.author, discord.Member) and is_staff(msg.author):
                has_staff_reply = True
                name = msg.author.display_name or msg.author.name
                if name not in staff_names:
                    staff_names.append(name)
    except discord.HTTPException as e:
        print(f"⚠ Could not read thread {thread.id}: {e}")
        return None

    if not preview:
        preview = "(no text content)"

    return Ticket(
        thread_id=thread.id,
        title=thread.name,
        url=url,
        created_at=created_at,
        age=age,
        owner_name=owner_name,
        preview=preview,
        has_logs=has_logs,
        log_files=log_files,
        has_staff_reply=has_staff_reply,
        staff_replied_by=staff_names,
        is_resolved=is_resolved or thread.archived,
        tags=tag_names,
        message_count=message_count,
    )


async def scan_all_tickets() -> list[Ticket]:
    forum = await get_forum_channel()
    if not forum:
        return []

    tickets: list[Ticket] = []
    threads = list(forum.threads)
    print(f"🔍 Scanning {len(threads)} active forum threads…")

    for i, thread in enumerate(threads):
        if thread.archived:
            continue
        ticket = await analyze_thread(thread)
        if ticket:
            tickets.append(ticket)
        if (i + 1) % 5 == 0:
            await asyncio.sleep(0.5)

    tickets.sort(key=lambda t: t.created_at, reverse=True)
    print(f"✓ Scanned {len(tickets)} tickets")
    return tickets


def build_summary_embeds(tickets: list[Ticket]) -> list[discord.Embed]:
    now = _utcnow()
    active = [t for t in tickets if not t.is_resolved]
    unseen_new = [t for t in active if t.is_unseen and t.is_new]
    unseen_older = [t for t in active if t.is_unseen and not t.is_new]
    with_logs = [t for t in active if t.has_logs]
    stale = [t for t in active if t.is_stale]
    logs_unseen = [t for t in with_logs if t.is_unseen]

    embeds: list[discord.Embed] = []

    overview = discord.Embed(
        title="📊 Support Forum Daily Summary",
        description=(
            f"**{len(active)}** open tickets · "
            f"**{len(unseen_new) + len(unseen_older)}** unseen · "
            f"**{len(with_logs)}** with logs · "
            f"**{len(stale)}** stale (>{STALE_HOURS}h unresolved)"
        ),
        color=0x5865F2,
        timestamp=now,
    )
    overview.add_field(
        name="Highlights",
        value=(
            f"🆕 **{len(unseen_new)}** new unseen (last {NEW_HOURS}h)\n"
            f"👀 **{len(unseen_older)}** older unseen\n"
            f"📎 **{len(logs_unseen)}** with logs & still unseen\n"
            f"⏰ **{len(stale)}** unresolved >{STALE_HOURS}h"
        ),
        inline=False,
    )
    overview.set_footer(text="Revolution Macro Support Tracker")
    embeds.append(overview)

    def add_section(title: str, items: list[Ticket], color: int, empty: str, extra_fn=None):
        if not items:
            return
        lines = []
        for t in items[:15]:
            extra = extra_fn(t) if extra_fn else ""
            lines.append(format_ticket_line(t, extra))
        if len(items) > 15:
            lines.append(f"_…and {len(items) - 15} more_")

        for i, chunk in enumerate(chunk_lines(lines)):
            section_title = title if i == 0 else f"{title} (cont.)"
            embed = discord.Embed(title=section_title, description=chunk, color=color)
            embeds.append(embed)

    add_section(
        f"🆕 New Unseen Tickets ({len(unseen_new)})",
        unseen_new,
        0xED4245,
        "No new unseen tickets — all caught up!",
    )
    add_section(
        f"👀 Unseen — Needs Attention ({len(unseen_older)})",
        unseen_older,
        0xFEE75C,
        "No older unseen tickets.",
    )
    add_section(
        f"📎 Tickets With Logs ({len(with_logs)})",
        with_logs,
        0x57F287,
        "No tickets with log files attached.",
        extra_fn=lambda t: ", ".join(t.log_files[:3]) if t.log_files else "",
    )
    add_section(
        f"⏰ Stale Unresolved — Over {STALE_HOURS}h ({len(stale)})",
        stale,
        0xEB459E,
        f"No tickets unresolved longer than {STALE_HOURS} hours.",
        extra_fn=lambda t: "no staff reply" if not t.has_staff_reply else f"staff: {', '.join(t.staff_replied_by[:2])}",
    )

    if not any([unseen_new, unseen_older, with_logs, stale]):
        embeds.append(
            discord.Embed(
                title="✅ All Clear",
                description="No open tickets need attention right now.",
                color=0x57F287,
            )
        )

    return embeds[:10]


async def send_daily_summary(user_id: Optional[int] = None) -> bool:
    target_id = user_id or LIAM_USER_ID
    try:
        user = await bot.fetch_user(target_id)
    except discord.HTTPException:
        print(f"⚠ Could not find user {target_id}")
        return False

    tickets = await scan_all_tickets()
    embeds = build_summary_embeds(tickets)

    try:
        for embed in embeds:
            await user.send(embed=embed)
            await asyncio.sleep(0.3)
        print(f"✅ Sent daily summary ({len(embeds)} embeds) to {user.name}")
        return True
    except discord.Forbidden:
        print(f"⚠ DMs disabled for {user.name}")
        return False


@tasks.loop(hours=24)
async def daily_summary_task():
    print(f"🕐 Daily summary task running at {_utcnow().isoformat()}")
    await send_daily_summary()


@daily_summary_task.before_loop
async def before_daily_summary():
    await bot.wait_until_ready()
    await asyncio.sleep(10)
    print(f"⏰ Daily summary scheduled every 24h → DM user {LIAM_USER_ID}")


@bot.event
async def on_ready():
    print(f"✓ Logged in as {bot.user} ({bot.user.id})")
    print(f"  Forum channel: {SUPPORT_FORUM_CHANNEL_ID}")
    print(f"  Liam DM target: {LIAM_USER_ID}")
    print(f"  Stale threshold: {STALE_HOURS}h")

    if not daily_summary_task.is_running():
        daily_summary_task.start()


@bot.event
async def on_thread_create(thread: discord.Thread):
    if not isinstance(thread.parent, discord.ForumChannel):
        return
    if thread.parent_id != SUPPORT_FORUM_CHANNEL_ID:
        return
    print(f"📬 New forum post: '{thread.name}' (id={thread.id})")


@bot.tree.command(name="daily_summary", description="Send the forum ticket summary to Liam now (Admin)")
async def daily_summary_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    ok = await send_daily_summary()
    if ok:
        await interaction.followup.send(f"✅ Summary sent to Liam (ID {LIAM_USER_ID}).", ephemeral=True)
    else:
        await interaction.followup.send("❌ Failed to send summary. Check bot logs.", ephemeral=True)


@bot.tree.command(name="scan", description="Preview current ticket counts without sending a DM (Admin)")
async def scan_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    tickets = await scan_all_tickets()
    active = [t for t in tickets if not t.is_resolved]
    unseen = [t for t in active if t.is_unseen]
    logs = [t for t in active if t.has_logs]
    stale = [t for t in active if t.is_stale]

    await interaction.followup.send(
        f"**Forum scan complete**\n"
        f"• {len(active)} open tickets\n"
        f"• {len(unseen)} unseen\n"
        f"• {len(logs)} with logs\n"
        f"• {len(stale)} stale (>{STALE_HOURS}h)",
        ephemeral=True,
    )


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        raise SystemExit("DISCORD_BOT_TOKEN is required")
    if not SUPPORT_FORUM_CHANNEL_ID:
        raise SystemExit("SUPPORT_FORUM_CHANNEL_ID is required")
    bot.run(DISCORD_BOT_TOKEN)
