import os
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
import google.generativeai as genai
from dotenv import load_dotenv
import aiohttp

# --- Configuration ---
load_dotenv()

# 1. LOAD ENVIRONMENT VARIABLES FROM .env FILE
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SUPPORT_FORUM_CHANNEL_ID_STR = os.getenv('SUPPORT_FORUM_CHANNEL_ID')
DISCORD_GUILD_ID_STR = os.getenv('DISCORD_GUILD_ID', '1265864190883532872')  # Server ID for slash command sync
DATA_API_URL = os.getenv('DATA_API_URL', 'https://your-vercel-app.vercel.app/api/data')

# --- Initial Validation ---
if not DISCORD_BOT_TOKEN:
    print("FATAL ERROR: 'DISCORD_BOT_TOKEN' not found in environment.")
    exit()

if not GEMINI_API_KEY:
    print("FATAL ERROR: 'GEMINI_API_KEY' not found in environment.")
    exit()

if not SUPPORT_FORUM_CHANNEL_ID_STR:
    print("FATAL ERROR: 'SUPPORT_FORUM_CHANNEL_ID' not found in environment.")
    exit()

try:
    SUPPORT_FORUM_CHANNEL_ID = int(SUPPORT_FORUM_CHANNEL_ID_STR)
except ValueError:
    print("FATAL ERROR: 'SUPPORT_FORUM_CHANNEL_ID' is not a valid number.")
    exit()

try:
    DISCORD_GUILD_ID = int(DISCORD_GUILD_ID_STR)
except ValueError:
    print("FATAL ERROR: 'DISCORD_GUILD_ID' is not a valid number.")
    exit()

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True  # CRITICAL: Required for reading message content
intents.guilds = True
intents.members = True
# Note: Threads are included in default() intents for discord.py >= 2.0
# Make sure MESSAGE CONTENT intent is enabled in Discord Developer Portal!
bot = commands.Bot(command_prefix="!unused-prefix!", intents=intents)

# --- Constants ---
IGNORE = "!"  # Messages starting with this prefix are ignored
STAFF_ROLE_ID = 1422106035337826315  # Staff role that can use bot commands
BOT_PERMISSIONS_ROLE_ID = 1439854362900959404  # Role that gives permissions for bot slash commands
OWNER_USER_ID = 614865086804394012  # Bot owner - full access to all commands

# --- DATA STORAGE (Synced from Dashboard) ---
RAG_DATABASE = []
AUTO_RESPONSES = []
SYSTEM_PROMPT_TEXT = ""  # Fetched from API, fallback to default if not available

# --- BOT SETTINGS (Stored in Vercel KV API - NO local files) ---
BOT_SETTINGS = {
    'support_forum_channel_id': SUPPORT_FORUM_CHANNEL_ID,
    'satisfaction_delay': 15,  # Seconds to wait before analyzing satisfaction
    'satisfaction_analysis_enabled': True,  # Enable/disable automatic satisfaction analysis (saves API calls!)
    'ai_temperature': 1.0,  # Gemini temperature (0.0-2.0)
    'ai_max_tokens': 2048,  # Max tokens for AI responses
    'ignored_post_ids': [],  # Post IDs to ignore (e.g., rules post)
    'post_inactivity_hours': 12,  # Hours before escalating old posts to High Priority
    'high_priority_check_interval_hours': 1.0,  # Hours between high priority checks (0.25 = 15 min, 1.0 = 1 hour)
    'solved_post_retention_days': 30,  # Days to keep solved/closed posts before deletion
    'unsolved_tag_id': None,  # Discord tag ID for "Unsolved" posts
    'resolved_tag_id': None,  # Discord tag ID for "Resolved" posts
    'auto_rag_enabled': True,  # Auto-create RAG entries from solved threads
    'support_notification_channel_id': '1436918674069000212',  # Channel ID for high priority notifications (string to prevent JS precision loss)
    'support_role_id': None,  # Support role ID to ping (optional)
    'last_updated': datetime.now().isoformat()
}

# --- GEMINI API RATE LIMITING (10 requests per minute) ---
from collections import deque
gemini_api_calls = deque(maxlen=100)  # Track last 100 API calls

async def check_rate_limit():
    """Check if we can make a Gemini API call without hitting rate limit"""
    now = datetime.now()
    # Remove calls older than 1 minute
    while gemini_api_calls and (now - gemini_api_calls[0]).total_seconds() > 60:
        gemini_api_calls.popleft()
    
    # Check if we're at the limit (10 per minute)
    if len(gemini_api_calls) >= 10:
        oldest_call = gemini_api_calls[0]
        wait_time = 60 - (now - oldest_call).total_seconds()
        print(f"⚠️ RATE LIMIT: {len(gemini_api_calls)}/10 API calls in last minute. Waiting {wait_time:.1f}s...")
        return False
    return True

def track_api_call():
    """Track that we made a Gemini API call"""
    gemini_api_calls.append(datetime.now())
    print(f"📊 Gemini API calls: {len(gemini_api_calls)}/10 in last minute")

# --- SATISFACTION ANALYSIS TIMERS ---
# Track pending satisfaction analysis tasks per thread
satisfaction_timers = {}  # {thread_id: asyncio.Task}
# Track processed threads to avoid duplicate processing
processed_threads = set()  # {thread_id}
# Track threads currently being processed (lock to prevent race conditions)
processing_threads = set()  # {thread_id}
# Track threads escalated to human support (bot stops responding)
escalated_threads = set()  # {thread_id}
# Track what type of response was given per thread (for satisfaction flow)
thread_response_type = {}  # {thread_id: 'auto' | 'ai' | None}
# Track threads manually closed with no_review (don't create RAG entries)
no_review_threads = set()  # {thread_id}

# REMOVED: No local storage - all data in Vercel KV API only

# --- SATISFACTION BUTTON VIEW ---
class SatisfactionButtons(discord.ui.View):
    """Interactive buttons for user feedback on bot responses"""
    
    def __init__(self, thread_id, conversation, response_type):
        super().__init__(timeout=None)  # Buttons never expire
        self.thread_id = thread_id
        self.conversation = conversation
        self.response_type = response_type
    
    @discord.ui.button(label="Yes, this solved my issue", style=discord.ButtonStyle.green, emoji="✅")
    async def solved_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle when user confirms issue is solved"""
        await interaction.response.defer()
        
        thread = interaction.channel
        print(f"✅ User clicked SOLVED button for thread {self.thread_id}")
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        # Send confirmation embed
        confirm_embed = discord.Embed(
            title="✅ Great! Issue Solved",
            description="Glad I could help! This post will now be locked.",
            color=0x2ECC71
        )
        confirm_embed.add_field(
            name="💬 More Questions?",
            value="Create a new post anytime!",
            inline=False
        )
        confirm_embed.set_footer(text="Revolution Macro Support")
        await thread.send(embed=confirm_embed)
        
        # Update status to Solved
        updated_status = 'Solved'
        
        # Apply tags
        try:
            forum_channel = bot.get_channel(SUPPORT_FORUM_CHANNEL_ID)
            if forum_channel:
                resolved_tag = await get_resolved_tag(forum_channel)
                unsolved_tag = await get_unsolved_tag(forum_channel)
                
                current_tags = list(thread.applied_tags)
                
                if unsolved_tag and unsolved_tag in current_tags:
                    current_tags.remove(unsolved_tag)
                    print(f"🏷️ Removed '{unsolved_tag.name}' tag from thread {self.thread_id}")
                
                if resolved_tag and resolved_tag not in current_tags:
                    current_tags.append(resolved_tag)
                    print(f"🏷️ Applied '{resolved_tag.name}' tag to thread {self.thread_id}")
                
                await thread.edit(applied_tags=current_tags)
        except Exception as tag_error:
            print(f"⚠ Could not update tags: {tag_error}")
        
        # Lock thread
        try:
            await thread.edit(archived=True, locked=True)
            print(f"🔒 Thread {self.thread_id} locked and archived successfully")
        except Exception as lock_error:
            print(f"❌ Error locking thread {self.thread_id}: {lock_error}")
        
        # Create pending RAG entry (if auto-RAG is enabled)
        try:
            # Check if auto-RAG creation is enabled
            if not BOT_SETTINGS.get('auto_rag_enabled', True):
                print(f"ℹ️ Auto-RAG creation is disabled. Skipping RAG entry for thread {self.thread_id}")
            else:
                print(f"📝 Attempting to create RAG entry from solved conversation...")
                
                formatted_lines = []
                for msg in self.conversation:
                    author = msg.get('author', 'Unknown')
                    content = msg.get('content', '')
                    formatted_lines.append(f"<@{author}> Said: {content}")
                
                conversation_text = "\n".join(formatted_lines)
                rag_entry = await analyze_conversation(conversation_text)
                
            if BOT_SETTINGS.get('auto_rag_enabled', True) and self.thread_id not in no_review_threads and rag_entry and 'your-vercel-app' not in DATA_API_URL:
                data_api_url_rag = DATA_API_URL
                
                async with aiohttp.ClientSession() as rag_session:
                    async with rag_session.get(data_api_url_rag) as get_data_response:
                        current_data = {'ragEntries': [], 'autoResponses': [], 'slashCommands': [], 'pendingRagEntries': []}
                        if get_data_response.status == 200:
                            current_data = await get_data_response.json()
                        
                        conversation_preview = conversation_text[:500] + "..." if len(conversation_text) > 500 else conversation_text
                        
                        new_pending_entry = {
                            'id': f'PENDING-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                            'title': rag_entry.get('title', 'Auto-generated from solved thread'),
                            'content': rag_entry.get('content', ''),
                            'keywords': rag_entry.get('keywords', []),
                            'createdAt': datetime.now().isoformat(),
                            'source': 'User-confirmed satisfaction',
                            'threadId': str(self.thread_id),
                            'conversationPreview': conversation_preview
                        }
                        
                        pending_entries = current_data.get('pendingRagEntries', [])
                        pending_entries.append(new_pending_entry)
                        
                        save_data = {
                            'ragEntries': current_data.get('ragEntries', []),
                            'autoResponses': current_data.get('autoResponses', []),
                            'slashCommands': current_data.get('slashCommands', []),
                            'botSettings': current_data.get('botSettings', {}),
                            'pendingRagEntries': pending_entries
                        }
                        
                        print(f"💾 Saving pending RAG entry to API for review...")
                        
                        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                        async with rag_session.post(data_api_url_rag, json=save_data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as save_response:
                            if save_response.status == 200:
                                print(f"✅ Created pending RAG entry for review: '{new_pending_entry['title']}'")
                                
                                rag_notification = discord.Embed(
                                    title="📋 Entry Saved for Review",
                                    description=f"**{new_pending_entry['title']}**\n\nThis will be reviewed and added to help future users!",
                                    color=0xF39C12
                                )
                                rag_notification.set_footer(text="Revolution Macro • Pending Approval")
                                await thread.send(embed=rag_notification)
        except Exception as rag_error:
            print(f"⚠ Error auto-creating RAG entry: {rag_error}")
        
        # Update dashboard
        await update_forum_post_status(self.thread_id, updated_status)
    
    @discord.ui.button(label="No, my issue isn't resolved", style=discord.ButtonStyle.red, emoji="❌")
    async def not_solved_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle when user says issue is not resolved"""
        await interaction.response.defer()
        
        thread = interaction.channel
        print(f"❌ User clicked NOT SOLVED button for thread {self.thread_id}")
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        # Check escalation path based on response type
        if self.response_type == 'auto':
            # Auto-response didn't help, try AI
            print(f"🔄 ESCALATION PATH: Auto → AI (user clicked not solved after auto-response)")
            
            try:
                # Get user's question from conversation
                user_messages = [msg.get('content', '') for msg in self.conversation if msg.get('author') == 'User']
                user_question = ' '.join(user_messages[:2]) if user_messages else "Help with this issue"
                
                # Try to find RAG entries
                relevant_docs = find_relevant_rag_entries(user_question)
                
                # Generate AI response (no images in button handler)
                if relevant_docs:
                    ai_response = await generate_ai_response(user_question, relevant_docs[:2], None)
                else:
                    ai_response = await generate_ai_response(user_question, [], None)
                
                # Send AI response with buttons
                ai_embed = discord.Embed(
                    title="💡 Let Me Try Again",
                    description=ai_response,
                    color=0x5865F2
                )
                ai_embed.add_field(
                    name="💬 Better?",
                    value="Let me know if this helps!",
                    inline=False
                )
                ai_embed.set_footer(text="Revolution Macro AI")
                
                # Add new buttons for AI response
                new_view = SatisfactionButtons(self.thread_id, self.conversation, 'ai')
                await thread.send(embed=ai_embed, view=new_view)
                thread_response_type[self.thread_id] = 'ai'
                
                await update_forum_post_status(self.thread_id, 'AI Response')
                print(f"✅ Sent AI follow-up response to thread {self.thread_id}")
                
            except Exception as ai_error:
                print(f"❌ Error generating AI follow-up: {ai_error}")
                # Escalate to human on error
                user_who_clicked = interaction.user if hasattr(interaction, 'user') else None
                await self._escalate_to_human(thread, user_who_clicked)
        else:
            # AI response didn't help (or was already AI), escalate to human
            print(f"⚠ ESCALATION PATH: → Human (user clicked not solved after AI response)")
            user_who_clicked = interaction.user if hasattr(interaction, 'user') else None
            await self._escalate_to_human(thread, user_who_clicked)
    
    async def _escalate_to_human(self, thread, user_who_triggered=None):
        """Escalate thread to human support with log upload prompt (only to post creator)"""
        escalated_threads.add(self.thread_id)
        
        # Get thread owner (post creator)
        thread_owner_id = None
        try:
            if hasattr(thread, 'owner_id') and thread.owner_id:
                thread_owner_id = thread.owner_id
            elif hasattr(thread, 'owner') and thread.owner:
                thread_owner_id = thread.owner.id
        except Exception as e:
            print(f"⚠ Could not get thread owner: {e}")
        
        # Only show log prompt if:
        # 1. We have a user who triggered this (from satisfaction flow)
        # 2. That user is the thread owner (post creator)
        # 3. That user is NOT staff/admin
        should_show_log_prompt = False
        if user_who_triggered and thread_owner_id:
            is_creator = user_who_triggered.id == thread_owner_id
            is_staff = is_staff_or_admin(user_who_triggered) if isinstance(user_who_triggered, discord.Member) else False
            should_show_log_prompt = is_creator and not is_staff
        
        if should_show_log_prompt:
            # First, ask for logs to help support team (only to post creator)
            log_prompt_embed = discord.Embed(
                title="📋 Before We Get Support...",
                description="To help our team solve this **much faster**, please include your **logs**!\n\nLogs contain error details that help us identify exactly what's wrong.",
                color=0xF39C12
            )
            log_prompt_embed.add_field(
                name="🧭 How to Get Logs (from the Macro)",
                value=(
                    "1) Open the macro and go to **Status → Logs**\n"
                    "2) Click **Copy Logs** → then paste here\n"
                    "   - or -\n"
                    "   Click **Open Logs Folder** → upload the most recent `.log` file"
                ),
                inline=False
            )
            log_prompt_embed.add_field(
                name="📌 Tips",
                value="Please include screenshots or a short video if possible. It helps a ton!",
                inline=False
            )
            log_prompt_embed.set_footer(text="💡 Uploading logs can reduce resolution time by 50%!")
            
            # Send the unified logs instructions (no OS selector needed anymore)
            await thread.send(embed=log_prompt_embed)
            
            # Wait a moment, then send escalation message
            await asyncio.sleep(2)
        else:
            print(f"ℹ Skipping log prompt - user is not post creator or is staff/admin")
        
        escalate_embed = discord.Embed(
            title="👨‍💼 Support Team Notified",
            description="Our support team has been notified and will review your issue soon!",
            color=0xE67E22
        )
        escalate_embed.add_field(
            name="⏰ Response Time",
            value="Usually under 24 hours",
            inline=True
        )
        escalate_embed.add_field(
            name="📎 Helpful to Include",
            value="Screenshots, videos, or error messages",
            inline=True
        )
        escalate_embed.set_footer(text="Revolution Macro Support Team")
        await thread.send(embed=escalate_embed)
        
        await update_forum_post_status(self.thread_id, 'Human Support')
        print(f"⚠ Thread {self.thread_id} escalated to Human Support")


class OSLogTutorialSelect(discord.ui.View):
    """Interactive dropdown menu for selecting OS to get log tutorial"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Never expires
    
    # The OS selector is now deprecated in favor of in-macro instructions.
    # Keep a simple helper button-less view to maintain compatibility if referenced.
    pass


async def update_forum_post_status(thread_id, status):
    """Helper function to update forum post status in dashboard"""
    if 'your-vercel-app' in DATA_API_URL:
        return
    
    try:
        forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(forum_api_url, timeout=aiohttp.ClientTimeout(total=10)) as get_resp:
                if get_resp.status == 200:
                    all_posts = await get_resp.json()
                    current_post = None
                    for p in all_posts:
                        if p.get('postId') == str(thread_id) or p.get('id') == f'POST-{thread_id}':
                            current_post = p
                            break
                    
                    if current_post:
                        current_post['status'] = status
                        update_payload = {
                            'action': 'update',
                            'post': current_post
                        }
                        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                        async with session.post(forum_api_url, json=update_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as update_resp:
                            if update_resp.status == 200:
                                print(f"✅ Updated forum post status to '{status}' for thread {thread_id}")
    except Exception as e:
        print(f"❌ Error updating status: {e}")

# --- BOT SETTINGS FUNCTIONS ---
def load_bot_settings():
    """Load bot settings from API (called during data sync)"""
    # This is now handled in fetch_data_from_api()
    # Settings are loaded from API's botSettings field
    # Keeping this function for backwards compatibility
    print(f"ℹ️ Bot settings loaded from API during sync")
    return True

async def save_bot_settings_to_api():
    """Save bot settings to API (persists across deployments)"""
    try:
        if 'your-vercel-app' in DATA_API_URL:
            print("⚠ API not configured, cannot save settings")
            return False
        
        BOT_SETTINGS['last_updated'] = datetime.now().isoformat()
        
        # Fetch current data from API
        async with aiohttp.ClientSession() as session:
            async with session.get(DATA_API_URL) as get_response:
                if get_response.status != 200:
                    print(f"⚠ Failed to fetch current data: {get_response.status}")
                    return False
                
                current_data = await get_response.json()
                
                # Update botSettings in the data - include system prompt if we have it
                full_bot_settings = BOT_SETTINGS.copy()
                if SYSTEM_PROMPT_TEXT:
                    full_bot_settings['systemPrompt'] = SYSTEM_PROMPT_TEXT
                    print(f"🔍 DEBUG: Including custom system prompt ({len(SYSTEM_PROMPT_TEXT)} chars)")
                
                current_data['botSettings'] = full_bot_settings
                
                # Debug: Show what we're saving
                print(f"🔍 DEBUG: Saving botSettings to API")
                print(f"🔍 DEBUG: support_notification_channel_id = {BOT_SETTINGS.get('support_notification_channel_id')}")
                print(f"🔍 DEBUG: systemPrompt included = {bool(full_bot_settings.get('systemPrompt'))}")
                
                # Save back to API
                headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                async with session.post(DATA_API_URL, json=current_data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as save_response:
                    if save_response.status == 200:
                        print(f"✅ Saved bot settings to API (persisted)")
                        return True
                    else:
                        print(f"⚠ Failed to save settings to API: {save_response.status}")
                        return False
    except Exception as e:
        print(f"⚠ Error saving bot settings to API: {e}")
        return False

def save_bot_settings():
    """Wrapper for backwards compatibility - schedules async save"""
    # Create a task to save settings asynchronously
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(save_bot_settings_to_api())
        else:
            loop.run_until_complete(save_bot_settings_to_api())
        return True
    except Exception as e:
        print(f"⚠ Error scheduling settings save: {e}")
        return False

# --- DATA SYNC FUNCTIONS ---
async def fetch_data_from_api():
    """Fetch RAG entries, auto-responses, and system prompt from the dashboard API"""
    global RAG_DATABASE, AUTO_RESPONSES, SYSTEM_PROMPT_TEXT
    
    # Skip API call if URL is still the placeholder
    if 'your-vercel-app' in DATA_API_URL:
        print("ℹ Skipping API sync - Vercel URL not configured. Bot will use local data.")
        load_local_fallback_data()
        return False
    
    print(f"🔗 Attempting to fetch data from: {DATA_API_URL}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATA_API_URL}", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    new_rag = data.get('ragEntries', [])
                    new_auto = data.get('autoResponses', [])
                    new_settings = data.get('botSettings', {})
                    
                    # Debug: Show what settings we got from API
                    if new_settings:
                        print(f"🔍 DEBUG: Received botSettings from API with keys: {list(new_settings.keys())}")
                        if 'support_notification_channel_id' in new_settings:
                            print(f"🔍 DEBUG: support_notification_channel_id = {new_settings['support_notification_channel_id']}")
                    
                    # Check if data actually changed (count or content) - BEFORE updating
                    old_rag_count = len(RAG_DATABASE)
                    old_auto_count = len(AUTO_RESPONSES)
                    old_auto_ids = {a.get('id') for a in AUTO_RESPONSES if a.get('id')}
                    rag_changed = len(new_rag) != old_rag_count
                    auto_changed = len(new_auto) != old_auto_count
                    
                    # Update data
                    RAG_DATABASE = new_rag
                    AUTO_RESPONSES = new_auto
                    
                    # Update system prompt if available
                    if new_settings and 'systemPrompt' in new_settings:
                        SYSTEM_PROMPT_TEXT = new_settings['systemPrompt']
                        print(f"✓ Loaded custom system prompt from API ({len(SYSTEM_PROMPT_TEXT)} characters)")
                    
                    # Load bot settings from API (persists across deployments!)
                    if new_settings:
                        # Merge API settings with defaults, API takes priority
                        settings_to_merge = {k: v for k, v in new_settings.items() if k != 'systemPrompt'}
                        if settings_to_merge:
                            BOT_SETTINGS.update(settings_to_merge)
                            print(f"✓ Loaded bot settings from API (persisted across deployments)")
                            print(f"   satisfaction_delay={BOT_SETTINGS.get('satisfaction_delay', 15)}s, "
                                  f"temperature={BOT_SETTINGS.get('ai_temperature', 1.0)}, "
                                  f"retention={BOT_SETTINGS.get('solved_post_retention_days', 30)}d, "
                                  f"notification_channel={BOT_SETTINGS.get('support_notification_channel_id', 'Not set')}")
                    
                    # Log changes for visibility
                    print(f"✓ Successfully connected to dashboard API!")
                    if rag_changed or auto_changed:
                        print(f"✓ Synced {len(RAG_DATABASE)} RAG entries and {len(AUTO_RESPONSES)} auto-responses from dashboard.")
                        if rag_changed:
                            print(f"  → RAG entries changed: {len(new_rag)} (was {old_rag_count})")
                            # Log new RAG entry titles for debugging
                            old_rag_ids = {e.get('id') for e in RAG_DATABASE}
                            for rag in new_rag:
                                rag_id = rag.get('id')
                                if rag_id and rag_id not in old_rag_ids:
                                    print(f"    + New RAG entry: '{rag.get('title', 'Unknown')}' (ID: {rag_id})")
                                    print(f"      Keywords: {', '.join(rag.get('keywords', []))}")
                        if auto_changed:
                            print(f"  → Auto-responses changed: {len(new_auto)} (was {old_auto_count})")
                            # Log new auto-response names for debugging
                            for auto in new_auto:
                                auto_id = auto.get('id')
                                if auto_id and auto_id not in old_auto_ids:
                                    print(f"    + New auto-response: '{auto.get('name', 'Unknown')}' with triggers: {auto.get('triggerKeywords', [])}")
                    else:
                        print(f"✓ Data already up to date ({len(RAG_DATABASE)} RAG entries, {len(AUTO_RESPONSES)} auto-responses)")
                        # Log all RAG entry titles for debugging
                        print(f"  📋 Available RAG entries:")
                        for rag in RAG_DATABASE[:5]:  # Show first 5
                            print(f"     - {rag.get('title', 'Unknown')} (ID: {rag.get('id', 'N/A')})")
                        if len(RAG_DATABASE) > 5:
                            print(f"     ... and {len(RAG_DATABASE) - 5} more")
                    return True
                elif response.status == 404:
                    print(f"⚠ Dashboard API not found (404) at {DATA_API_URL}. Check your URL configuration.")
                    print("ℹ Using local data. Deploy to Vercel to sync with dashboard.")
                    load_local_fallback_data()
                    return False
                else:
                    text = await response.text()
                    print(f"⚠ Failed to fetch data from API: Status {response.status}")
                    print(f"   Response: {text[:200]}")
                    print("ℹ Using local data.")
                    load_local_fallback_data()
                    return False
    except asyncio.TimeoutError:
        print(f"⚠ API request timed out when connecting to {DATA_API_URL}")
        print("ℹ Using local data.")
        load_local_fallback_data()
        return False
    except aiohttp.ClientError as e:
        print(f"⚠ Network error connecting to dashboard API: {type(e).__name__}: {str(e)}")
        print(f"   URL attempted: {DATA_API_URL}")
        print("ℹ Using local data. Check your DATA_API_URL environment variable.")
        load_local_fallback_data()
        return False
    except Exception as e:
        print(f"⚠ Error connecting to dashboard API: {type(e).__name__}: {str(e)}")
        print(f"   URL attempted: {DATA_API_URL}")
        print("ℹ Using local data.")
        load_local_fallback_data()
        return False

def load_local_fallback_data():
    """Load fallback data if API is unavailable"""
    global RAG_DATABASE, AUTO_RESPONSES
    RAG_DATABASE = [
        {
            'id': 'RAG-001',
            'title': 'Character Resets Instead of Converting Honey',
            'content': "This issue typically occurs when the 'Auto-Deposit' setting is enabled, but the main 'Gather' task is not set to pause during the conversion process. The macro incorrectly prioritizes gathering, causing it to reset the character's position and interrupt honey conversion. To fix this, go to Script Settings > Tasks > Gather and check the box 'Pause While Converting Honey'. Alternatively, you can disable 'Auto-Deposit' in the Hive settings.",
            'keywords': ['honey', 'pollen', 'convert', 'reset', 'resets', 'resetting', 'gather', 'auto-deposit', 'stuck', 'hive'],
        },
    ]
    AUTO_RESPONSES = [
        {
            'id': 'AR-001',
            'name': 'Password Reset',
            'triggerKeywords': ['password', 'reset', 'forgot', 'lost account'],
            'responseText': 'You can reset your password by visiting this link: [https://revolutionmacro.com/password-reset](https://revolutionmacro.com/password-reset).',
        },
    ]
    print("✓ Loaded fallback local data.")

# --- Context Fetching Functions ---
async def fetch_context(msg):
    """Fetch last 10 messages and format them"""
    messages = []
    async for m in msg.channel.history(limit=10):
        if m.content.startswith(IGNORE):  # Ignore
            continue
        messages.append(m)
    messages.reverse()  # Oldest to newest
    formatted_lines = []
    emoji_pattern = re.compile(r'<a?:([a-zA-Z0-9_]+):\d+>')
    for m in messages:
        author = m.author.display_name
        content = m.content
        
        # Replace mentions with display names
        for user in m.mentions:
            content = content.replace(f"<@{user.id}>", f"<@{user.display_name}>")
            content = content.replace(f"<@!{user.id}>", f"<@{user.display_name}>")
        
        # Replace emojis
        content = emoji_pattern.sub(r'<Emoji: \1>', content)
        
        # Check for attachments
        if m.attachments:
            for attachment in m.attachments:
                if attachment.content_type and "image" in attachment.content_type:
                    content += " <Media: Image>"
                else:
                    content += " <Media: File>"
        
        # Replies
        if m.reference and m.reference.resolved:
            replied_to = m.reference.resolved.author.display_name
            formatted_line = f"<@{author}> Replied to <@{replied_to}> with: {content}"
        else:
            formatted_line = f"<@{author}> Said: {content}"
        
        formatted_lines.append(formatted_line)
    
    formatted_string = "\n".join(formatted_lines)
    return formatted_string

# REMOVED: No local RAG storage - all data loaded from API in memory only
# RAG_DATABASE is loaded from API and kept in memory

# --- CORE BOT LOGIC (MIRRORS PLAYGROUND) ---
def get_auto_response(query: str) -> str | None:
    """Check if query matches any auto-response triggers"""
    query_lower = query.lower()
    
    # Debug: Log what we're checking
    if len(AUTO_RESPONSES) == 0:
        print(f"⚠ No auto-responses loaded. Query: '{query[:50]}...'")
    
    for auto_response in AUTO_RESPONSES:
        trigger_keywords = auto_response.get('triggerKeywords', [])
        for keyword in trigger_keywords:
            if keyword.lower() in query_lower:
                response_text = auto_response.get('responseText')
                print(f"✓ Auto-response matched: '{auto_response.get('name', 'Unknown')}' (keyword: '{keyword}')")
                return response_text
    
    # Debug: Log what we checked if no match
    if AUTO_RESPONSES:
        all_keywords = [kw for auto in AUTO_RESPONSES for kw in auto.get('triggerKeywords', [])]
        print(f"ℹ No auto-response match. Checked {len(AUTO_RESPONSES)} auto-responses with {len(all_keywords)} total keywords.")
    
    return None

def find_relevant_rag_entries(query, db=RAG_DATABASE):
    """Find relevant RAG entries with improved scoring algorithm"""
    # Keep ALL words, including short ones (vpn, api, etc.)
    query_words = set(query.lower().split())
    # Remove ONLY very common/meaningless words
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'be'}
    query_words = {word for word in query_words if word not in stopwords}
    
    scored_entries = []
    for entry in db:
        score = 0
        entry_title = entry.get('title', '').lower()
        entry_content = entry.get('content', '').lower()
        entry_keywords = ' '.join(entry.get('keywords', [])).lower()
        
        # Weighted scoring (same as dashboard):
        # - Title match: 5 points (highest priority)
        # - Keyword match: 3 points (high priority)
        # - Content match: 1 point (lower priority)
        for word in query_words:
            if word in entry_title:
                score += 5
            if word in entry_keywords:
                score += 3
            if word in entry_content:
                score += 1
        
        if score > 0:
            scored_entries.append({'entry': entry, 'score': score})
    
    # Sort by score (highest first) and filter out very low scores
    scored_entries.sort(key=lambda x: x['score'], reverse=True)
    
    # Log for debugging
    if scored_entries:
        top_score = scored_entries[0]['score']
        print(f"📊 Found {len(scored_entries)} relevant RAG entries (top score: {top_score})")
        for item in scored_entries[:3]:  # Log top 3
            entry_title = item['entry'].get('title', 'Unknown')
            print(f"   - '{entry_title}' (score: {item['score']})")
    else:
        print(f"⚠ No RAG entries matched query: '{query[:50]}...'")
        print(f"   Total RAG entries in database: {len(db)}")
    
    return [item['entry'] for item in scored_entries]

SYSTEM_PROMPT = (
    "You are Revolution Macro support bot. ALWAYS try to answer directly based on the post title and message - DON'T ask 'what's wrong' unless absolutely necessary.\n\n"
    
    "CRITICAL RULES:\n"
    "1. Read the POST TITLE first - it contains the key issue\n"
    "2. ALWAYS attempt a direct answer based on title + message\n"
    "3. Use knowledge base if available\n"
    "4. Keep answers SHORT (2-3 sentences MAX)\n"
    "5. If you truly can't help, acknowledge human support is available\n\n"
    
    "REVOLUTION MACRO FEATURES:\n"
    "- Auto farming/gathering resources\n"
    "- Smart navigation and pathfinding\n"
    "- Auto-deposit to containers\n"
    "- Planter automation and scheduling\n"
    "- License activation system\n"
    "- Robobear challenge automation\n\n"
    
    "HOW TO ANSWER:\n"
    "✅ GOOD: 'To download, go to #downloads channel and click the latest version link. Run the .exe file after extracting.'\n"
    "❌ BAD: 'Could you clarify what you're trying to download?' [Wasting time!]\n\n"
    "✅ GOOD: 'Try: 1. Restart macro 2. Check license is active 3. Use windowed mode'\n"
    "❌ BAD: 'Well, this could be caused by several things...' [Too long!]\n\n"
    
    "IF YOU CAN'T HELP:\n"
    "Say: 'I don't have specific info on this. Our support team can help - they usually respond within 24 hours.'\n\n"
    
    "Remember: POST TITLE = Main clue. Answer directly. Be SHORT. Human support is backup."
)

async def download_images_for_gemini(attachments):
    """Download images from Discord, prepare for Gemini, returns list of PIL Images"""
    image_data = []
    try:
        import PIL.Image
        import io
        
        for attachment in attachments:
            # Only process images
            if attachment.content_type and "image" in attachment.content_type:
                print(f"📥 Downloading image: {attachment.filename}")
                
                # Download the image to memory
                image_bytes = await attachment.read()
                
                # Open with PIL (in memory, no disk I/O)
                image = PIL.Image.open(io.BytesIO(image_bytes))
                
                # Gemini accepts PIL Image objects directly
                image_data.append(image)
                print(f"✅ Image prepared: {attachment.filename} ({image.size[0]}x{image.size[1]})")
        
        return image_data if image_data else None
    
    except Exception as e:
        print(f"⚠ Error downloading images: {e}")
        return None

def build_user_context(query, context_entries):
    """Build the user message with query and knowledge base context."""
    context_text = "\n\n".join(
        [f"Title: {entry['title']}\nContent: {entry['content']}"
         for entry in context_entries]
    )
    return (
        f"Knowledge Base Context:\n{context_text}\n\n"
        f"User Question:\n{query}"
    )

async def generate_ai_response(query, context_entries, image_data=None):
    try:
        # Check rate limit before making API call
        if not await check_rate_limit():
            print(f"⚠️ Skipping AI response generation due to rate limit")
            return "I'm experiencing high traffic right now. Please wait a moment or contact human support!"
        
        # Use API system prompt if available, otherwise use default
        system_instruction = SYSTEM_PROMPT_TEXT if SYSTEM_PROMPT_TEXT else SYSTEM_PROMPT
        
        # Get AI settings from bot settings
        temperature = BOT_SETTINGS.get('ai_temperature', 1.0)
        max_tokens = BOT_SETTINGS.get('ai_max_tokens', 2048)
        
        # Use vision model if we have images
        model_name = 'gemini-2.0-flash-exp' if image_data else 'gemini-2.5-flash'
        model = genai.GenerativeModel(
            model_name,
            system_instruction=system_instruction
        )
        
        if image_data:
            print(f"🖼️ Using vision model with {len(image_data)} image(s)")
        
        # Configure generation settings
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        
        # User context separated
        user_context = build_user_context(query, context_entries)
        
        # Prepare content for Gemini (text + images if provided)
        if image_data:
            # Include images in the prompt for vision model
            content_parts = []
            for img in image_data:
                content_parts.append(img)
            content_parts.append(user_context)
            prompt_content = content_parts
        else:
            prompt_content = user_context
        
        # Generate response with custom settings
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(prompt_content, generation_config=generation_config)
        )
        track_api_call()  # Track successful API call
        
        # Clean up images from memory after use
        if image_data:
            for img in image_data:
                img.close()  # Release image from memory
            print(f"🗑️ Cleaned up {len(image_data)} image(s) from memory")
        
        return response.text
    except Exception as e:
        print(f"An error occurred with the Gemini API: {e}")
        return "I'm sorry, I'm having trouble connecting to my AI brain right now. A human will be with you shortly."

async def analyze_conversation(conversation_text):
    """Analyze a conversation and create a RAG entry from it"""
    try:
        # Check rate limit before making API call
        if not await check_rate_limit():
            print(f"⚠️ Skipping RAG entry generation due to rate limit")
            return None
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = (
            "Analyze the following support conversation and generate a structured knowledge base entry from it.\n"
            "- The 'title' should be a clear, concise summary of the problem (e.g., 'Fix for ... Error').\n"
            "- The 'content' should be a detailed explanation of the solution.\n"
            "- The 'keywords' should be an array of relevant search terms.\n\n"
            f"Conversation:\n{conversation_text}\n\n"
            "Return only a valid JSON object with this structure:\n"
            '{\n'
            '  "title": "string",\n'
            '  "content": "string",\n'
            '  "keywords": ["string1", "string2", ...]\n'
            '}'
        )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, model.generate_content, prompt)
        
        # Parse JSON response
        response_text = response.text.strip()
        # Try to extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        parsed = json.loads(response_text)
        return parsed
    except Exception as e:
        print(f"Error analyzing conversation: {e}")
        return None

async def analyze_user_satisfaction(user_messages: list) -> dict:
    """Use AI to determine if user is satisfied or needs human support
    
    Args:
        user_messages: List of recent user messages to analyze together
    """
    try:
        # Combine messages for analysis
        combined_message = " ".join(user_messages)
        
        # Check for explicit human support requests first
        human_keywords = ['human', 'staff', 'real person', 'talk to someone', 'support agent', 'representative', 'speak to', 'talk to']
        if any(keyword in combined_message.lower() for keyword in human_keywords):
            print(f"🚨 Explicit human support request detected")
            return {
                "satisfied": False,
                "reason": "User explicitly requested human support",
                "confidence": 100,
                "wants_human": True
            }
        
        # Check if satisfaction analysis is enabled (saves API calls!)
        if not BOT_SETTINGS.get('satisfaction_analysis_enabled', True):
            print(f"ℹ️ Satisfaction analysis disabled - skipping")
            return {"satisfied": False, "reason": "Analysis disabled", "confidence": 0, "wants_human": False}
        
        # Check rate limit before making API call
        if not await check_rate_limit():
            print(f"⚠️ Skipping satisfaction analysis due to rate limit")
            return {"satisfied": False, "reason": "Rate limit", "confidence": 0, "wants_human": False}
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = (
            "Analyze the following user message(s) and determine if they are satisfied with the bot's response or need human support.\n\n"
            f"User message(s): \"{combined_message}\"\n\n"
            "Return a JSON object with this structure:\n"
            '{\n'
            '  "satisfied": true/false,\n'
            '  "reason": "brief explanation",\n'
            '  "confidence": 0-100,\n'
            '  "wants_human": true/false\n'
            '}\n\n'
            "Consider satisfied if:\n"
            "- They say thanks, thank you, appreciated, helpful, etc.\n"
            "- They confirm it worked or was resolved\n"
            "- They say they're good, all set, no problem, etc.\n\n"
            "Consider NOT satisfied if:\n"
            "- They ask follow-up questions\n"
            "- They express confusion or frustration\n"
            "- They say it didn't work or need more help\n\n"
            "IMPORTANT: Set wants_human to true ONLY if:\n"
            "- They EXPLICITLY ask for: human support, staff, real person, agent, representative, etc.\n"
            "- They use phrases like: 'talk to someone', 'speak to a person', 'need human help'\n"
            "\n"
            "DO NOT set wants_human to true just because:\n"
            "- They're unsatisfied or frustrated\n"
            "- They say 'that didn't work' or 'still not working'\n"
            "- They ask follow-up questions\n"
            "- They need more help (bot can provide another solution first)"
        )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, model.generate_content, prompt)
        track_api_call()  # Track successful API call
        
        # Parse JSON response
        response_text = response.text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        print(f"📊 Satisfaction analysis: {result.get('satisfied')} ({result.get('confidence')}% confidence) - {result.get('reason')}")
        return result
    except Exception as e:
        print(f"⚠ Error analyzing user satisfaction: {e}")
        # Default to needing human support if analysis fails
        return {"satisfied": False, "reason": "Analysis failed", "confidence": 0, "wants_human": False}

async def get_resolved_tag(forum_channel):
    """
    Find the 'Resolved' tag in a forum channel.
    Returns the tag object if found, None otherwise.
    """
    try:
        if not hasattr(forum_channel, 'available_tags'):
            return None
        
        # First, check if we have a specific tag ID set
        resolved_tag_id = BOT_SETTINGS.get('resolved_tag_id')
        if resolved_tag_id:
            # Convert to int (stored as string to prevent JavaScript precision loss)
            resolved_tag_id = int(resolved_tag_id) if isinstance(resolved_tag_id, str) else resolved_tag_id
            for tag in forum_channel.available_tags:
                if tag.id == resolved_tag_id:
                    print(f"✓ Found resolved tag by ID: '{tag.name}' (ID: {tag.id})")
                    return tag
        
        # Fallback: Look for a tag with "resolved" or "solved" in the name (case-insensitive)
        for tag in forum_channel.available_tags:
            tag_name_lower = tag.name.lower()
            if 'resolved' in tag_name_lower or 'solved' in tag_name_lower:
                print(f"✓ Found resolved tag by name: '{tag.name}' (ID: {tag.id})")
                return tag
        
        print(f"⚠ No 'Resolved' or 'Solved' tag found in forum channel")
        return None
    except Exception as e:
        print(f"⚠ Error getting resolved tag: {e}")
        return None

async def get_unsolved_tag(forum_channel):
    """
    Find the 'Unsolved' tag in a forum channel.
    Returns the tag object if found, None otherwise.
    """
    try:
        if not hasattr(forum_channel, 'available_tags'):
            return None
        
        # First, check if we have a specific tag ID set
        unsolved_tag_id = BOT_SETTINGS.get('unsolved_tag_id')
        if unsolved_tag_id:
            # Convert to int (stored as string to prevent JavaScript precision loss)
            unsolved_tag_id = int(unsolved_tag_id) if isinstance(unsolved_tag_id, str) else unsolved_tag_id
            for tag in forum_channel.available_tags:
                if tag.id == unsolved_tag_id:
                    print(f"✓ Found unsolved tag by ID: '{tag.name}' (ID: {tag.id})")
                    return tag
        
        # Fallback: Look for a tag with "unsolved" or "open" in the name (case-insensitive)
        for tag in forum_channel.available_tags:
            tag_name_lower = tag.name.lower()
            if 'unsolved' in tag_name_lower or 'open' in tag_name_lower:
                print(f"✓ Found unsolved tag by name: '{tag.name}' (ID: {tag.id})")
                return tag
        
        print(f"⚠ No 'Unsolved' or 'Open' tag found in forum channel")
        return None
    except Exception as e:
        print(f"⚠ Error getting unsolved tag: {e}")
        return None

# --- PERIODIC DATA SYNC ---
@tasks.loop(hours=1)  # Sync every hour
async def sync_data_task():
    """Periodically sync data from the dashboard"""
    await fetch_data_from_api()
    # All data stored in memory (loaded from API) - no local files

@sync_data_task.before_loop
async def before_sync_task():
    await bot.wait_until_ready()

# --- BOT EVENTS ---
@tasks.loop(hours=24)  # Run daily
async def cleanup_old_solved_posts():
    """Background task to delete old solved/closed posts and posts open for 30+ days"""
    try:
        if 'your-vercel-app' in DATA_API_URL:
            return  # Skip if API not configured
        
        retention_days = BOT_SETTINGS.get('solved_post_retention_days', 30)
        open_post_retention_days = 30  # Delete posts open for 30+ days regardless of status
        print(f"\n🧹 Cleaning up old posts...")
        print(f"   - Solved/Closed posts older than {retention_days} days")
        print(f"   - Any posts open for {open_post_retention_days}+ days")
        
        forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(forum_api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    print(f"⚠ Failed to fetch posts for cleanup: {response.status}")
                    return
                
                all_posts = await response.json()
                now = datetime.now()
                deleted_count = 0
                
                for post in all_posts:
                    status = post.get('status', '')
                    post_id = post.get('id') or f"POST-{post.get('postId')}"
                    post_title = post.get('postTitle', 'Unknown')
                    should_delete = False
                    delete_reason = ""
                    
                    # Check 1: Delete Solved/Closed posts after retention period
                    if status in ['Solved', 'Closed']:
                        updated_at_str = post.get('updatedAt') or post.get('createdAt')
                        if updated_at_str:
                            try:
                                updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                                if updated_at.tzinfo:
                                    updated_at = updated_at.replace(tzinfo=None)
                                age_days = (now - updated_at).total_seconds() / 86400
                                if age_days > retention_days:
                                    should_delete = True
                                    delete_reason = f"solved {age_days:.1f} days ago"
                            except Exception as parse_error:
                                print(f"⚠ Error parsing post date: {parse_error}")
                                continue
                    
                    # Check 2: Delete ANY post open for 30+ days (regardless of status)
                    created_at_str = post.get('createdAt')
                    if created_at_str and not should_delete:
                        try:
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            if created_at.tzinfo:
                                created_at = created_at.replace(tzinfo=None)
                            age_days = (now - created_at).total_seconds() / 86400
                            if age_days > open_post_retention_days:
                                should_delete = True
                                delete_reason = f"open for {age_days:.1f} days"
                        except Exception as parse_error:
                            print(f"⚠ Error parsing post creation date: {parse_error}")
                            continue
                    
                    if should_delete:
                        print(f"🗑️ Deleting post ({delete_reason}): '{post_title}' (Status: {status})")
                        
                        # Delete from dashboard
                        delete_payload = {
                            'action': 'delete',
                            'postId': post_id
                        }
                        
                        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                        async with session.post(forum_api_url, json=delete_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as delete_response:
                            if delete_response.status == 200:
                                deleted_count += 1
                                print(f"✅ Deleted: '{post_title}'")
                            else:
                                print(f"⚠ Failed to delete '{post_title}': {delete_response.status}")
                
                if deleted_count > 0:
                    print(f"✅ Cleanup complete: Deleted {deleted_count} old post(s)")
                else:
                    print(f"✓ No old posts found to delete")
    
    except Exception as e:
        print(f"❌ Error in cleanup_old_solved_posts task: {e}")
        import traceback
        traceback.print_exc()

async def notify_support_channel_summary():
    """Send a summary of all high priority posts to the support channel"""
    try:
        support_channel_id = BOT_SETTINGS.get('support_notification_channel_id')
        if not support_channel_id:
            print("⚠ Support notification channel not configured")
            return
        
        # Convert to int (stored as string to prevent JavaScript precision loss)
        support_channel_id = int(support_channel_id) if isinstance(support_channel_id, str) else support_channel_id
        
        support_channel = bot.get_channel(support_channel_id)
        if not support_channel:
            print(f"⚠ Support notification channel {support_channel_id} not found")
            return
        
        # Fetch all high priority posts from API
        if 'your-vercel-app' in DATA_API_URL:
            return
        
        forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
        
        async with aiohttp.ClientSession() as session:
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            async with session.get(forum_api_url, headers=headers) as response:
                if response.status != 200:
                    print(f"⚠ Failed to fetch posts for notification: {response.status}")
                    return
                
                all_posts = await response.json()
                
                # Filter for high priority posts
                high_priority_posts = [p for p in all_posts if p.get('status') == 'High Priority']
                
                if not high_priority_posts:
                    print("✓ No high priority posts to notify about")
                    return
                
                # Build the message content
                support_role_id = BOT_SETTINGS.get('support_role_id')
                # Note: support_role_id is stored as string to prevent JavaScript precision loss
                message_content = f"<@&{support_role_id}>\n\n" if support_role_id else ""
                message_content += "**High Priority Posts:**\n\n"
                
                # Add each post as a numbered list item
                for i, post in enumerate(high_priority_posts[:10], 1):  # Limit to 10
                    thread_id = post.get('postId')
                    post_title = post.get('postTitle', 'Unknown Post')
                    post_url = f"https://discord.com/channels/{DISCORD_GUILD_ID}/{thread_id}"
                    message_content += f"{i}. [{post_title}]({post_url})\n"
                
                if len(high_priority_posts) > 10:
                    message_content += f"\n*... and {len(high_priority_posts) - 10} more*"
                
                # Send the message
                await support_channel.send(message_content)
                print(f"✅ Sent high priority summary to support channel ({len(high_priority_posts)} posts)")
    
    except Exception as e:
        print(f"❌ Error sending support notification summary: {e}")
        import traceback
        traceback.print_exc()

# REMOVED: Local backups disabled - all data stored in Vercel KV API only
# Users can download backups anytime with /export_data command

@tasks.loop(hours=1)  # Default interval, can be changed dynamically
async def check_old_posts():
    """Background task to check for old unsolved posts and escalate them"""
    try:
        if 'your-vercel-app' in DATA_API_URL:
            return  # Skip if API not configured
        
        inactivity_threshold = BOT_SETTINGS.get('post_inactivity_hours', 12)
        interval_hours = BOT_SETTINGS.get('high_priority_check_interval_hours', 1.0)
        print(f"\n🔍 Checking for old unsolved posts (>{inactivity_threshold} hours, checking every {interval_hours}h)...")
        
        forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(forum_api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    print(f"⚠ Failed to fetch posts for age check: {response.status}")
                    return
                
                all_posts = await response.json()
                now = datetime.now()
                escalated_count = 0
                
                for post in all_posts:
                    status = post.get('status', '')
                    
                    # Skip if already solved, closed, or already escalated
                    if status in ['Solved', 'Closed', 'High Priority']:
                        continue
                    
                    # Check post age
                    created_at_str = post.get('createdAt')
                    if not created_at_str:
                        continue
                    
                    try:
                        # Parse ISO timestamp
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        # Remove timezone info for comparison
                        if created_at.tzinfo:
                            created_at = created_at.replace(tzinfo=None)
                        
                        age_hours = (now - created_at).total_seconds() / 3600
                        
                        # Get inactivity threshold from settings (default: 12 hours)
                        inactivity_threshold = BOT_SETTINGS.get('post_inactivity_hours', 12)
                        
                        if age_hours > inactivity_threshold:
                            # Post is older than threshold and not solved
                            thread_id = post.get('postId')
                            post_title = post.get('postTitle', 'Unknown')
                            
                            print(f"⚠ Found old post: '{post_title}' ({age_hours:.1f} hours old, threshold: {inactivity_threshold}h)")
                            
                            # Update status to High Priority
                            post['status'] = 'High Priority'
                            
                            update_payload = {
                                'action': 'update',
                                'post': post
                            }
                            
                            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                            async with session.post(forum_api_url, json=update_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as update_response:
                                if update_response.status == 200:
                                    print(f"✅ Escalated to High Priority: '{post_title}'")
                                    escalated_count += 1
                                    
                                    # Try to ping support in the thread
                                    try:
                                        thread_channel = bot.get_channel(int(thread_id))
                                        if thread_channel and thread_id not in escalated_threads:
                                            escalate_embed = discord.Embed(
                                                title="🚨 Support Team Notified",
                                                description=f"This post has been open for {int(age_hours)} hours. Our support team has been pinged and will help you soon.",
                                                color=0xE74C3C  # Red for high priority
                                            )
                                            escalate_embed.set_footer(text="Revolution Macro Support • Auto-escalation")
                                            
                                            await thread_channel.send(embed=escalate_embed)
                                            escalated_threads.add(thread_id)  # Mark as escalated
                                            print(f"📢 Sent high priority notification to thread {thread_id}")
                                    except Exception as ping_error:
                                        print(f"⚠ Could not send notification to thread {thread_id}: {ping_error}")
                                else:
                                    print(f"❌ Failed to escalate post '{post_title}': {update_response.status}")
                    
                    except Exception as parse_error:
                        print(f"⚠ Error parsing timestamp for post: {parse_error}")
                        continue
                
                if escalated_count > 0:
                    print(f"✅ Escalated {escalated_count} old post(s) to High Priority")
                    # Send summary of all high priority posts to support channel
                    await notify_support_channel_summary()
                else:
                    print(f"✓ No old posts found needing escalation")
    
    except Exception as e:
        print(f"❌ Error in check_old_posts task: {e}")
        import traceback
        traceback.print_exc()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('-------------------')
    
    # Bot settings are now loaded from API during fetch_data_from_api()
    # This ensures settings persist across deployments!
    
    print(f'📡 API Configuration:')
    if 'your-vercel-app' in DATA_API_URL:
        print(f'   ⚠ DATA_API_URL not configured (using placeholder)')
        print(f'   ℹ Set DATA_API_URL in .env file to connect to dashboard')
    else:
        print(f'   ✓ DATA_API_URL: {DATA_API_URL}')
    print(f'📺 Forum Channel ID: {SUPPORT_FORUM_CHANNEL_ID}')
    print('-------------------')
    
    # Initial data sync - loads everything into memory from API
    await fetch_data_from_api()
    
    # Start periodic sync
    sync_data_task.start()
    
    # Start old post check task
    if not check_old_posts.is_running():
        check_old_posts.start()
        print("✓ Started background task: check_old_posts (runs every hour)")
    
    # Start cleanup task for old solved posts
    if not cleanup_old_solved_posts.is_running():
        cleanup_old_solved_posts.start()
        print("✓ Started background task: cleanup_old_solved_posts (runs daily)")
    
    # No local backups - all data in Vercel KV (use /export_data to download anytime)
    
    try:
        # DON'T clear commands on every startup - this causes CommandNotFound errors
        # Only sync commands to update any changes
        guild = discord.Object(id=DISCORD_GUILD_ID)
        
        print(f'🔄 Syncing slash commands to guild {DISCORD_GUILD_ID}...')
        
        # Sync commands to specific guild for instant availability
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f'✓ Slash commands synced to guild {DISCORD_GUILD_ID} ({len(synced)} commands).')
        print(f'   Commands are now available in the server!')
        print(f'   💡 If you see duplicates, use /fix_duplicate_commands')
        print(f'   ⚠ NOTE: If you don\'t see commands, re-invite bot with "applications.commands" scope!')
    except Exception as e:
        print(f'⚠ Failed to sync commands: {e}')
        print(f'   This usually means the bot lacks "applications.commands" permission.')
        print(f'   Re-invite the bot using the OAuth2 URL Generator with both "bot" and "applications.commands" scopes.')
    
    # Verify bot is watching the correct channel and list all forum channels
    try:
        forum_channel = bot.get_channel(SUPPORT_FORUM_CHANNEL_ID)
        all_forum_channels = []
        
        # Find all forum channels bot can see
        for guild in bot.guilds:
            for channel in guild.channels:
                if hasattr(channel, 'id'):
                    channel_type = type(channel).__name__
                    # Check if it's a forum channel or if it's our target channel
                    if 'forum' in channel_type.lower() or channel.id == SUPPORT_FORUM_CHANNEL_ID:
                        all_forum_channels.append({
                            'name': channel.name,
                            'id': channel.id,
                            'type': channel_type,
                            'category_id': getattr(channel, 'category_id', None)
                        })
        
        if forum_channel:
            channel_type = type(forum_channel).__name__
            print(f'✓ Monitoring channel: {forum_channel.name} (ID: {SUPPORT_FORUM_CHANNEL_ID})')
            print(f'✓ Channel type: {channel_type}')
            
            # Check if it's actually a forum channel or a category
            if 'category' in channel_type.lower():
                print(f'\n⚠⚠⚠ WARNING: Channel ID {SUPPORT_FORUM_CHANNEL_ID} is a CATEGORY, not a forum channel!')
                print(f'⚠ Forum posts are created in FORUM CHANNELS under this category.')
                print(f'⚠ Bot will check if forum posts are in this category.')
            elif 'forum' in channel_type.lower():
                print(f'✓ Channel is a forum channel - ready to detect posts!')
            else:
                print(f'⚠ Channel type might not be a forum channel - may not work correctly!')
            
            if all_forum_channels:
                print(f'\n📋 All forum channels bot can access:')
                for fc in all_forum_channels:
                    match_marker = ' ← CURRENT' if fc['id'] == SUPPORT_FORUM_CHANNEL_ID else ''
                    category_info = f" (in category {fc['category_id']})" if fc['category_id'] else ""
                    print(f'   - {fc["name"]} (ID: {fc["id"]}, Type: {fc["type"]}){category_info}{match_marker}')
        else:
            print(f'\n⚠⚠⚠ CRITICAL: Could not find channel with ID: {SUPPORT_FORUM_CHANNEL_ID}')
            print(f'⚠ Make sure:')
            print(f'   1. Channel ID in .env is correct')
            print(f'   2. Bot has permission to view this channel')
            print(f'   3. Bot is in the same server as the channel')
            
            if all_forum_channels:
                print(f'\n📋 Available FORUM channels bot CAN see (use one of these IDs):')
                for fc in all_forum_channels:
                    print(f'   - {fc["name"]} (ID: {fc["id"]}, Type: {fc["type"]})')
            else:
                print(f'\n📋 All channels bot CAN see:')
                for guild in bot.guilds:
                    print(f'   Server: {guild.name}')
                    for channel in guild.channels:
                        if hasattr(channel, 'id') and hasattr(channel, 'name'):
                            channel_type = type(channel).__name__
                            print(f'      - {channel.name} (ID: {channel.id}, Type: {channel_type})')
    except Exception as e:
        print(f'⚠ Error checking forum channel: {e}')
        import traceback
        traceback.print_exc()
    
    print('Bot is ready and listening for new forum posts.')
    print('-------------------')

async def send_forum_post_to_api(thread, owner_name, owner_id, owner_avatar_url, initial_message):
    """Send forum post data to the dashboard API with full Discord information"""
    # Skip API call if URL is still the placeholder
    if 'your-vercel-app' in DATA_API_URL:
        print("ℹ Skipping forum post sync - Vercel URL not configured.")
        return  # Silently skip if API not configured
    
    try:
        forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
        print(f"🔗 Sending forum post to: {forum_api_url}")
        
        # Get thread creation time
        thread_created = thread.created_at if hasattr(thread, 'created_at') else datetime.now()
        
        # Build full avatar URL if not already a full URL
        if owner_avatar_url and not owner_avatar_url.startswith('http'):
            avatar_url = f'https://cdn.discordapp.com/avatars/{owner_id}/{owner_avatar_url}.png' if owner_id else owner_avatar_url
        elif not owner_avatar_url and owner_id:
            avatar_url = f'https://cdn.discordapp.com/avatars/{owner_id}/default.png'
        else:
            avatar_url = owner_avatar_url or f'https://cdn.discordapp.com/embed/avatars/0.png'
        
        post_data = {
            'action': 'create',
            'post': {
                'id': f'POST-{thread.id}',
                'user': {
                    'username': owner_name,
                    'id': str(owner_id) if owner_id else str(thread.id),
                    'avatarUrl': avatar_url
                },
                'postTitle': thread.name,
                'status': 'Unsolved',  # All new posts start as Unsolved
                'tags': [],
                'createdAt': thread_created.isoformat() if hasattr(thread_created, 'isoformat') else datetime.now().isoformat(),
                'forumChannelId': str(thread.parent_id),
                'postId': str(thread.id),
                'conversation': [
                    {
                        'author': 'User',
                        'content': initial_message,
                        'timestamp': datetime.now().isoformat()
                    }
                ]
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(forum_api_url, json=post_data, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print(f"✓ Forum post sent to dashboard: '{thread.name}' by {owner_name}")
                else:
                    text = await response.text()
                    print(f"⚠ Failed to send forum post to API: Status {response.status}")
                    print(f"   Response: {text[:200]}")
                    print(f"   API URL: {forum_api_url}")
                    print(f"   Request body: {json.dumps(post_data)[:200]}")
    except aiohttp.ClientError as e:
        print(f"⚠ Network error sending forum post to API: {type(e).__name__}: {str(e)}")
        print(f"   API URL attempted: {forum_api_url}")
    except Exception as e:
        print(f"⚠ Error sending forum post to API: {type(e).__name__}: {str(e)}")
        print(f"   API URL attempted: {forum_api_url}")

@bot.event
async def on_thread_create(thread):
    """Handle new forum posts (threads created in forum channels)"""
    print(f"\n🔍 THREAD CREATED EVENT FIRED")
    print(f"   Thread name: '{thread.name}'")
    print(f"   Thread ID: {thread.id}")
    
    # Check if this is a forum channel thread
    if not hasattr(thread, 'parent_id') or not thread.parent_id:
        print(f"⚠ Thread doesn't have parent_id attribute. Skipping.")
        return
    
    thread_parent_id = int(thread.parent_id)
    expected_channel_id = int(SUPPORT_FORUM_CHANNEL_ID)
    
    print(f"   Thread parent_id: {thread_parent_id}")
    print(f"   Expected channel ID: {expected_channel_id}")
    
    # Get the parent channel to check its type and category
    parent_channel = None
    should_process = False
    
    try:
        parent_channel = bot.get_channel(thread_parent_id)
        if parent_channel:
            channel_type = type(parent_channel).__name__
            print(f"   Parent channel: {parent_channel.name} (Type: {channel_type})")
            
            # Check if parent channel's ID matches (direct forum channel match)
            if thread_parent_id == expected_channel_id:
                print(f"✅ MATCH! Forum post is in forum channel {expected_channel_id}")
                should_process = True
            # Check if parent channel is in a category that matches
            elif hasattr(parent_channel, 'category_id') and parent_channel.category_id:
                category_id = int(parent_channel.category_id)
                print(f"   Parent channel category_id: {category_id}")
                
                # Get the category channel to verify
                category_channel = bot.get_channel(category_id)
                if category_channel:
                    category_type = type(category_channel).__name__
                    print(f"   Category channel: {category_channel.name} (Type: {category_type}, ID: {category_id})")
                    
                    if category_id == expected_channel_id:
                        print(f"✅ MATCH! Forum post is in a forum channel within category {expected_channel_id}")
                        should_process = True
                    else:
                        print(f"⚠ Category ID ({category_id}) doesn't match expected ({expected_channel_id})")
                else:
                    print(f"⚠ Could not fetch category channel")
            else:
                print(f"⚠ Parent channel ID ({thread_parent_id}) doesn't match forum channel ID ({expected_channel_id})")
                print(f"⚠ Parent channel has no category_id or category doesn't match")
        else:
            print(f"⚠ Could not fetch parent channel with ID {thread_parent_id}")
    except Exception as e:
        print(f"⚠ Error checking parent channel: {e}")
        import traceback
        traceback.print_exc()
    
    if not should_process:
        print(f"⚠ This thread will be ignored. Use the FORUM CHANNEL ID (not category ID) or update to accept this category!")
        return
    
    print(f"✅ Processing forum post: '{thread.name}'")
    
    # LOCK: Check if this thread is currently being processed RIGHT NOW
    if thread.id in processing_threads:
        print(f"🔒 Thread {thread.id} is ALREADY being processed, skipping duplicate")
        return
    
    # Check if we've already fully processed this thread
    if thread.id in processed_threads:
        print(f"⚠ Thread {thread.id} already processed, skipping duplicate event")
        return
    
    # LOCK THIS THREAD IMMEDIATELY (before any async operations that could cause race condition)
    processing_threads.add(thread.id)
    print(f"🔒 Locked thread {thread.id} for processing")
    
    # Double-check by looking for bot messages already in thread
    try:
        bot_messages = [msg async for msg in thread.history(limit=10) if msg.author == bot.user]
        if bot_messages:
            print(f"⚠ Thread {thread.id} already has {len(bot_messages)} bot message(s), skipping duplicate processing")
            processed_threads.add(thread.id)
            processing_threads.remove(thread.id)  # Release lock
            return
    except Exception as check_error:
        print(f"⚠ Could not check for existing bot messages: {check_error}")
    
    # Mark as processed to prevent future duplicates
    processed_threads.add(thread.id)

    # Safely get owner information
    owner_name = "Unknown"
    owner_mention = "there"
    owner_id = None
    owner_avatar_url = None
    
    try:
        if thread.owner:
            owner_name = getattr(thread.owner, 'name', 'Unknown')
            owner_mention = getattr(thread.owner, 'mention', 'there')
            owner_id = getattr(thread.owner, 'id', None)
            owner_avatar_url = str(getattr(thread.owner, 'avatar', None)) if hasattr(thread.owner, 'avatar') else None
        elif hasattr(thread, 'owner_id') and thread.owner_id:
            try:
                owner = await bot.fetch_user(thread.owner_id)
                owner_name = owner.name
                owner_mention = owner.mention
                owner_id = owner.id
                owner_avatar_url = str(owner.avatar) if owner.avatar else None
            except Exception:
                pass
    except Exception as e:
        print(f"⚠ Could not get thread owner: {e}")

    print(f"New forum post created: '{thread.name}' by {owner_name}")
    
    # Wait a moment for Discord to process the thread
    await asyncio.sleep(1)
    
    # Get the initial message from thread history
    history = [message async for message in thread.history(limit=1, oldest_first=True)]
    if not history:
        print(f"⚠ No initial message found in thread {thread.id}")
        return

    initial_msg = history[0]
    initial_message = initial_msg.content
    
    # Check for attachments (images, videos, files)
    has_attachments = len(initial_msg.attachments) > 0
    attachment_types = []
    if has_attachments:
        for attachment in initial_msg.attachments:
            if attachment.content_type:
                if "image" in attachment.content_type:
                    attachment_types.append("image")
                    initial_message += f"\n[User attached an image: {attachment.filename}]"
                elif "video" in attachment.content_type:
                    attachment_types.append("video")
                    initial_message += f"\n[User attached a video: {attachment.filename}]"
                else:
                    attachment_types.append("file")
                    initial_message += f"\n[User attached a file: {attachment.filename}]"
            else:
                attachment_types.append("file")
                initial_message += f"\n[User attached a file: {attachment.filename}]"
        print(f"📎 User attached {len(initial_msg.attachments)} file(s): {', '.join(attachment_types)}")
    
    # Send greeting embed AFTER we have the initial message (Discord requirement) - SHORTER
    greeting_embed = discord.Embed(
        title="👋 Revolution Macro Support",
        description=f"Hi {owner_mention}! Looking for an answer...",
        color=0x5865F2
    )
    greeting_embed.set_footer(text="Revolution Macro AI")
    
    try:
        await thread.send(embed=greeting_embed)
    except discord.errors.Forbidden as e:
        print(f"⚠ Could not send greeting (Discord restriction): {e}")
        # Continue anyway - the important part is answering the question
    user_question = f"{thread.name}\n{initial_message}"
    
    # Send forum post to dashboard API
    await send_forum_post_to_api(thread, owner_name, owner_id or thread.id, owner_avatar_url, initial_message)

    # --- LOGIC FLOW ---
    # Track which response type we used for satisfaction analysis
    thread_id = thread.id
    
    # Check auto-responses first
    auto_response = get_auto_response(user_question)
    bot_response_text = None
    
    # Download images if user attached them (for Gemini vision)
    image_data = None
    if has_attachments and "image" in attachment_types:
        print(f"🖼️ User attached {attachment_types.count('image')} image(s) - downloading for analysis...")
        image_data = await download_images_for_gemini(initial_msg.attachments)
        if image_data:
            print(f"✅ Downloaded {len(image_data)} image(s) for Gemini vision analysis")
    
    # If user uploaded image with NO text or very little text, enhance with image analysis
    text_only = initial_msg.content.strip() if initial_msg.content else ""
    if image_data and len(text_only) < 10:
        print(f"📸 Image-only post detected (minimal text) - analyzing image to understand issue...")
        # Ask Gemini what's in the image to enhance the query
        try:
            import google.generativeai as genai
            vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            image_analysis_prompt = "Describe what you see in this image. What issue or problem does it show? Be brief (2-3 sentences)."
            
            # Create content with images
            content_parts = []
            for img in image_data:
                content_parts.append(img)
            content_parts.append(image_analysis_prompt)
            
            loop = asyncio.get_event_loop()
            analysis = await loop.run_in_executor(None, lambda: vision_model.generate_content(content_parts))
            image_description = analysis.text
            
            # Enhance the user question with what we see in the image
            user_question = f"{thread.name}\n{initial_message}\n\nWhat I see in the image: {image_description}"
            print(f"🔍 Image analysis: {image_description[:100]}...")
        except Exception as e:
            print(f"⚠ Error analyzing image: {e}")
    
    # If user attached videos or non-image files, escalate to human
    needs_human_review = False
    if has_attachments and ("video" in attachment_types or len([t for t in attachment_types if t not in ["image"]]) > 0):
        print(f"🎥 User attached video/file - escalating to human support for review")
        needs_human_review = True
    
    # Handle immediate human escalation (videos or non-image files)
    if needs_human_review:
        escalated_threads.add(thread_id)
        thread_response_type[thread_id] = 'human'
        
        human_escalation_embed = discord.Embed(
            title="👨‍💼 Support Team Notified",
            description="I see you've included video/file attachments. Our support team will review them and help you directly!",
            color=0xE67E22
        )
        human_escalation_embed.add_field(
            name="⏰ Response Time",
            value="Usually under 24 hours",
            inline=True
        )
        human_escalation_embed.add_field(
            name="📎 Attachments Received",
            value=f"{len(initial_msg.attachments)} file(s)",
            inline=True
        )
        human_escalation_embed.set_footer(text="Revolution Macro Support Team")
        await thread.send(embed=human_escalation_embed)
        
        # Clean up images if we downloaded any
        if image_data:
            for img in image_data:
                img.close()
            print(f"🗑️ Cleaned up {len(image_data)} image(s) from memory")
        
        # Update forum post status
        await update_forum_post_status(thread_id, 'Human Support')
        print(f"✅ Thread {thread_id} escalated to human support (video/file attachments)")
        return  # Exit early - no bot response needed
    
    if auto_response:
        # Send auto-response as professional embed
        auto_embed = discord.Embed(
            title="⚡ Quick Answer",
            description=auto_response,
            color=0x5865F2  # Discord blurple for instant responses
        )
        auto_embed.add_field(
            name="💡 Did this help?",
            value="Let me know by clicking a button below!",
            inline=False
        )
        auto_embed.set_footer(text="Revolution Macro • Instant Answer")
        
        # Create conversation for button handler
        conversation = [
            {
                'author': 'User',
                'content': initial_message,
                'timestamp': datetime.now().isoformat()
            },
            {
                'author': 'Bot',
                'content': auto_response,
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        # Add satisfaction buttons
        button_view = SatisfactionButtons(thread_id, conversation, 'auto')
        await thread.send(embed=auto_embed, view=button_view)
        bot_response_text = auto_response
        thread_response_type[thread_id] = 'auto'  # Track that we gave an auto-response
        print(f"⚡ Responded to '{thread.name}' with instant auto-response.")
    else:
        relevant_docs = find_relevant_rag_entries(user_question)
        
        # AGGRESSIVE RAG USAGE - Use knowledge base if we have ANYTHING at all
        # Prefer RAG over general AI responses
        confident_docs = []
        
        # Prepare query words
        query_words = set(user_question.lower().split())
        # Remove only common stopwords, keep all actual keywords (including short ones like vpn, rbc, api, ip)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'be'}
        query_words = {word for word in query_words if word not in stopwords}
        
        print(f"🔍 Searching for matches with query words: {query_words}")
        print(f"🔍 Total RAG entries available: {len(RAG_DATABASE)}")
        if RAG_DATABASE:
            print(f"🔍 RAG entry examples:")
            for entry in RAG_DATABASE[:3]:
                print(f"   - '{entry.get('title', 'Unknown')}' | Keywords: {entry.get('keywords', [])}")
        
        # Score ALL entries and use ANY that have matches
        all_scored_entries = []
        for entry in RAG_DATABASE:
            score = 0
            entry_title = entry.get('title', '').lower()
            entry_keywords = ' '.join(entry.get('keywords', [])).lower()
            entry_content = entry.get('content', '').lower()
            
            # More aggressive matching - check if keywords are substrings too
            for word in query_words:
                # Exact word matches in title (highest priority)
                if f" {word} " in f" {entry_title} " or entry_title.startswith(word) or entry_title.endswith(word):
                    score += 5
                # Partial match in title
                elif word in entry_title:
                    score += 3
                    
                # Exact word matches in keywords (high priority)
                if f" {word} " in f" {entry_keywords} " or entry_keywords.startswith(word) or entry_keywords.endswith(word):
                    score += 4
                # Partial match in keywords
                elif word in entry_keywords:
                    score += 2
                    
                # Any match in content
                if word in entry_content:
                    score += 1
            
            if score > 0:
                all_scored_entries.append({'entry': entry, 'score': score})
                print(f"   ✓ Match found: '{entry.get('title', 'Unknown')}' (score: {score})")
        
        # Sort by score and use top matches
        all_scored_entries.sort(key=lambda x: x['score'], reverse=True)
        confident_docs = [item['entry'] for item in all_scored_entries[:5]]  # Use top 5 matches
        
        if not confident_docs:
            print(f"⚠ No RAG entries had any keyword matches")
            print(f"   This means no entry in your knowledge base contains any of the words: {query_words}")

        if confident_docs:
            # Found matches in knowledge base - use top entries
            num_to_use = min(3, len(confident_docs))  # Use up to 3 best matches
            bot_response_text = await generate_ai_response(user_question, confident_docs[:num_to_use], image_data)
            
            # Send AI response - SHORTER AND SIMPLER
            ai_embed = discord.Embed(
                title="✅ Solution",
                description=bot_response_text,
                color=0x2ECC71
            )
            ai_embed.add_field(
                name="💬 Did this help?",
                value="Let me know by clicking a button below!",
                inline=False
            )
            ai_embed.set_footer(text="Revolution Macro AI • From Knowledge Base")
            
            # Create conversation for button handler
            conversation = [
                {
                    'author': 'User',
                    'content': initial_message,
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'author': 'Bot',
                    'content': bot_response_text,
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            # Add satisfaction buttons
            button_view = SatisfactionButtons(thread_id, conversation, 'ai')
            await thread.send(embed=ai_embed, view=button_view)
            thread_response_type[thread_id] = 'ai'  # Track that we gave an AI response
            
            # Show which entries were used in terminal
            print(f"✅ Responded to '{thread.name}' with RAG-based answer using {num_to_use} knowledge base {'entry' if num_to_use == 1 else 'entries'}:")
            for i, doc in enumerate(confident_docs[:num_to_use], 1):
                print(f"   {i}. '{doc.get('title', 'Unknown')}'")
        else:
            # No confident match - generate AI response using general Revolution Macro knowledge
            print(f"⚠ No confident RAG match found. Attempting AI response with general knowledge...")
            
            try:
                # Build context from auto-responses to give AI some Revolution Macro knowledge
                auto_response_context = []
                for auto_resp in AUTO_RESPONSES:
                    auto_response_context.append(f"- {auto_resp.get('name', '')}: {auto_resp.get('responseText', '')}")
                
                context_info = "\n".join(auto_response_context) if auto_response_context else "No additional context available."
                
                # Generate AI response with general Revolution Macro context
                # Use custom system prompt as base if available
                base_instruction = SYSTEM_PROMPT_TEXT if SYSTEM_PROMPT_TEXT else SYSTEM_PROMPT
                
                model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=base_instruction)
                
                general_prompt = (
                    "Revolution Macro is a game automation tool.\n\n"
                    
                    "FEATURES:\n"
                    "- Auto farming/gathering\n"
                    "- Smart navigation\n"
                    "- Auto-deposit\n"
                    "- License system\n\n"
                    
                    f"USER'S QUESTION:\n{user_question}\n\n"
                    
                    "ANSWER RULES:\n"
                    "1. Use SIMPLE words\n"
                    "2. Keep it SHORT (3 sentences MAXIMUM)\n"
                    "3. Use numbered steps if needed\n"
                    "4. NO long explanations\n\n"
                    
                    "If you're not sure, keep it simple and suggest they wait for support team."
                )
                
                loop = asyncio.get_event_loop()
                ai_response = await loop.run_in_executor(None, model.generate_content, general_prompt)
                bot_response_text = ai_response.text
                
                # Send general AI response (SHORTER, SIMPLER)
                general_ai_embed = discord.Embed(
                    title="💡 Here's What I Found",
                    description=bot_response_text,
                    color=0x5865F2
                )
                general_ai_embed.add_field(
                    name="💬 Did this help?",
                    value="Let me know by clicking a button below!",
                    inline=False
                )
                general_ai_embed.set_footer(text="Revolution Macro AI")
                
                # Create conversation for button handler
                conversation = [
                    {
                        'author': 'User',
                        'content': initial_message,
                        'timestamp': datetime.now().isoformat()
                    },
                    {
                        'author': 'Bot',
                        'content': bot_response_text,
                        'timestamp': datetime.now().isoformat()
                    }
                ]
                
                # Add satisfaction buttons
                button_view = SatisfactionButtons(thread_id, conversation, 'ai')
                await thread.send(embed=general_ai_embed, view=button_view)
                thread_response_type[thread_id] = 'ai'  # Track that we gave an AI response
                print(f"💡 Responded to '{thread.name}' with Revolution Macro AI assistance (no specific RAG match).")
                
            except Exception as e:
                print(f"⚠ Error generating general AI response: {e}")
                # Fallback: shorter message
                bot_response_text = "Not sure about this. Can you give more details or wait for our support team?"
                
                fallback_embed = discord.Embed(
                    title="🤔 Need More Info",
                    description=bot_response_text,
                    color=0xF39C12
                )
                fallback_embed.set_footer(text="Revolution Macro")
                
                # Create conversation for button handler
                conversation = [
                    {
                        'author': 'User',
                        'content': initial_message,
                        'timestamp': datetime.now().isoformat()
                    },
                    {
                        'author': 'Bot',
                        'content': bot_response_text,
                        'timestamp': datetime.now().isoformat()
                    }
                ]
                
                # Add satisfaction buttons
                button_view = SatisfactionButtons(thread_id, conversation, 'ai')
                await thread.send(embed=fallback_embed, view=button_view)
                thread_response_type[thread_id] = 'ai'  # Track as AI attempt
                print(f"⚠ Sent fallback response for '{thread.name}' (AI generation failed).")
    
        # Update forum post in API with bot response (must include all post data for full update)
        if bot_response_text and 'your-vercel-app' not in DATA_API_URL:
            print(f"🔗 Updating forum post with bot response...")
            try:
                # Determine status based on response type
                # Status is "AI Response" since we always try to help with AI now (human escalation only happens if user is unsatisfied)
                post_status = 'AI Response'
                
                forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
                
                # Get full post data (include user info, title, etc.)
                post_update = {
                    'action': 'update',
                    'post': {
                        'id': f'POST-{thread.id}',
                        'user': {
                            'username': owner_name,
                            'id': str(owner_id) if owner_id else str(thread.id),
                            'avatarUrl': f'https://cdn.discordapp.com/avatars/{owner_id}/default.png' if owner_id else f'https://cdn.discordapp.com/embed/avatars/0.png'
                        },
                        'postTitle': thread.name,
                        'status': post_status,
                        'tags': [],
                        'createdAt': (thread.created_at.isoformat() if hasattr(thread.created_at, 'isoformat') else datetime.now().isoformat()),
                        'forumChannelId': str(thread.parent_id),
                        'postId': str(thread.id),
                        'conversation': [
                            {
                                'author': 'User',
                                'content': initial_message,
                                'timestamp': datetime.now().isoformat()
                            },
                            {
                                'author': 'Bot',
                                'content': bot_response_text,
                                'timestamp': datetime.now().isoformat()
                            }
                        ]
                    }
                }
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(forum_api_url, json=post_update, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            print(f"✓ Updated forum post with bot response in dashboard API")
                        else:
                            text = await response.text()
                            print(f"⚠ Failed to update forum post: Status {response.status}, Response: {text[:200]}")
                            print(f"   API URL: {forum_api_url}")
                            print(f"   Request body: {json.dumps(post_update)[:200]}")
            except Exception as e:
                print(f"⚠ Error updating forum post with bot response: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    # Apply "Unsolved" tag to new forum post
    try:
        parent_channel = bot.get_channel(thread.parent_id)
        if parent_channel and hasattr(parent_channel, 'available_tags'):
            unsolved_tag = await get_unsolved_tag(parent_channel)
            if unsolved_tag:
                # Get current tags and add unsolved tag if not already present
                current_tags = list(thread.applied_tags) if hasattr(thread, 'applied_tags') else []
                if unsolved_tag not in current_tags:
                    current_tags.append(unsolved_tag)
                    await thread.edit(applied_tags=current_tags)
                    print(f"🏷️ Applied '{unsolved_tag.name}' tag to new thread {thread.id}")
                else:
                    print(f"ℹ️ Thread {thread.id} already has '{unsolved_tag.name}' tag")
            else:
                print(f"ℹ️ No 'Unsolved' tag available in forum channel")
    except Exception as tag_error:
        print(f"⚠ Could not apply unsolved tag: {tag_error}")
    finally:
        # Clean up images from memory if we downloaded any
        if 'image_data' in locals() and image_data:
            try:
                for img in image_data:
                    img.close()
                print(f"🗑️ Final cleanup: Released {len(image_data)} image(s) from memory")
            except Exception as cleanup_error:
                print(f"⚠ Error cleaning up images: {cleanup_error}")
        
        # ALWAYS release the processing lock
        if thread.id in processing_threads:
            processing_threads.remove(thread.id)
            print(f"🔓 Released lock for thread {thread.id}")

@bot.event
async def on_message(message):
    """Listen for new messages in threads and update forum posts in real-time"""
    # Only process messages in threads within our forum channel or category
    if not message.channel or not hasattr(message.channel, 'parent_id') or not message.channel.parent_id:
        await bot.process_commands(message)
        return
    
    # Check if message is in a thread from our forum channel or category
    thread_parent_id = int(message.channel.parent_id) if message.channel.parent_id else None
    expected_channel_id = int(SUPPORT_FORUM_CHANNEL_ID)
    
    should_process = False
    
    # Direct match
    if thread_parent_id == expected_channel_id:
        should_process = True
    # Check if parent channel is in matching category
    else:
        try:
            parent_channel = bot.get_channel(thread_parent_id)
            if parent_channel and hasattr(parent_channel, 'category_id') and parent_channel.category_id:
                if int(parent_channel.category_id) == expected_channel_id:
                    should_process = True
        except Exception:
            pass
    
    if not should_process:
        await bot.process_commands(message)
        return
    
    # Track bot messages too, but don't analyze them
    is_bot_message = message.author == bot.user
    if is_bot_message:
        print(f"🤖 Bot message in thread {message.channel.id}: {message.content[:50] if message.content else '[embed only]'}")
    
    # Update forum post with new message in real-time
    if 'your-vercel-app' not in DATA_API_URL:
        try:
            thread = message.channel
            forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
            
            # Get user info with full Discord data
            user_name = message.author.display_name or message.author.name
            user_id = str(message.author.id)
            user_avatar = message.author.avatar
            avatar_url = f'https://cdn.discordapp.com/avatars/{user_id}/{user_avatar}.png' if user_avatar else f'https://cdn.discordapp.com/avatars/{user_id}/default.png'
            
            # Fetch current post to update conversation
            async with aiohttp.ClientSession() as session:
                # Get current post
                async with session.get(forum_api_url) as get_response:
                    current_posts = []
                    if get_response.status == 200:
                        current_posts = await get_response.json()
                    
                    # Find matching post
                    matching_post = None
                    for post in current_posts:
                        if post.get('postId') == str(thread.id) or post.get('id') == f'POST-{thread.id}':
                            matching_post = post
                            break
                    
                    # Build updated conversation
                    # Extract embed content for bot messages
                    message_content = message.content
                    if is_bot_message and not message_content and message.embeds:
                        # Extract text from embed
                        embed = message.embeds[0]
                        embed_parts = []
                        if embed.title:
                            embed_parts.append(f"**{embed.title}**")
                        if embed.description:
                            embed_parts.append(embed.description)
                        # Add fields if any
                        for field in embed.fields[:2]:  # Limit to first 2 fields to keep it concise
                            if field.name and field.value:
                                embed_parts.append(f"{field.name}: {field.value}")
                        message_content = "\n".join(embed_parts) if embed_parts else '[Embed message]'
                    elif not message_content:
                        message_content = '[Embed message]'
                    
                    new_message = {
                        'author': 'Bot' if is_bot_message else 'User',
                        'content': message_content,
                        'timestamp': message.created_at.isoformat() if hasattr(message.created_at, 'isoformat') else datetime.now().isoformat()
                    }
                    
                    if matching_post:
                        # Update existing post
                        conversation = matching_post.get('conversation', [])
                        conversation.append(new_message)
                        
                        # Check if there was a bot response before this user message
                        has_bot_response = any(msg.get('author') == 'Bot' for msg in conversation)
                        print(f"📊 Conversation has {len(conversation)} messages, bot response: {has_bot_response}")
                        
                        # Start delayed satisfaction analysis if bot has already responded and this is a USER message
                        # BUT: Don't respond if thread has been escalated to human support
                        new_status = matching_post.get('status', 'Unsolved')
                        thread_id = thread.id
                        
                        # Check if thread is escalated to human - if so, bot stays silent
                        if thread_id in escalated_threads:
                            print(f"🔇 Thread {thread_id} escalated to human support - bot will not respond")
                            # Just update the conversation, don't trigger any bot responses
                            post_update = {
                                'action': 'update',
                                'post': {
                                    **matching_post,
                                    'conversation': conversation,
                                    'status': matching_post.get('status', 'Human Support')  # Keep as Human Support
                                }
                            }
                        elif not is_bot_message and has_bot_response and matching_post.get('status') not in ['Solved', 'Closed', 'High Priority']:
                            # Check if the user is staff/admin - if so, don't trigger satisfaction analysis
                            user_who_sent = message.author
                            is_staff_user = is_staff_or_admin(user_who_sent) if isinstance(user_who_sent, discord.Member) else False
                            
                            if is_staff_user:
                                print(f"ℹ User {user_who_sent.name} is staff/admin - skipping satisfaction analysis")
                                # Just update conversation, no bot response
                                post_update = {
                                    'action': 'update',
                                    'post': {
                                        **matching_post,
                                        'conversation': conversation,
                                        'status': new_status
                                    }
                                }
                            else:
                                # Cancel any existing timer for this thread
                                if thread_id in satisfaction_timers:
                                    satisfaction_timers[thread_id].cancel()
                                    print(f"⏰ Cancelled previous satisfaction timer for thread {thread_id}")
                                
                                # IMPORTANT: Update the conversation with user's reply BEFORE starting timer
                                post_update = {
                                    'action': 'update',
                                    'post': {
                                        **matching_post,
                                        'conversation': conversation,
                                        'status': new_status
                                    }
                                }
                                
                                # Create delayed analysis task (configurable delay)
                                # Capture user_who_sent in closure for later use
                                captured_user = user_who_sent
                                async def delayed_satisfaction_check():
                                    try:
                                        delay = BOT_SETTINGS.get('satisfaction_delay', 15)
                                        await asyncio.sleep(delay)  # Wait for user to finish typing
                                        
                                        # Get the thread channel
                                        thread_channel = bot.get_channel(thread_id)
                                        if not thread_channel:
                                            print(f"⚠ Could not find thread channel {thread_id}")
                                            return
                                        
                                        # Get all recent user messages (last 5)
                                        recent_user_messages = [msg.get('content') for msg in conversation[-5:] if msg.get('author') == 'User']
                                        
                                        print(f"📝 Analyzing {len(recent_user_messages)} user message(s): {recent_user_messages}")
                                        
                                        if not recent_user_messages:
                                            print(f"⚠ No user messages found for analysis")
                                            return
                                        
                                        satisfaction = await analyze_user_satisfaction(recent_user_messages)
                                        print(f"📊 Analysis result: satisfied={satisfaction.get('satisfied')}, wants_human={satisfaction.get('wants_human')}, confidence={satisfaction.get('confidence')}")
                                        
                                        # Update status based on analysis
                                        updated_status = matching_post.get('status', 'Unsolved')
                                        response_type = thread_response_type.get(thread_id)  # Get what type of response we gave
                                        
                                        # DEBUG: Log escalation decision factors
                                        print(f"🔍 Escalation Decision Factors:")
                                        print(f"   Response type: {response_type}")
                                        print(f"   Satisfied: {satisfaction.get('satisfied')}")
                                        print(f"   Wants human: {satisfaction.get('wants_human')}")
                                        print(f"   Confidence: {satisfaction.get('confidence')}")
                                        
                                        # ESCALATION LOGIC:
                                        # 1. Auto-response → if unsatisfied → AI response
                                        # 2. AI response → if unsatisfied → Human support
                                        # 3. Explicit human request → Human support immediately
                                        
                                        if satisfaction.get('satisfied') and satisfaction.get('confidence', 0) > 60:
                                            # User is satisfied - mark as solved
                                            updated_status = 'Solved'
                                            
                                            # Send shorter satisfaction confirmation embed
                                            confirm_embed = discord.Embed(
                                                title="✅ Great! Issue Solved",
                                                description="Glad I could help! This post will now be locked.",
                                                color=0x2ECC71
                                            )
                                            confirm_embed.add_field(
                                                name="💬 More Questions?",
                                                value="Create a new post anytime!",
                                                inline=False
                                            )
                                            confirm_embed.set_footer(text="Revolution Macro Support")
                                            await thread_channel.send(embed=confirm_embed)
                                            print(f"✅ User satisfaction detected - marking thread {thread_id} as Solved")
                                            
                                            # Apply "Resolved" tag and remove "Unsolved" tag if it exists
                                            try:
                                                forum_channel = bot.get_channel(SUPPORT_FORUM_CHANNEL_ID)
                                                if forum_channel:
                                                    resolved_tag = await get_resolved_tag(forum_channel)
                                                    unsolved_tag = await get_unsolved_tag(forum_channel)
                                                    
                                                    # Get current tags
                                                    current_tags = list(thread_channel.applied_tags)
                                                    
                                                    # Remove unsolved tag if present
                                                    if unsolved_tag and unsolved_tag in current_tags:
                                                        current_tags.remove(unsolved_tag)
                                                        print(f"🏷️ Removed '{unsolved_tag.name}' tag from thread {thread_id}")
                                                    
                                                    # Add resolved tag if not present
                                                    if resolved_tag and resolved_tag not in current_tags:
                                                        current_tags.append(resolved_tag)
                                                        print(f"🏷️ Applied '{resolved_tag.name}' tag to thread {thread_id}")
                                                    
                                                    # Update tags
                                                    await thread_channel.edit(applied_tags=current_tags)
                                            except Exception as tag_error:
                                                print(f"⚠ Could not update tags: {tag_error}")
                                            
                                            # Lock/archive the thread
                                            try:
                                                await thread_channel.edit(archived=True, locked=True)
                                                print(f"🔒 Thread {thread_id} locked and archived successfully")
                                            except discord.errors.Forbidden as perm_error:
                                                print(f"❌ Bot lacks 'Manage Threads' permission to lock thread {thread_id}")
                                                print(f"   Error: {perm_error}")
                                                # Send notification that thread couldn't be locked
                                                try:
                                                    lock_fail_embed = discord.Embed(
                                                        title="⚠️ Thread Not Locked",
                                                        description="This thread has been marked as Solved, but I don't have permission to lock it. Please give me the **Manage Threads** permission.",
                                                        color=0xF39C12
                                                    )
                                                    await thread_channel.send(embed=lock_fail_embed)
                                                except:
                                                    pass
                                            except Exception as lock_error:
                                                print(f"❌ Error locking thread {thread_id}: {lock_error}")
                                                import traceback
                                                traceback.print_exc()
                                            
                                            # Automatically create RAG entry from this solved conversation (if enabled)
                                            try:
                                                # Check if auto-RAG is enabled
                                                if not BOT_SETTINGS.get('auto_rag_enabled', True):
                                                    print(f"ℹ️ Auto-RAG creation is disabled - skipping RAG entry for thread {thread_id}")
                                                else:
                                                    print(f"📝 Attempting to create RAG entry from solved conversation...")
                                                    
                                                    # Format conversation for analysis
                                                    formatted_lines = []
                                                    for msg in conversation:
                                                        author = msg.get('author', 'Unknown')
                                                        content = msg.get('content', '')
                                                        formatted_lines.append(f"<@{author}> Said: {content}")
                                                    
                                                    conversation_text = "\n".join(formatted_lines)
                                                    
                                                    # Analyze conversation to create RAG entry
                                                    rag_entry = await analyze_conversation(conversation_text)
                                                    
                                                    # Check if thread was manually closed with no_review (don't create RAG)
                                                    if thread_id in no_review_threads:
                                                        print(f"🚫 Thread {thread_id} marked as no_review - skipping auto-RAG creation")
                                                    elif rag_entry and 'your-vercel-app' not in DATA_API_URL:
                                                        # Create pending RAG entry (requires approval)
                                                        data_api_url_rag = DATA_API_URL
                                                        
                                                        async with aiohttp.ClientSession() as rag_session:
                                                            async with rag_session.get(data_api_url_rag) as get_data_response:
                                                                current_data = {'ragEntries': [], 'autoResponses': [], 'slashCommands': [], 'pendingRagEntries': []}
                                                                if get_data_response.status == 200:
                                                                    current_data = await get_data_response.json()
                                                                
                                                                # Create conversation preview for review
                                                                conversation_preview = conversation_text[:500] + "..." if len(conversation_text) > 500 else conversation_text
                                                                
                                                                # Create new PENDING RAG entry
                                                                new_pending_entry = {
                                                                    'id': f'PENDING-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                                                                    'title': rag_entry.get('title', 'Auto-generated from solved thread'),
                                                                    'content': rag_entry.get('content', ''),
                                                                    'keywords': rag_entry.get('keywords', []),
                                                                    'createdAt': datetime.now().isoformat(),
                                                                    'source': 'Auto-satisfaction',
                                                                    'threadId': str(thread_id),
                                                                    'conversationPreview': conversation_preview
                                                                }
                                                                
                                                                pending_entries = current_data.get('pendingRagEntries', [])
                                                                pending_entries.append(new_pending_entry)
                                                                
                                                                # Save to API (must include ALL fields)
                                                                save_data = {
                                                                    'ragEntries': current_data.get('ragEntries', []),
                                                                    'autoResponses': current_data.get('autoResponses', []),
                                                                    'slashCommands': current_data.get('slashCommands', []),
                                                                    'botSettings': current_data.get('botSettings', {}),
                                                                    'pendingRagEntries': pending_entries
                                                                }
                                                                
                                                                print(f"💾 Saving pending RAG entry to API for review...")
                                                                print(f"   Total pending entries: {len(pending_entries)}")
                                                                print(f"   New pending entry: '{new_pending_entry['title']}'")
                                                                
                                                                headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                                                                async with rag_session.post(data_api_url_rag, json=save_data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as save_response:
                                                                    response_text = await save_response.text()
                                                                    if save_response.status == 200:
                                                                        print(f"✅ Created pending RAG entry for review: '{new_pending_entry['title']}'")
                                                                        print(f"   API response: {response_text[:200]}")
                                                                        
                                                                        # Send shorter notification in thread
                                                                        rag_notification = discord.Embed(
                                                                            title="📋 Entry Saved for Review",
                                                                            description=f"**{new_pending_entry['title']}**\n\nThis will be reviewed and added to help future users!",
                                                                            color=0xF39C12
                                                                        )
                                                                        rag_notification.set_footer(text="Revolution Macro • Pending Approval")
                                                                        await thread_channel.send(embed=rag_notification)
                                                                    else:
                                                                        print(f"❌ Failed to create pending RAG entry!")
                                                                        print(f"   Status: {save_response.status}")
                                                                        print(f"   Response: {response_text[:300]}")
                                                                        print(f"   URL: {data_api_url_rag}")
                                                                        print(f"   Payload: {len(pending_entries)} pending entries")
                                                    else:
                                                        print(f"ℹ Skipping RAG entry creation (no entry generated or API not configured)")
                                            except Exception as rag_error:
                                                print(f"⚠ Error auto-creating RAG entry: {rag_error}")
                                                import traceback
                                                traceback.print_exc()
                                        
                                        elif not satisfaction.get('satisfied') and satisfaction.get('confidence', 0) > 60:
                                            # User is unsatisfied - check escalation path
                                            
                                            # STEP 1: Check if they EXPLICITLY asked for human (e.g., "I want to talk to a person")
                                            if satisfaction.get('wants_human') and response_type == 'ai':
                                                # They got AI and explicitly want human - escalate
                                                updated_status = 'Human Support'
                                                escalated_threads.add(thread_id)
                                                
                                                human_embed = discord.Embed(
                                                    title="👨‍💼 Support Team Notified",
                                                    description="Got it! I've notified our support team. They'll help you soon.",
                                                    color=0x3498DB
                                                )
                                                human_embed.add_field(
                                                    name="⏰ Response Time",
                                                    value="Usually under 24 hours",
                                                    inline=True
                                                )
                                                human_embed.add_field(
                                                    name="📸 Tip",
                                                    value="Send screenshots if you have any!",
                                                    inline=True
                                                )
                                                human_embed.set_footer(text="Revolution Macro Support Team")
                                                await thread_channel.send(embed=human_embed)
                                                print(f"👥 User explicitly requested human support after AI - thread {thread_id} escalated")
                                            
                                            # STEP 2: They got auto-response and are unsatisfied - try AI
                                            elif response_type == 'auto':
                                                print(f"🔄 ESCALATION PATH: Auto → AI (user unsatisfied with auto-response, trying AI follow-up...)")
                                                
                                                try:
                                                    # Get the user's question from conversation
                                                    user_messages = [msg.get('content', '') for msg in conversation if msg.get('author') == 'User']
                                                    user_question = ' '.join(user_messages[:2]) if user_messages else "Help with this issue"
                                                    
                                                    print(f"📝 Generating AI response for: {user_question[:50]}...")
                                                    
                                                    # Try to find RAG entries
                                                    relevant_docs = find_relevant_rag_entries(user_question)
                                                    
                                                    # Generate AI response (ALWAYS, with or without RAG) - no images in on_message handler
                                                    if relevant_docs:
                                                        print(f"📚 Found {len(relevant_docs)} RAG entries for AI response")
                                                        ai_response = await generate_ai_response(user_question, relevant_docs[:2], None)
                                                    else:
                                                        print(f"💭 No RAG entries - AI using general knowledge")
                                                        ai_response = await generate_ai_response(user_question, [], None)
                                                    
                                                    print(f"✅ AI response generated ({len(ai_response)} chars)")
                                                    
                                                    # Send the AI response
                                                    ai_embed = discord.Embed(
                                                        title="💡 Let Me Try Again",
                                                        description=ai_response,
                                                        color=0x5865F2
                                                    )
                                                    ai_embed.add_field(
                                                        name="💬 Better?",
                                                        value="Let me know by clicking a button below!",
                                                        inline=False
                                                    )
                                                    ai_embed.set_footer(text="Revolution Macro AI")
                                                    
                                                    # Add satisfaction buttons
                                                    button_view = SatisfactionButtons(thread_id, conversation, 'ai')
                                                    await thread_channel.send(embed=ai_embed, view=button_view)
                                                    thread_response_type[thread_id] = 'ai'
                                                    updated_status = 'AI Response'
                                                    print(f"✅ SENT AI FOLLOW-UP RESPONSE to thread {thread_id}")
                                                    
                                                except Exception as ai_error:
                                                    print(f"❌ ERROR generating AI follow-up: {ai_error}")
                                                    import traceback
                                                    traceback.print_exc()
                                                    # Even if AI fails, send something
                                                    try:
                                                        fallback_embed = discord.Embed(
                                                            title="💡 Let Me Try Again",
                                                            description="I'm having trouble generating a detailed response. Let me get a human to help you with this!",
                                                            color=0xF39C12
                                                        )
                                                        await thread_channel.send(embed=fallback_embed)
                                                        updated_status = 'Human Support'
                                                        escalated_threads.add(thread_id)
                                                    except:
                                                        pass
                                            
                                            # STEP 3: They got AI response and are still unsatisfied - escalate to human
                                            elif response_type == 'ai':
                                                # They got AI response and were still unsatisfied - escalate to human
                                                print(f"⚠ ESCALATION PATH: AI → Human (user still unsatisfied after AI response)")
                                                updated_status = 'Human Support'
                                                escalated_threads.add(thread_id)  # Mark thread - bot stops talking
                                                
                                                # Get the user who triggered this (from the message that started the timer)
                                                # We need to check if they're the post creator and not staff
                                                user_who_triggered = None
                                                thread_owner_id = None
                                                should_show_log_prompt = False
                                                
                                                try:
                                                    # Get thread owner
                                                    if hasattr(thread_channel, 'owner_id') and thread_channel.owner_id:
                                                        thread_owner_id = thread_channel.owner_id
                                                    elif hasattr(thread_channel, 'owner') and thread_channel.owner:
                                                        thread_owner_id = thread_channel.owner.id
                                                    
                                                    # Get the user who sent the message that triggered this (from closure)
                                                    user_who_triggered = captured_user
                                                    if user_who_triggered and thread_owner_id:
                                                        is_creator = user_who_triggered.id == thread_owner_id
                                                        is_staff = is_staff_or_admin(user_who_triggered) if isinstance(user_who_triggered, discord.Member) else False
                                                        should_show_log_prompt = is_creator and not is_staff
                                                except Exception as user_check_error:
                                                    print(f"⚠ Error checking user for log prompt: {user_check_error}")
                                                
                                                if should_show_log_prompt:
                                                    # First, ask for logs to help support team (only to post creator)
                                                    log_prompt_embed = discord.Embed(
                                                        title="📋 Before We Get Support...",
                                                        description="To help our team solve this **much faster**, please include your **logs**!\n\nLogs contain error details that help us identify exactly what's wrong.",
                                                        color=0xF39C12
                                                    )
                                                    log_prompt_embed.add_field(
                                                        name="🧭 How to Get Logs (from the Macro)",
                                                        value=(
                                                            "1) Open the macro and go to **Status → Logs**\n"
                                                            "2) Click **Copy Logs** → then paste here\n"
                                                            "   - or -\n"
                                                            "   Click **Open Logs Folder** → upload the most recent `.log` file"
                                                        ),
                                                        inline=False
                                                    )
                                                    log_prompt_embed.add_field(
                                                        name="📌 Tips",
                                                        value="Please include screenshots or a short video if possible. It helps a ton!",
                                                        inline=False
                                                    )
                                                    log_prompt_embed.set_footer(text="💡 Uploading logs can reduce resolution time by 50%!")
                                                    
                                                    # Send the unified logs instructions (no OS selector needed anymore)
                                                    await thread_channel.send(embed=log_prompt_embed)
                                                    
                                                    # Wait a moment, then send escalation message
                                                    await asyncio.sleep(2)
                                                else:
                                                    print(f"ℹ Skipping log prompt - user is not post creator or is staff/admin")
                                                
                                                # Send escalation embed
                                                escalate_embed = discord.Embed(
                                                    title="👨‍💼 Support Team Notified",
                                                    description="Our support team has been notified and will review your issue soon!",
                                                    color=0xE67E22
                                                )
                                                escalate_embed.add_field(
                                                    name="⏰ Response Time",
                                                    value="Usually under 24 hours",
                                                    inline=True
                                                )
                                                escalate_embed.add_field(
                                                    name="📎 Helpful to Include",
                                                    value="Screenshots, videos, or error messages",
                                                    inline=True
                                                )
                                                escalate_embed.set_footer(text="Revolution Macro Support Team")
                                                await thread_channel.send(embed=escalate_embed)
                                                print(f"⚠ User unsatisfied after AI - escalating thread {thread_id} to Human Support")
                                            
                                            # STEP 4: No response type tracked - default behavior
                                            else:
                                                print(f"⚠ No response type tracked for thread {thread_id}, defaulting to human escalation")
                                                updated_status = 'Human Support'
                                                escalated_threads.add(thread_id)
                                    
                                        # Update forum post status in dashboard
                                        if updated_status != matching_post.get('status'):
                                            # Only try to update if API is configured
                                            if 'your-vercel-app' not in DATA_API_URL:
                                                try:
                                                    forum_api_url_delayed = DATA_API_URL.replace('/api/data', '/api/forum-posts')
                                                    print(f"🔄 Updating dashboard status to '{updated_status}' for thread {thread_id}")
                                                    
                                                    async with aiohttp.ClientSession() as delayed_session:
                                                        # Get current posts
                                                        async with delayed_session.get(forum_api_url_delayed) as get_resp:
                                                            if get_resp.status == 200:
                                                                all_posts = await get_resp.json()
                                                                current_post = None
                                                                for p in all_posts:
                                                                    if p.get('postId') == str(thread_id) or p.get('id') == f'POST-{thread_id}':
                                                                        current_post = p
                                                                        break
                                                                
                                                                if current_post:
                                                                    current_post['status'] = updated_status
                                                                    update_payload = {
                                                                        'action': 'update',
                                                                        'post': current_post
                                                                    }
                                                                    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                                                                    async with delayed_session.post(forum_api_url_delayed, json=update_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as update_resp:
                                                                        if update_resp.status == 200:
                                                                            print(f"✅ Successfully updated forum post status to '{updated_status}' for thread {thread_id}")
                                                                            response_data = await update_resp.json()
                                                                            print(f"   API response: {response_data}")
                                                                        else:
                                                                            error_text = await update_resp.text()
                                                                            print(f"❌ Failed to update forum post status: HTTP {update_resp.status}")
                                                                            print(f"   Error: {error_text[:200]}")
                                                                else:
                                                                    print(f"⚠ Could not find forum post with thread ID {thread_id} in dashboard")
                                                            else:
                                                                print(f"⚠ Failed to fetch forum posts from API: HTTP {get_resp.status}")
                                                except Exception as e:
                                                    print(f"❌ Error updating status after delayed analysis: {e}")
                                                    import traceback
                                                    traceback.print_exc()
                                            else:
                                                print(f"ℹ Skipping dashboard update - API not configured")
                                        
                                        # Clean up timer
                                        if thread_id in satisfaction_timers:
                                            del satisfaction_timers[thread_id]
                                            
                                    except asyncio.CancelledError:
                                        print(f"⏰ Satisfaction timer cancelled for thread {thread_id}")
                                    except Exception as e:
                                        print(f"⚠ Error in delayed satisfaction check: {e}")
                                        import traceback
                                        traceback.print_exc()
                            
                            # Store the task
                            satisfaction_timers[thread_id] = asyncio.create_task(delayed_satisfaction_check())
                            delay = BOT_SETTINGS.get('satisfaction_delay', 15)
                            print(f"⏰ Started {delay}-second satisfaction timer for thread {thread_id}")
                        
                        else:
                            # Normal flow - update conversation
                            post_update = {
                                'action': 'update',
                                'post': {
                                    **matching_post,
                                    'conversation': conversation,
                                    'status': new_status
                                }
                            }
                    else:
                        # Create new post if it doesn't exist
                        thread_name = thread.name if hasattr(thread, 'name') else 'New Thread'
                        thread_created = thread.created_at if hasattr(thread, 'created_at') else datetime.now()
                        
                        post_update = {
                            'action': 'create',
                            'post': {
                                'id': f'POST-{thread.id}',
                                'user': {
                                    'username': user_name,
                                    'id': user_id,
                                    'avatarUrl': avatar_url
                                },
                                'postTitle': thread_name,
                                'status': 'Unsolved',
                                'tags': [],
                                'createdAt': thread_created.isoformat() if hasattr(thread_created, 'isoformat') else datetime.now().isoformat(),
                                'forumChannelId': str(thread.parent_id),
                                'postId': str(thread.id),
                                'conversation': [new_message]
                            }
                        }
                    
                    # Update post immediately
                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                    async with session.post(forum_api_url, json=post_update, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as post_response:
                        if post_response.status == 200:
                            print(f"✓ Updated forum post with message from {user_name}")
                        else:
                            text = await post_response.text()
                            print(f"⚠ Failed to update forum post with message: Status {post_response.status}, Response: {text[:100]}")
        except Exception:
            pass  # Silently fail - bot continues working
    
    await bot.process_commands(message)

# --- ADMIN SLASH COMMANDS ---
@bot.tree.command(name="stop", description="Stops the bot gracefully (Admin only).")
async def stop(interaction: discord.Interaction):
    """Stop the bot - requires admin or bot permissions role"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("🛑 Shutting down Revolution Macro bot...", ephemeral=True)
    print(f"Stop command issued by {interaction.user}. Shutting down in 2 seconds...")
    
    # Give time for response to send, then close
    await asyncio.sleep(2)
    print("Closing bot connection...")
    await bot.close()
    print("Bot stopped successfully.")

@bot.event
async def on_thread_delete(thread):
    """Handle forum post deletion - sync to dashboard"""
    try:
        # Only process if it's in our support forum channel
        if thread.parent_id != SUPPORT_FORUM_CHANNEL_ID:
            return
        
        # Skip API call if URL is not configured
        if 'your-vercel-app' in DATA_API_URL:
            return
        
        thread_id = thread.id
        print(f"🗑️ Forum post deleted: '{thread.name}' (ID: {thread_id})")
        
        # Remove from dashboard
        forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
        delete_data = {
            'action': 'delete',
            'postId': f'POST-{thread_id}'
        }
        
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        async with aiohttp.ClientSession() as session:
            async with session.post(forum_api_url, json=delete_data, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print(f"✅ Deleted forum post from dashboard: {thread_id}")
                else:
                    print(f"⚠ Failed to delete post from dashboard: {response.status}")
        
        # Clean up tracking dictionaries
        if thread_id in satisfaction_timers:
            satisfaction_timers[thread_id].cancel()
            del satisfaction_timers[thread_id]
        if thread_id in processed_threads:
            processed_threads.remove(thread_id)
        if thread_id in escalated_threads:
            escalated_threads.remove(thread_id)
        if thread_id in thread_response_type:
            del thread_response_type[thread_id]
            
    except Exception as e:
        print(f"⚠ Error handling thread deletion: {e}")
        import traceback
        traceback.print_exc()

@bot.tree.command(name="reload", description="Reloads data from dashboard (Admin only).")
async def reload(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    
    # Check permissions
    if not is_owner_or_admin(interaction):
        await interaction.followup.send("❌ You need Administrator permission to use this command.", ephemeral=True)
        return
    
    success = await fetch_data_from_api()
    if success:
        await interaction.followup.send(f"✅ Data reloaded successfully from dashboard! Loaded {len(RAG_DATABASE)} RAG entries into memory.", ephemeral=False)
    else:
        await interaction.followup.send("⚠️ Failed to reload data. Using cached data.", ephemeral=False)
    print(f"Reload command issued by {interaction.user}.")

@bot.tree.command(name="fix_duplicate_commands", description="Clear ALL slash commands and re-sync (fixes duplicates) (Admin only).")
async def fix_duplicate_commands(interaction: discord.Interaction):
    """Clear all slash commands (global + guild) and re-sync to fix duplicates"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        guild = discord.Object(id=DISCORD_GUILD_ID)
        
        # Step 1: Clear global commands
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print(f"🧹 Cleared global commands")
        
        # Step 2: Clear guild commands
        bot.tree.clear_commands(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"🧹 Cleared guild commands for {DISCORD_GUILD_ID}")
        
        # Step 3: Wait a moment for Discord to process
        await asyncio.sleep(2)
        
        # Step 4: Re-sync commands to guild
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        
        await interaction.followup.send(
            f"✅ **Fixed duplicate commands!**\n\n"
            f"🧹 Cleared: Global + Guild commands\n"
            f"🔄 Re-synced: {len(synced)} commands to guild\n\n"
            f"💡 **Refresh Discord** (`Ctrl+R`) to see the changes!\n"
            f"Commands should now appear only once.",
            ephemeral=False
        )
        print(f"✓ Fixed duplicate commands - re-synced {len(synced)} commands by {interaction.user}")
        
    except Exception as e:
        print(f"Error in fix_duplicate_commands: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=False)

@bot.tree.command(name="set_forums_id", description="Set the support forum channel ID for the bot to monitor (Admin only).")
async def set_forums_id(interaction: discord.Interaction, channel_id: str):
    """Set the forum channel ID and save to settings file"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Validate channel ID
        try:
            new_channel_id = int(channel_id)
        except ValueError:
            await interaction.followup.send("❌ Invalid channel ID. Must be a number.", ephemeral=False)
            return
        
        # Try to get the channel
        channel = bot.get_channel(new_channel_id)
        if not channel:
            await interaction.followup.send(
                f"⚠️ Warning: Channel with ID {new_channel_id} not found.\n"
                f"Make sure:\n"
                f"1. The ID is correct\n"
                f"2. Bot has access to this channel\n"
                f"3. Bot is in the same server\n\n"
                f"I'll save it anyway, but the bot may not work until these are fixed.",
                ephemeral=False
            )
        else:
            channel_type = type(channel).__name__
            await interaction.followup.send(
                f"✅ Forum channel updated!\n\n"
                f"**Channel:** {channel.name}\n"
                f"**ID:** {new_channel_id}\n"
                f"**Type:** {channel_type}\n\n"
                f"Bot will now monitor this channel for new forum posts.",
                ephemeral=False
            )
        
        # Update global variable
        global SUPPORT_FORUM_CHANNEL_ID, BOT_SETTINGS
        SUPPORT_FORUM_CHANNEL_ID = new_channel_id
        # Store as STRING to prevent JavaScript number precision loss
        BOT_SETTINGS['support_forum_channel_id'] = str(new_channel_id)
        
        # Save to file
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            print(f"✓ Updated forum channel ID to {new_channel_id}")
        else:
            await interaction.followup.send(
                "⚠️ Channel ID updated in memory but failed to save to file.",
                ephemeral=False
            )
            
    except Exception as e:
        print(f"Error in set_forums_id command: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_ignore_post_id", description="Set a post ID to ignore (like rules post). Bot won't respond to it (Admin only).")
async def set_ignore_post_id(interaction: discord.Interaction, post_id: str):
    """Add a post ID to the ignore list"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Validate post ID is a number
        try:
            post_id_int = int(post_id)
        except ValueError:
            await interaction.followup.send("❌ Post ID must be a number.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        ignored_posts = BOT_SETTINGS.get('ignored_post_ids', [])
        
        # Check if already in list (stored as strings)
        if str(post_id_int) in ignored_posts or post_id in ignored_posts:
            await interaction.followup.send(f"⚠️ Post ID {post_id} is already in the ignore list.", ephemeral=False)
            return
        
        # Store as STRING to prevent JavaScript number precision loss
        ignored_posts.append(str(post_id_int))
        BOT_SETTINGS['ignored_post_ids'] = ignored_posts
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            await interaction.followup.send(
                f"✅ Post ID **{post_id}** added to ignore list!\n\n"
                f"The bot will no longer respond to this post.\n"
                f"Total ignored posts: {len(ignored_posts)}",
                ephemeral=False
            )
            print(f"✓ Added post ID {post_id} to ignore list by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_ignore_post_id: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_unsolved_tag_id", description="Set the Discord tag ID for 'Unsolved' posts (Admin only).")
async def set_unsolved_tag_id(interaction: discord.Interaction, tag_id: str):
    """Set the unsolved tag ID"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Validate tag ID is a number
        try:
            tag_id_int = int(tag_id)
        except ValueError:
            await interaction.followup.send("❌ Tag ID must be a number.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        # Store as STRING to prevent JavaScript number precision loss
        BOT_SETTINGS['unsolved_tag_id'] = str(tag_id_int)
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            await interaction.followup.send(
                f"✅ Unsolved tag ID set to **{tag_id}**!\n\n"
                f"New forum posts will automatically be tagged as 'Unsolved'.",
                ephemeral=False
            )
            print(f"✓ Set unsolved tag ID to {tag_id} by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_unsolved_tag_id: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_solved_tag_id", description="Set the Discord tag ID for 'Solved' posts (Admin only).")
async def set_solved_tag_id(interaction: discord.Interaction, tag_id: str):
    """Set the solved tag ID"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Validate tag ID is a number
        try:
            tag_id_int = int(tag_id)
        except ValueError:
            await interaction.followup.send("❌ Tag ID must be a number.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        # Store as STRING to prevent JavaScript number precision loss
        BOT_SETTINGS['resolved_tag_id'] = str(tag_id_int)
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            await interaction.followup.send(
                f"✅ Solved tag ID set to **{tag_id}**!\n\n"
                f"Posts marked as Solved will automatically get this tag applied.",
                ephemeral=False
            )
            print(f"✓ Solved tag ID set to {tag_id} by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_solved_tag_id: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_satisfaction_delay", description="Set the delay (in seconds) before analyzing user satisfaction (Admin only).")
async def set_satisfaction_delay(interaction: discord.Interaction, seconds: int):
    """Set the satisfaction analysis delay"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        if seconds < 5 or seconds > 300:
            await interaction.followup.send("❌ Delay must be between 5 and 300 seconds.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        BOT_SETTINGS['satisfaction_delay'] = seconds
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            await interaction.followup.send(
                f"✅ Satisfaction delay updated to **{seconds} seconds**!\n\n"
                f"The bot will now wait {seconds} seconds after a user's last message before analyzing their satisfaction.",
                ephemeral=False
            )
            print(f"✓ Satisfaction delay updated to {seconds} seconds by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_satisfaction_delay: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_temperature", description="Set the AI temperature (0.0-2.0) for response generation (Admin only).")
async def set_temperature(interaction: discord.Interaction, temperature: float):
    """Set the AI temperature"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        if temperature < 0.0 or temperature > 2.0:
            await interaction.followup.send("❌ Temperature must be between 0.0 and 2.0.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        BOT_SETTINGS['ai_temperature'] = temperature
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            temp_desc = "more focused/deterministic" if temperature < 0.7 else "more creative/varied" if temperature > 1.3 else "balanced"
            await interaction.followup.send(
                f"✅ AI temperature updated to **{temperature}**!\n\n"
                f"Responses will be **{temp_desc}**.\n"
                f"Lower = more consistent, Higher = more creative",
                ephemeral=False
            )
            print(f"✓ AI temperature updated to {temperature} by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_temperature: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_max_tokens", description="Set the maximum tokens for AI responses (Admin only).")
async def set_max_tokens(interaction: discord.Interaction, max_tokens: int):
    """Set the maximum tokens for AI responses"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        if max_tokens < 100 or max_tokens > 8192:
            await interaction.followup.send("❌ Max tokens must be between 100 and 8192.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        BOT_SETTINGS['ai_max_tokens'] = max_tokens
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            length_desc = "shorter" if max_tokens < 1024 else "longer" if max_tokens > 3072 else "medium"
            await interaction.followup.send(
                f"✅ Max tokens updated to **{max_tokens}**!\n\n"
                f"Responses will be **{length_desc}** (approximately {max_tokens // 4} words max).",
                ephemeral=False
            )
            print(f"✓ Max tokens updated to {max_tokens} by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_max_tokens: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_post_inactivity_time", description="Set hours before old posts escalate to High Priority (Admin only).")
async def set_post_inactivity_time(interaction: discord.Interaction, hours: int):
    """Set the post inactivity threshold for auto-escalation"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        if hours < 1 or hours > 168:  # 1 hour to 7 days
            await interaction.followup.send("❌ Hours must be between 1 and 168 (7 days).", ephemeral=False)
            return
        
        global BOT_SETTINGS
        BOT_SETTINGS['post_inactivity_hours'] = hours
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            await interaction.followup.send(
                f"✅ Post inactivity threshold updated to **{hours} hours**!\n\n"
                f"Posts older than {hours} hours will be escalated to **High Priority**.\n"
                f"The background task runs every hour to check for old posts.",
                ephemeral=False
            )
            print(f"✓ Post inactivity threshold updated to {hours} hours by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_post_inactivity_time: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_ping_high_priority_interval", description="Set how often to check for high priority posts in hours (Admin only).")
async def set_ping_high_priority_interval(interaction: discord.Interaction, hours: float):
    """Set the interval for checking old posts that need escalation"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        if hours < 0.25 or hours > 24:  # 15 minutes to 24 hours
            await interaction.followup.send("❌ Interval must be between 0.25 (15 min) and 24 hours.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        BOT_SETTINGS['high_priority_check_interval_hours'] = hours
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            # Update the background task interval
            check_old_posts.change_interval(hours=hours)
            
            # Convert to readable format
            if hours < 1:
                minutes = int(hours * 60)
                time_str = f"{minutes} minutes"
            else:
                time_str = f"{hours} hour{'s' if hours != 1 else ''}"
            
            inactivity_threshold = BOT_SETTINGS.get('post_inactivity_hours', 12)
            # Get channel info - always use clickable format
            notification_channel_id = BOT_SETTINGS.get('support_notification_channel_id')
            if notification_channel_id:
                channel_display = f"<#{notification_channel_id}>"
            else:
                channel_display = "Not configured (use `/set_support_notification_channel`)"
            
            await interaction.followup.send(
                f"✅ High priority check interval updated to **{time_str}**!\n\n"
                f"📊 **Current Settings:**\n"
                f"• Check Interval: Every {time_str}\n"
                f"• Escalation Threshold: {inactivity_threshold} hours of inactivity\n"
                f"• Notification Channel: {channel_display}\n\n"
                f"💡 **Tip**: Shorter intervals mean faster response to old posts, but check your server load!",
                ephemeral=False
            )
            print(f"✓ High priority check interval updated to {hours} hours ({time_str}) by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_ping_high_priority_interval: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_support_role", description="Set the role to ping for high priority posts (Admin only).")
async def set_support_role(interaction: discord.Interaction, role: discord.Role):
    """Set the support role to ping for high priority posts"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        global BOT_SETTINGS
        # Store as STRING to prevent JavaScript number precision loss
        BOT_SETTINGS['support_role_id'] = str(role.id)
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            # Get channel info - always use clickable format
            notification_channel_id = BOT_SETTINGS.get('support_notification_channel_id')
            if notification_channel_id:
                # Convert to int for Discord API (stored as string to prevent precision loss)
                channel_id_int = int(notification_channel_id) if isinstance(notification_channel_id, str) else notification_channel_id
                channel_display = f"<#{channel_id_int}>"
            else:
                channel_display = "the notification channel (set with `/set_support_notification_channel`)"
            
            await interaction.followup.send(
                f"✅ Support role set to {role.mention}!\n\n"
                f"This role will be pinged in {channel_display} "
                f"whenever a post is escalated to **High Priority**.",
                ephemeral=False
            )
            print(f"✓ Support role set to {role.name} (ID: {role.id}) by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_support_role: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_support_notification_channel", description="Set channel for high priority notifications (Admin only).")
async def set_support_notification_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the channel for high priority post notifications"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        global BOT_SETTINGS
        BOT_SETTINGS['support_notification_channel_id'] = channel.id
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            role_mention = f"<@&{BOT_SETTINGS.get('support_role_id')}>" if BOT_SETTINGS.get('support_role_id') else "No role set"
            await interaction.followup.send(
                f"✅ Support notification channel set to {channel.mention}!\n\n"
                f"**Current Support Role:** {role_mention}\n"
                f"High priority posts will be announced in {channel.mention}.\n\n"
                f"Use `/set_support_role` to configure which role gets pinged.",
                ephemeral=False
            )
            print(f"✓ Support notification channel set to #{channel.name} (ID: {channel.id}) by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_support_notification_channel: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_high_priority_channel_id", description="Set high priority notification channel by ID (Admin only).")
async def set_high_priority_channel_id(interaction: discord.Interaction, channel_id: str):
    """Set the high priority notification channel by ID"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Validate channel ID
        try:
            new_channel_id = int(channel_id)
        except ValueError:
            await interaction.followup.send("❌ Invalid channel ID. Must be a number.", ephemeral=False)
            return
        
        # Try to get the channel
        channel = bot.get_channel(new_channel_id)
        
        global BOT_SETTINGS
        # Store as STRING to prevent JavaScript number precision loss
        BOT_SETTINGS['support_notification_channel_id'] = str(new_channel_id)
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            if channel:
                role_mention = f"<@&{BOT_SETTINGS.get('support_role_id')}>" if BOT_SETTINGS.get('support_role_id') else "No role set"
                await interaction.followup.send(
                    f"✅ Support notification channel set to {channel.mention}!\n\n"
                    f"**Channel ID:** {new_channel_id}\n"
                    f"**Current Support Role:** {role_mention}\n\n"
                    f"High priority posts will be announced in {channel.mention}.\n"
                    f"Use `/set_support_role` to configure which role gets pinged.",
                    ephemeral=False
                )
                print(f"✓ Support notification channel set to #{channel.name} (ID: {new_channel_id}) by {interaction.user}")
            else:
                await interaction.followup.send(
                    f"⚠️ Channel ID {new_channel_id} set, but channel not found.\n\n"
                    f"Make sure:\n"
                    f"1. The ID is correct\n"
                    f"2. Bot has access to this channel\n"
                    f"3. Bot is in the same server\n\n"
                    f"The setting has been saved and will work once the channel is accessible.",
                    ephemeral=False
                )
                print(f"⚠️ Support notification channel ID set to {new_channel_id} (channel not found) by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_high_priority_channel_id: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_solved_post_retention", description="Set days to keep solved posts before auto-deletion (Admin only).")
async def set_solved_post_retention(interaction: discord.Interaction, days: int):
    """Set how long to keep solved/closed posts before automatic deletion"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        if days < 1 or days > 365:  # 1 day to 1 year
            await interaction.followup.send("❌ Days must be between 1 and 365.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        BOT_SETTINGS['solved_post_retention_days'] = days
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            await interaction.followup.send(
                f"✅ Solved post retention updated to **{days} days**!\n\n"
                f"Posts with status **Solved** or **Closed** older than {days} days will be automatically deleted.\n"
                f"The cleanup task runs **daily** to check for old posts.\n\n"
                f"💡 This helps keep your dashboard clean and improves performance.",
                ephemeral=False
            )
            print(f"✓ Solved post retention updated to {days} days by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_solved_post_retention: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="toggle_auto_rag", description="Enable/disable automatic RAG entry creation from solved threads (Admin only).")
async def toggle_auto_rag(interaction: discord.Interaction, enabled: bool):
    """Toggle automatic RAG entry creation from solved threads"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        global BOT_SETTINGS
        BOT_SETTINGS['auto_rag_enabled'] = enabled
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            status_emoji = "✅" if enabled else "❌"
            status_text = "enabled" if enabled else "disabled"
            
            enabled_msg = "✅ When users click \"Yes, this solved my issue\", the bot will automatically create a pending RAG entry for review."
            disabled_msg = "❌ Solved threads will NOT automatically create RAG entries. You can still manually create them from the dashboard."
            
            await interaction.followup.send(
                f"{status_emoji} Auto-RAG creation is now **{status_text}**!\n\n"
                f"{enabled_msg if enabled else disabled_msg}\n\n"
                f"💡 This setting helps control how many pending RAG entries are created.",
                ephemeral=False
            )
            print(f"✓ Auto-RAG creation {status_text} by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in toggle_auto_rag: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="list_high_priority_posts", description="List all current high priority posts (Admin only).")
async def list_high_priority_posts(interaction: discord.Interaction):
    """List all posts currently marked as High Priority"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        forum_api_url = DATA_API_URL.replace('/data', '/forum-posts')
        
        async with aiohttp.ClientSession() as session:
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            async with session.get(forum_api_url, headers=headers) as response:
                if response.status != 200:
                    await interaction.followup.send("❌ Failed to fetch posts from API.", ephemeral=False)
                    return
                
                all_posts = await response.json()
                
                # Filter for high priority posts
                high_priority_posts = [p for p in all_posts if p.get('status') == 'High Priority']
                
                if not high_priority_posts:
                    await interaction.followup.send(
                        "✅ No high priority posts at the moment!\n\n"
                        "All support requests are being handled normally.",
                        ephemeral=False
                    )
                    return
                
                # Build embed with list of high priority posts
                embed = discord.Embed(
                    title=f"🚨 High Priority Posts ({len(high_priority_posts)})",
                    description="These posts need immediate attention from the support team:",
                    color=0xE74C3C
                )
                
                for i, post in enumerate(high_priority_posts[:10], 1):  # Limit to 10 posts
                    thread_id = post.get('postId')
                    post_title = post.get('postTitle', 'Unknown')
                    user_name = post.get('user', {}).get('username', 'Unknown')
                    
                    embed.add_field(
                        name=f"{i}. {post_title}",
                        value=f"**User:** {user_name}\n[View Post](https://discord.com/channels/{DISCORD_GUILD_ID}/{thread_id})",
                        inline=False
                    )
                
                if len(high_priority_posts) > 10:
                    embed.set_footer(text=f"Showing 10 of {len(high_priority_posts)} high priority posts")
                else:
                    # Get notification channel info
                    notif_channel_id = BOT_SETTINGS.get('support_notification_channel_id')
                    if notif_channel_id:
                        notif_channel_id = int(notif_channel_id) if isinstance(notif_channel_id, str) else notif_channel_id
                        notif_channel = bot.get_channel(notif_channel_id)
                        channel_name = f"#{notif_channel.name}" if notif_channel else "Not set"
                    else:
                        channel_name = "Not set"
                    embed.set_footer(text=f"Support Notification Channel: {channel_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=False)
                
    except Exception as e:
        print(f"Error in list_high_priority_posts: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="ping_high_priority_now", description="Manually send high priority summary to notification channel (Admin only).")
async def ping_high_priority_now(interaction: discord.Interaction):
    """Manually trigger a high priority posts summary notification"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Send the summary
        await notify_support_channel_summary()
        
        support_channel_id = BOT_SETTINGS.get('support_notification_channel_id')
        if support_channel_id:
            # Convert to int (stored as string to prevent JavaScript precision loss)
            support_channel_id = int(support_channel_id) if isinstance(support_channel_id, str) else support_channel_id
        support_channel = bot.get_channel(support_channel_id) if support_channel_id else None
        
        if support_channel:
            await interaction.followup.send(
                f"✅ High priority summary sent to {support_channel.mention}!\n\n"
                f"Check the channel for the list of all current high priority posts.",
                ephemeral=False
            )
        else:
            await interaction.followup.send(
                "✅ Attempted to send high priority summary!\n\n"
                "Check bot logs for any issues.",
                ephemeral=False
            )
        
        print(f"✓ Manual high priority ping triggered by {interaction.user}")
        
    except Exception as e:
        print(f"Error in ping_high_priority_now: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="toggle_satisfaction_analysis", description="Enable/disable automatic satisfaction analysis (saves Gemini API calls!) (Admin only).")
async def toggle_satisfaction_analysis(interaction: discord.Interaction, enabled: bool):
    """Toggle automatic satisfaction analysis to save API rate limits"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        global BOT_SETTINGS
        BOT_SETTINGS['satisfaction_analysis_enabled'] = enabled
        
        # Save to API (persists across deployments)
        if await save_bot_settings_to_api():
            status_emoji = "✅" if enabled else "❌"
            status_text = "enabled" if enabled else "disabled"
            
            await interaction.followup.send(
                f"{status_emoji} Satisfaction analysis is now **{status_text}**!\n\n"
                f"{'✅ The bot will automatically analyze user messages to detect satisfaction and escalate when needed.' if enabled else '❌ The bot will NOT automatically analyze satisfaction. Users can still click buttons to give feedback.'}\n\n"
                f"💡 **Gemini API Impact**: This saves ~1 API call per user reply (10 RPM limit)\n"
                f"📊 **Current rate**: {len(gemini_api_calls)}/10 calls in last minute",
                ephemeral=False
            )
            print(f"✓ Satisfaction analysis {status_text} by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to API.", ephemeral=False)
    except Exception as e:
        print(f"Error in toggle_satisfaction_analysis: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="status", description="Check bot status and current configuration (Admin only).")
async def status(interaction: discord.Interaction):
    """Show bot status and configuration"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("❌ You need Administrator permission to use this command.", ephemeral=True)
        return
    
    try:
        # Get channel info
        channel = bot.get_channel(SUPPORT_FORUM_CHANNEL_ID)
        channel_info = f"{channel.name} (ID: {SUPPORT_FORUM_CHANNEL_ID})" if channel else f"Not found (ID: {SUPPORT_FORUM_CHANNEL_ID})"
        
        # Count active timers
        active_timers = len(satisfaction_timers)
        
        # Check API status
        api_status = "✅ Connected" if 'your-vercel-app' not in DATA_API_URL else "⚠️ Not configured"
        
        status_embed = discord.Embed(
            title="🤖 Revolution Macro Bot Status",
            color=0x2ECC71
        )
        
        status_embed.add_field(
            name="📊 Data Loaded",
            value=f"**RAG Entries:** {len(RAG_DATABASE)}\n**Auto-Responses:** {len(AUTO_RESPONSES)}",
            inline=True
        )
        
        status_embed.add_field(
            name="⚙️ AI Settings",
            value=f"**Temperature:** {BOT_SETTINGS.get('ai_temperature', 1.0)}\n**Max Tokens:** {BOT_SETTINGS.get('ai_max_tokens', 2048)}",
            inline=True
        )
        
        status_embed.add_field(
            name="⏱️ Timers & Cleanup",
            value=f"**Satisfaction Delay:** {BOT_SETTINGS.get('satisfaction_delay', 15)}s\n**Active Timers:** {active_timers}\n**Post Inactivity:** {BOT_SETTINGS.get('post_inactivity_hours', 12)}h\n**Post Retention:** {BOT_SETTINGS.get('solved_post_retention_days', 30)}d",
            inline=True
        )
        
        status_embed.add_field(
            name="📚 Auto-RAG Creation",
            value=f"{'✅ Enabled' if BOT_SETTINGS.get('auto_rag_enabled', True) else '❌ Disabled'}",
            inline=True
        )
        
        status_embed.add_field(
            name="🔍 Satisfaction Analysis",
            value=f"{'✅ Enabled' if BOT_SETTINGS.get('satisfaction_analysis_enabled', True) else '❌ Disabled (saves API calls)'}",
            inline=True
        )
        
        status_embed.add_field(
            name="🔥 Gemini API Rate",
            value=f"**{len(gemini_api_calls)}/10** calls in last minute",
            inline=True
        )
        
        status_embed.add_field(
            name="📺 Forum Channel",
            value=channel_info,
            inline=False
        )
        
        status_embed.add_field(
            name="📡 API Status",
            value=api_status,
            inline=True
        )
        
        status_embed.add_field(
            name="🧠 System Prompt",
            value=f"Using {'custom' if SYSTEM_PROMPT_TEXT else 'default'} prompt",
            inline=True
        )
        
        status_embed.set_footer(text=f"Last updated: {BOT_SETTINGS.get('last_updated', 'Never')} • Use /api_info for sensitive details")
        
        await interaction.followup.send(embed=status_embed, ephemeral=False)
        print(f"Status command used by {interaction.user}")
        
    except Exception as e:
        print(f"Error in status command: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=False)

@bot.tree.command(name="api_info", description="View sensitive API configuration (Private, Admin only).")
async def api_info(interaction: discord.Interaction):
    """Show sensitive API and configuration details (private)"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    
    try:
        # API configuration
        api_status = "✅ Connected" if 'your-vercel-app' not in DATA_API_URL else "⚠️ Not configured"
        api_url = DATA_API_URL if 'your-vercel-app' not in DATA_API_URL else 'Not configured (using placeholder)'
        
        # System prompt details
        prompt_source = "Custom (from API)" if SYSTEM_PROMPT_TEXT else "Default (hardcoded)"
        prompt_length = len(SYSTEM_PROMPT_TEXT or SYSTEM_PROMPT)
        prompt_preview = (SYSTEM_PROMPT_TEXT or SYSTEM_PROMPT)[:200] + "..." if prompt_length > 200 else (SYSTEM_PROMPT_TEXT or SYSTEM_PROMPT)
        
        # Bot settings file
        # All settings stored in Vercel KV API now (no local file)
        
        api_embed = discord.Embed(
            title="🔐 Sensitive API Configuration",
            description="This information is private and only visible to you.",
            color=0xE74C3C
        )
        
        api_embed.add_field(
            name="📡 API Connection",
            value=f"**Status:** {api_status}\n**URL:** `{api_url}`",
            inline=False
        )
        
        api_embed.add_field(
            name="🧠 System Prompt Details",
            value=f"**Source:** {prompt_source}\n**Length:** {prompt_length} characters\n**Preview:** {prompt_preview}",
            inline=False
        )
        
        api_embed.add_field(
            name="💾 Bot Settings File",
            value=f"**Storage:** Vercel KV API (persists across deployments)\n**Loaded Settings:** {len(BOT_SETTINGS)} settings",
            inline=False
        )
        
        api_embed.add_field(
            name="🔑 Environment Variables",
            value=f"**DISCORD_BOT_TOKEN:** {'✅ Set' if DISCORD_BOT_TOKEN else '❌ Missing'}\n**GEMINI_API_KEY:** {'✅ Set' if GEMINI_API_KEY else '❌ Missing'}",
            inline=False
        )
        
        api_embed.set_footer(text="⚠️ Keep this information private! Only visible to you.")
        
        await interaction.followup.send(embed=api_embed, ephemeral=True)
        print(f"api_info command used by {interaction.user}")
        
    except Exception as e:
        print(f"Error in api_info command: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="check_rag_entries", description="List all loaded RAG knowledge base entries (Admin only).")
async def check_rag_entries(interaction: discord.Interaction):
    """Show all RAG entries"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        if not RAG_DATABASE:
            await interaction.followup.send("⚠️ No RAG entries loaded. Add some in the dashboard or run /reload.", ephemeral=False)
            return
        
        rag_embed = discord.Embed(
            title="📚 Knowledge Base Entries",
            description=f"Currently loaded: **{len(RAG_DATABASE)} entries**",
            color=0x3498DB
        )
        
        # Show first 10 entries
        entries_to_show = RAG_DATABASE[:10]
        for i, entry in enumerate(entries_to_show, 1):
            title = entry.get('title', 'Unknown')
            keywords = ', '.join(entry.get('keywords', [])[:5])
            rag_embed.add_field(
                name=f"{i}. {title}",
                value=f"Keywords: {keywords}\nID: {entry.get('id', 'N/A')}",
                inline=False
            )
        
        if len(RAG_DATABASE) > 10:
            rag_embed.set_footer(text=f"Showing 10 of {len(RAG_DATABASE)} entries")
        
        await interaction.followup.send(embed=rag_embed, ephemeral=False)
        print(f"check_rag_entries command used by {interaction.user}")
        
    except Exception as e:
        print(f"Error in check_rag_entries: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=False)

@bot.tree.command(name="check_auto_entries", description="List all loaded auto-responses (Admin only).")
async def check_auto_entries(interaction: discord.Interaction):
    """Show all auto-responses"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        if not AUTO_RESPONSES:
            await interaction.followup.send("⚠️ No auto-responses loaded. Add some in the dashboard or run /reload.", ephemeral=False)
            return
        
        auto_embed = discord.Embed(
            title="⚡ Auto-Responses",
            description=f"Currently loaded: **{len(AUTO_RESPONSES)} responses**",
            color=0x5865F2
        )
        
        # Show all auto-responses (usually not too many)
        for i, auto in enumerate(AUTO_RESPONSES, 1):
            name = auto.get('name', 'Unknown')
            triggers = ', '.join(auto.get('triggerKeywords', []))
            response_preview = auto.get('responseText', '')[:100]
            if len(auto.get('responseText', '')) > 100:
                response_preview += '...'
            
            auto_embed.add_field(
                name=f"{i}. {name}",
                value=f"Triggers: {triggers}\nResponse: {response_preview}\nID: {auto.get('id', 'N/A')}",
                inline=False
            )
        
        await interaction.followup.send(embed=auto_embed, ephemeral=False)
        print(f"check_auto_entries command used by {interaction.user}")
        
    except Exception as e:
        print(f"Error in check_auto_entries: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=False)

# REMOVED: No local backups - use /export_data to download complete backup anytime

@bot.tree.command(name="export_data", description="Download backup of all RAG entries and auto-responses (Admin only).")
async def export_data(interaction: discord.Interaction):
    """Export all data as downloadable JSON file"""
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("❌ You need Administrator permission to use this command.", ephemeral=True)
        return
    
    try:
        print(f"📥 Export data requested by {interaction.user}")
        print(f"🔍 DEBUG: Current SYSTEM_PROMPT_TEXT length: {len(SYSTEM_PROMPT_TEXT) if SYSTEM_PROMPT_TEXT else 0}")
        
        # Fetch current data from API
        if 'your-vercel-app' in DATA_API_URL:
            await interaction.followup.send("⚠️ API not configured. Cannot export data.", ephemeral=True)
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.get(DATA_API_URL, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    await interaction.followup.send(f"❌ Failed to fetch data: Status {response.status}", ephemeral=True)
                    return
                
                data = await response.json()
                
                # Create export data with FULL bot settings including system prompt
                full_bot_settings = BOT_SETTINGS.copy()
                if SYSTEM_PROMPT_TEXT:
                    full_bot_settings['systemPrompt'] = SYSTEM_PROMPT_TEXT
                    print(f"✓ Including custom system prompt in export ({len(SYSTEM_PROMPT_TEXT)} characters)")
                else:
                    print(f"⚠ No custom system prompt to export (using default)")
                
                # Show what's in the settings
                print(f"📊 Export will include these settings:")
                for key in full_bot_settings.keys():
                    if key != 'systemPrompt':  # Don't log entire prompt
                        print(f"   - {key}: {full_bot_settings[key]}")
                    else:
                        print(f"   - systemPrompt: {len(full_bot_settings[key])} characters")
                
                export_data = {
                    'export_info': {
                        'timestamp': datetime.now().isoformat(),
                        'exported_by': str(interaction.user),
                        'bot_version': 'RAG-Bot-v2'
                    },
                    'ragEntries': data.get('ragEntries', []),
                    'autoResponses': data.get('autoResponses', []),
                    'slashCommands': data.get('slashCommands', []),
                    'pendingRagEntries': data.get('pendingRagEntries', []),
                    'botSettings': full_bot_settings,
                    'statistics': {
                        'total_rag_entries': len(data.get('ragEntries', [])),
                        'total_auto_responses': len(data.get('autoResponses', [])),
                        'total_slash_commands': len(data.get('slashCommands', [])),
                        'total_pending': len(data.get('pendingRagEntries', [])),
                        'has_custom_prompt': bool(SYSTEM_PROMPT_TEXT)
                    }
                }
                
                # Create filename with timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M%S")
                filename = f"revolution-macro-export-{timestamp}.json"
                
                # Save to temporary file
                temp_path = Path(filename)
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                # Create embed with export info
                export_embed = discord.Embed(
                    title="📦 Data Export Ready",
                    description="Your complete data backup is ready to download!",
                    color=0x2ECC71
                )
                export_embed.add_field(
                    name="📊 Export Contents",
                    value=f"**RAG Entries:** {export_data['statistics']['total_rag_entries']}\n"
                          f"**Auto-Responses:** {export_data['statistics']['total_auto_responses']}\n"
                          f"**Pending Entries:** {export_data['statistics']['total_pending']}\n"
                          f"**Slash Commands:** {export_data['statistics']['total_slash_commands']}\n"
                          f"**Bot Settings:** {len(full_bot_settings)} settings\n"
                          f"**Custom Prompt:** {'✅ Yes' if export_data['statistics']['has_custom_prompt'] else '❌ No'}",
                    inline=False
                )
                export_embed.add_field(
                    name="📅 Export Time",
                    value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    inline=True
                )
                export_embed.add_field(
                    name="📁 Filename",
                    value=f"`{filename}`",
                    inline=True
                )
                export_embed.set_footer(text="💡 Keep this file safe! It contains your entire knowledge base.")
                
                # Send file as attachment
                with open(temp_path, 'rb') as f:
                    file = discord.File(f, filename=filename)
                    await interaction.followup.send(
                        embed=export_embed,
                        file=file,
                        ephemeral=True
                    )
                
                # Clean up temp file
                temp_path.unlink()
                
                print(f"✅ Data exported successfully for {interaction.user}")
        
    except Exception as e:
        print(f"Error in export_data: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Error exporting data: {str(e)}", ephemeral=True)

def has_staff_role(interaction: discord.Interaction) -> bool:
    """Check if user has admin, staff role, or bot permissions role"""
    # Owner has access to everything
    if interaction.user.id == OWNER_USER_ID:
        return True
    if interaction.user.guild_permissions.administrator:
        return True
    # Check for staff role or bot permissions role
    user_roles = [role.id for role in interaction.user.roles]
    return STAFF_ROLE_ID in user_roles or BOT_PERMISSIONS_ROLE_ID in user_roles

def is_staff_or_admin(member: discord.Member) -> bool:
    """Check if a member is staff, admin, or has bot permissions role (for use in message handlers)"""
    if not member:
        return False
    # Owner has access to everything
    if member.id == OWNER_USER_ID:
        return True
    if member.guild_permissions.administrator:
        return True
    # Check for staff role or bot permissions role
    user_roles = [role.id for role in member.roles]
    return STAFF_ROLE_ID in user_roles or BOT_PERMISSIONS_ROLE_ID in user_roles

def is_owner_or_admin(interaction: discord.Interaction) -> bool:
    """Check if user is owner, admin, or has bot permissions role (for admin-only commands)"""
    # Owner has access to everything
    if interaction.user.id == OWNER_USER_ID:
        return True
    if interaction.user.guild_permissions.administrator:
        return True
    # Check for bot permissions role
    user_roles = [role.id for role in interaction.user.roles]
    return BOT_PERMISSIONS_ROLE_ID in user_roles

@bot.tree.command(name="ask", description="Ask the bot a question using the RAG knowledge base (Staff only).")
async def ask(interaction: discord.Interaction, question: str):
    """Staff command to query the RAG knowledge base"""
    await interaction.response.defer(ephemeral=False)
    
    # Check if user has staff role or admin
    if not has_staff_role(interaction):
        await interaction.followup.send("❌ You need the Staff role or Administrator permission to use this command.", ephemeral=True)
        return
    
    try:
        # Check auto-responses first
        auto_response = get_auto_response(question)
        
        if auto_response:
            embed = discord.Embed(
                title="💬 Auto-Response Match",
                description=auto_response,
                color=0x3498DB
            )
            embed.set_footer(text="From Auto-Response Database")
            await interaction.followup.send(embed=embed, ephemeral=False)
            return
        
        # Find relevant RAG entries
        relevant_docs = find_relevant_rag_entries(question)
        
        if relevant_docs:
            # Generate AI response (no images in /ask command)
            ai_response = await generate_ai_response(question, relevant_docs[:2], None)
            
            embed = discord.Embed(
                title="✅ AI Response",
                description=ai_response,
                color=0x2ECC71
            )
            
            # Add knowledge base references
            doc_titles = [doc.get('title', 'Unknown') for doc in relevant_docs[:2]]
            embed.add_field(
                name="📚 Knowledge Base References",
                value="\n".join([f"• {title}" for title in doc_titles]),
                inline=False
            )
            
            embed.set_footer(text=f"Based on {len(relevant_docs)} knowledge base entries")
            await interaction.followup.send(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(
                title="⚠️ No Match Found",
                description="I couldn't find any relevant information in my knowledge base for this question.",
                color=0xE67E22
            )
            embed.set_footer(text="Try rephrasing or adding keywords")
            await interaction.followup.send(embed=embed, ephemeral=False)
            
    except Exception as e:
        print(f"Error in /ask command: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=False)

@bot.tree.command(name="mark_as_solve_no_review", description="Mark thread as solved and lock it WITHOUT creating a RAG entry (Staff only).")
async def mark_as_solve_no_review(interaction: discord.Interaction):
    """Mark thread as solved and lock it without creating RAG entry"""
    await interaction.response.defer(ephemeral=False)
    
    # Check if user has staff role or admin
    if not has_staff_role(interaction):
        await interaction.followup.send("❌ You need the Staff role or Administrator permission to use this command.", ephemeral=True)
        return
    
    try:
        # Must be used in a thread
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.followup.send("⚠ This command must be used inside a forum thread.", ephemeral=True)
            return
        
        thread = interaction.channel
        thread_id = thread.id
        
        # Mark this thread as manually closed with no review (prevents auto-RAG creation)
        global no_review_threads
        no_review_threads.add(thread_id)
        print(f"🚫 Thread {thread_id} marked as no_review - will not create RAG entry")
        
        # Cancel any pending satisfaction timer for this thread
        if thread_id in satisfaction_timers:
            satisfaction_timers[thread_id].cancel()
            del satisfaction_timers[thread_id]
            print(f"⏰ Cancelled satisfaction timer for no_review thread {thread_id}")
        
        # Apply "Resolved" tag and remove "Unsolved" tag if it exists
        try:
            forum_channel = bot.get_channel(SUPPORT_FORUM_CHANNEL_ID)
            if forum_channel:
                resolved_tag = await get_resolved_tag(forum_channel)
                unsolved_tag = await get_unsolved_tag(forum_channel)
                
                current_tags = list(thread.applied_tags)
                
                # Remove unsolved tag if present
                if unsolved_tag and unsolved_tag in current_tags:
                    current_tags.remove(unsolved_tag)
                    print(f"🏷️ Removed '{unsolved_tag.name}' tag from thread {thread_id}")
                
                # Add resolved tag if not present
                if resolved_tag and resolved_tag not in current_tags:
                    current_tags.append(resolved_tag)
                    print(f"🏷️ Applied '{resolved_tag.name}' tag to thread {thread_id}")
                
                # Update tags
                await thread.edit(applied_tags=current_tags)
        except Exception as tag_error:
            print(f"⚠ Could not update tags: {tag_error}")
        
        # Lock and archive the thread
        try:
            await thread.edit(archived=True, locked=True)
            print(f"🔒 Thread {thread_id} locked and archived (manual /mark_as_solve_no_review)")
        except discord.errors.Forbidden:
            await interaction.followup.send(
                "⚠️ I don't have permission to lock the thread.\n\n"
                "**Fix:** Give the bot the **Manage Threads** permission.",
                ephemeral=True
            )
            return
        except Exception as lock_error:
            print(f"❌ Error locking thread: {lock_error}")
            await interaction.followup.send(
                f"⚠️ Error locking thread: {str(lock_error)}",
                ephemeral=True
            )
            return
        
        # Update forum post status in dashboard
        if 'your-vercel-app' not in DATA_API_URL:
            try:
                forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
                async with aiohttp.ClientSession() as session:
                    async with session.get(forum_api_url) as get_response:
                        if get_response.status == 200:
                            all_posts = await get_response.json()
                            current_post = None
                            for p in all_posts:
                                if p.get('postId') == str(thread_id) or p.get('id') == f'POST-{thread_id}':
                                    current_post = p
                                    break
                            
                            if current_post:
                                current_post['status'] = 'Solved'
                                update_payload = {
                                    'action': 'update',
                                    'post': current_post
                                }
                                headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                                async with session.post(forum_api_url, json=update_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as post_response:
                                    if post_response.status == 200:
                                        print(f"✅ Updated forum post status to Solved (no RAG)")
            except Exception as e:
                print(f"⚠ Error updating dashboard: {e}")
        
        # Send success message
        await interaction.followup.send(
            f"✅ Thread marked as **Solved** and locked!\n\n"
            f"🔒 Thread is now closed.\n"
            f"📋 No RAG entry created (as requested).",
            ephemeral=False
        )
        print(f"✓ Thread {thread_id} marked as solved (no RAG) by {interaction.user}")
        
    except Exception as e:
        print(f"Error in mark_as_solve_no_review: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="mark_as_solve", description="Mark thread as solved and send conversation to analyzer (Staff only).")
async def mark_as_solve(interaction: discord.Interaction):
    """Mark a thread as solved and analyze the conversation for RAG entry creation"""
    # Check if user has staff role or admin
    if not has_staff_role(interaction):
        await interaction.response.send_message("❌ You need the Staff role or Administrator permission to use this command.", ephemeral=True)
        return
    
    # Check if this is in a thread
    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message("❌ This command can only be used in a thread.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Fetch all messages from the thread and format them
        messages = []
        async for m in interaction.channel.history(limit=50, oldest_first=False):
            if m.content and not m.content.startswith(IGNORE):
                messages.append(m)
        messages.reverse()  # Oldest to newest
        
        if not messages:
            await interaction.followup.send("❌ No messages found in this thread.", ephemeral=True)
            return
        
        # Format messages using the same logic as fetch_context
        formatted_lines = []
        emoji_pattern = re.compile(r'<a?:([a-zA-Z0-9_]+):\d+>')
        for m in messages:
            author = m.author.display_name
            content = m.content
            
            # Replace mentions with display names
            for user in m.mentions:
                content = content.replace(f"<@{user.id}>", f"<@{user.display_name}>")
                content = content.replace(f"<@!{user.id}>", f"<@{user.display_name}>")
            
            # Replace emojis
            content = emoji_pattern.sub(r'<Emoji: \1>', content)
            
            # Check for attachments
            if m.attachments:
                for attachment in m.attachments:
                    if attachment.content_type and "image" in attachment.content_type:
                        content += " <Media: Image>"
                    else:
                        content += " <Media: File>"
            
            # Replies
            if m.reference and m.reference.resolved:
                replied_to = m.reference.resolved.author.display_name
                formatted_line = f"<@{author}> Replied to <@{replied_to}> with: {content}"
            else:
                formatted_line = f"<@{author}> Said: {content}"
            
            formatted_lines.append(formatted_line)
        
        conversation_text = "\n".join(formatted_lines)
        
        # Analyze conversation to create RAG entry
        await interaction.followup.send("🔍 Analyzing conversation...", ephemeral=True)
        rag_entry = await analyze_conversation(conversation_text)
        
        if rag_entry:
            # Update forum post status to Solved
            thread = interaction.channel
            forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
            data_api_url = DATA_API_URL
            
            if 'your-vercel-app' not in DATA_API_URL:
                try:
                    async with aiohttp.ClientSession() as session:
                        # Update forum post status to Solved
                        async with session.get(forum_api_url) as get_response:
                            current_posts = []
                            if get_response.status == 200:
                                current_posts = await get_response.json()
                            
                            # Find matching post
                            matching_post = None
                            for post in current_posts:
                                if post.get('postId') == str(thread.id) or post.get('id') == f'POST-{thread.id}':
                                    matching_post = post
                                    break
                            
                            if matching_post:
                                # Update post status to Solved
                                matching_post['status'] = 'Solved'
                                
                                post_update = {
                                    'action': 'update',
                                    'post': matching_post
                                }
                                
                                headers = {
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json'
                                }
                                async with session.post(forum_api_url, json=post_update, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as post_response:
                                    if post_response.status == 200:
                                        print(f"✓ Updated forum post status to Solved for thread {thread.id}")
                                    else:
                                        text = await post_response.text()
                                        print(f"⚠ Failed to update forum post status: Status {post_response.status}, Response: {text[:100]}")
            
                        # Create pending RAG entry for review
                        async with session.get(data_api_url) as get_data_response:
                            current_data = {'ragEntries': [], 'autoResponses': [], 'pendingRagEntries': []}
                            if get_data_response.status == 200:
                                current_data = await get_data_response.json()
                            
                            # Create conversation preview for review
                            conversation_preview = conversation_text[:500] + "..." if len(conversation_text) > 500 else conversation_text
                            
                            # Add new PENDING RAG entry
                            new_pending_entry = {
                                'id': f'PENDING-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                                'title': rag_entry.get('title', 'Unknown'),
                                'content': rag_entry.get('content', ''),
                                'keywords': rag_entry.get('keywords', []),
                                'createdAt': datetime.now().isoformat(),
                                'source': f'Staff ({interaction.user.name}) via /mark_as_solve',
                                'threadId': str(thread.id),
                                'conversationPreview': conversation_preview
                            }
                            
                            pending_entries = current_data.get('pendingRagEntries', [])
                            pending_entries.append(new_pending_entry)
                            
                            # Save back to API (include ALL fields to avoid overwriting)
                            save_data = {
                                'ragEntries': current_data.get('ragEntries', []),
                                'autoResponses': current_data.get('autoResponses', []),
                                'slashCommands': current_data.get('slashCommands', []),
                                'botSettings': current_data.get('botSettings', {}),
                                'pendingRagEntries': pending_entries
                            }
                            
                            print(f"💾 Attempting to save pending RAG entry: '{new_pending_entry['title']}'")
                            print(f"   Total pending RAG entries after save: {len(pending_entries)}")
                            
                            async with session.post(data_api_url, json=save_data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as save_response:
                                if save_response.status == 200:
                                    result = await save_response.json()
                                    print(f"✓ Created pending RAG entry for review: '{new_pending_entry['title']}'")
                                    print(f"✓ API response: {result}")
            
                                    # Send success message to user
                                    await interaction.followup.send(
                                        f"✅ Thread marked as solved and RAG entry submitted for review!\n\n"
                                        f"**Title:** {new_pending_entry['title']}\n"
                                        f"**ID:** {new_pending_entry['id']}\n\n"
                                        f"📋 The entry is now **pending review** in the **RAG Management** tab.\n"
                                        f"You can approve or reject it from the dashboard.",
                                        ephemeral=True
                                    )
                                else:
                                    text = await save_response.text()
                                    print(f"⚠ Failed to save pending RAG entry: Status {save_response.status}, Response: {text[:100]}")
                                    await interaction.followup.send(
                                        f"❌ Failed to save pending RAG entry to API.\n"
                                        f"Status: {save_response.status}\n"
                                        f"Response: {text[:200]}",
                                        ephemeral=True
                                    )
            
                except Exception as e:
                    print(f"⚠ Error saving RAG entry: {e}")
                    import traceback
                    traceback.print_exc()
                    await interaction.followup.send(
                        f"❌ Error saving RAG entry: {str(e)}\n"
                        f"Check the console logs for details.",
                        ephemeral=True
                    )
            else:
                # API not configured - show preview but can't save
                entry_preview = f"**Title:** {rag_entry.get('title', 'N/A')}\n"
                entry_preview += f"**Content:** {rag_entry.get('content', 'N/A')[:200]}...\n"
                entry_preview += f"**Keywords:** {', '.join(rag_entry.get('keywords', []))}"
                
                await interaction.followup.send(
                    f"⚠️ API not configured - cannot save RAG entry.\n\n"
                    f"**Generated RAG Entry (preview only):**\n{entry_preview}\n\n"
                    f"Configure DATA_API_URL in .env to enable saving.",
                    ephemeral=True
                )
                print(f"✓ Marked thread {thread.id} as solved but could not save RAG entry (API not configured)")
            
            # Apply "Resolved" tag and remove "Unsolved" tag if it exists
            try:
                thread = interaction.channel
                forum_channel = bot.get_channel(SUPPORT_FORUM_CHANNEL_ID)
                if forum_channel:
                    resolved_tag = await get_resolved_tag(forum_channel)
                    unsolved_tag = await get_unsolved_tag(forum_channel)
                    
                    # Get current tags
                    current_tags = list(thread.applied_tags)
                    
                    # Remove unsolved tag if present
                    if unsolved_tag and unsolved_tag in current_tags:
                        current_tags.remove(unsolved_tag)
                        print(f"🏷️ Removed '{unsolved_tag.name}' tag from thread {thread.id}")
                    
                    # Add resolved tag if not present
                    if resolved_tag and resolved_tag not in current_tags:
                        current_tags.append(resolved_tag)
                        print(f"🏷️ Applied '{resolved_tag.name}' tag to thread {thread.id}")
                    
                    # Update tags
                    await thread.edit(applied_tags=current_tags)
            except Exception as tag_error:
                print(f"⚠ Could not update tags: {tag_error}")
            
            # Lock and archive the thread since it's marked as solved
            try:
                thread = interaction.channel
                await thread.edit(archived=True, locked=True)
                print(f"🔒 Thread {thread.id} locked and archived (manual /mark_as_solve)")
            except discord.errors.Forbidden as perm_error:
                print(f"❌ Bot lacks 'Manage Threads' permission to lock thread {thread.id}")
                print(f"   Error: {perm_error}")
                await interaction.followup.send(
                    "⚠️ Thread marked as solved and RAG entry created, but I don't have permission to lock the thread.\n\n"
                    "**Fix:** Give the bot the **Manage Threads** permission in Server Settings → Roles.",
                    ephemeral=True
                )
            except Exception as lock_error:
                print(f"❌ Error locking thread: {lock_error}")
                import traceback
                traceback.print_exc()
                await interaction.followup.send(
                    f"⚠️ Thread marked as solved but encountered an error locking it: {str(lock_error)}",
                    ephemeral=True
                )
        else:
            await interaction.followup.send("⚠ Failed to analyze conversation. No RAG entry generated.", ephemeral=True)
            print(f"⚠ Failed to generate RAG entry from conversation in thread {interaction.channel.id}")
    
    except Exception as e:
        print(f"Error in mark_as_solve command: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

# --- RUN THE BOT ---
if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)