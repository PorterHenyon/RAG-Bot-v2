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

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
# Note: Thread intents are included in default() for discord.py >= 2.0
# Thread detection works automatically with these intents
bot = commands.Bot(command_prefix="!unused-prefix!", intents=intents)

# --- Constants ---
IGNORE = "!"  # Messages starting with this prefix are ignored

# --- DATA STORAGE (Synced from Dashboard) ---
RAG_DATABASE = []
AUTO_RESPONSES = []

# --- Local RAG Storage ---
LOCALRAG_DIR = Path("localrag")
LOCALRAG_DIR.mkdir(exist_ok=True)

# --- DATA SYNC FUNCTIONS ---
async def fetch_data_from_api():
    """Fetch RAG entries and auto-responses from the dashboard API"""
    global RAG_DATABASE, AUTO_RESPONSES
    
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
                    
                    # Check if data actually changed (count or content) - BEFORE updating
                    old_rag_count = len(RAG_DATABASE)
                    old_auto_count = len(AUTO_RESPONSES)
                    old_auto_ids = {a.get('id') for a in AUTO_RESPONSES if a.get('id')}
                    rag_changed = len(new_rag) != old_rag_count
                    auto_changed = len(new_auto) != old_auto_count
                    
                    # Update data
                    RAG_DATABASE = new_rag
                    AUTO_RESPONSES = new_auto
                    
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

# --- Local RAG Functions ---
async def download_rag_to_local():
    """Download RAG entries to local files"""
    try:
        # Clear existing local files
        for file in LOCALRAG_DIR.glob("*.txt"):
            file.unlink()
        
        # Write each RAG entry to a file
        for entry in RAG_DATABASE:
            entry_id = entry.get('id', f"RAG-{hash(entry.get('title', 'unknown'))}")
            filename = f"{entry_id}.txt"
            filepath = LOCALRAG_DIR / filename
            
            content = f"Title: {entry.get('title', '')}\n"
            content += f"Content: {entry.get('content', '')}\n"
            content += f"Keywords: {', '.join(entry.get('keywords', []))}"
            
            filepath.write_text(content, encoding='utf-8')
        
        print(f"✓ Downloaded {len(RAG_DATABASE)} RAG entries to localrag/")
        return len(RAG_DATABASE)
    except Exception as e:
        print(f"⚠ Error downloading RAG to local: {e}")
        return 0

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
    # Filter out short words (less than 3 chars) for better matching
    query_words = set(query.lower().split())
    query_words = {word for word in query_words if len(word) > 2}
    
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
    "You are an expert support bot for a macroing application called 'Revolution Macro'. "
    "Using the context from the knowledge base provided in user messages, provide helpful and friendly answers. "
    "If the context is highly relevant, you can reference the documentation by title in your response."
)

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

async def generate_ai_response(query, context_entries):
    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=SYSTEM_PROMPT
        )
        
        # User context separated
        user_context = build_user_context(query, context_entries)
        
        # Generate response
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            model.generate_content,
            user_context
        )
        return response.text
    except Exception as e:
        print(f"An error occurred with the Gemini API: {e}")
        return "I'm sorry, I'm having trouble connecting to my AI brain right now. A human will be with you shortly."

async def analyze_conversation(conversation_text):
    """Analyze a conversation and create a RAG entry from it"""
    try:
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

# --- PERIODIC DATA SYNC ---
@tasks.loop(hours=1)  # Sync every hour
async def sync_data_task():
    """Periodically sync data from the dashboard"""
    await fetch_data_from_api()
    # Also download to local RAG after syncing
    await download_rag_to_local()

@sync_data_task.before_loop
async def before_sync_task():
    await bot.wait_until_ready()

# --- BOT EVENTS ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('-------------------')
    print(f'📡 API Configuration:')
    if 'your-vercel-app' in DATA_API_URL:
        print(f'   ⚠ DATA_API_URL not configured (using placeholder)')
        print(f'   ℹ Set DATA_API_URL in .env file to connect to dashboard')
    else:
        print(f'   ✓ DATA_API_URL: {DATA_API_URL}')
    print('-------------------')
    
    # Initial data sync
    await fetch_data_from_api()
    # Initial local RAG download
    await download_rag_to_local()
    
    # Start periodic sync
    sync_data_task.start()
    
    try:
        synced = await bot.tree.sync()
        print(f'✓ Slash commands synced ({len(synced)} commands).')
    except Exception as e:
        print(f'⚠ Failed to sync commands: {e}')
    
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
                'status': 'Unsolved',
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
    await thread.send(f"Hi {owner_mention}, thanks for your question! I'm analyzing it now...")

    history = [message async for message in thread.history(limit=1, oldest_first=True)]
    if not history:
        return

    initial_message = history[0].content
    user_question = f"{thread.name}\n{initial_message}"
    
    # Send forum post to dashboard API
    await send_forum_post_to_api(thread, owner_name, owner_id or thread.id, owner_avatar_url, initial_message)

    # --- LOGIC FLOW ---
    # Check auto-responses first
    auto_response = get_auto_response(user_question)
    bot_response_text = None
    
    if auto_response:
        await thread.send(auto_response)
        bot_response_text = auto_response
        print(f"✓ Responded to '{thread.name}' with an auto-response.")
    else:
        relevant_docs = find_relevant_rag_entries(user_question)
        
        # Use a score threshold similar to dashboard (score of 5 = title match minimum)
        # Lower threshold to 3 to catch keyword matches (not just title matches)
        SCORE_THRESHOLD = 3  # Minimum confidence threshold (allows keyword matches)
        confident_docs = []
        
        # Recalculate scores to filter by threshold
        query_words = set(user_question.lower().split())
        query_words = {word for word in query_words if len(word) > 2}
        
        if not query_words:
            # If no words > 2 chars, try with all words (might be short keywords like "api")
            query_words = set(user_question.lower().split())
        
        print(f"🔍 Searching for matches with query words: {query_words}")
        
        for entry in relevant_docs:
            score = 0
            entry_title = entry.get('title', '').lower()
            entry_keywords = ' '.join(entry.get('keywords', [])).lower()
            entry_content = entry.get('content', '').lower()
            
            for word in query_words:
                if word in entry_title:
                    score += 5
                if word in entry_keywords:
                    score += 3
                if word in entry_content:
                    score += 1
            
            if score >= SCORE_THRESHOLD:
                confident_docs.append(entry)
                print(f"   ✓ Match found: '{entry.get('title', 'Unknown')}' (score: {score})")
        
        if not confident_docs and relevant_docs:
            print(f"⚠ No entries met threshold ({SCORE_THRESHOLD}). Top matches:")
            # Show top 3 scores even if below threshold
            query_words = set(user_question.lower().split())
            query_words = {word for word in query_words if len(word) > 2} if {word for word in query_words if len(word) > 2} else set(user_question.lower().split())
            
            scored_entries = []
            for entry in relevant_docs[:5]:  # Check top 5
                score = 0
                entry_title = entry.get('title', '').lower()
                entry_keywords = ' '.join(entry.get('keywords', [])).lower()
                entry_content = entry.get('content', '').lower()
                
                for word in query_words:
                    if word in entry_title:
                        score += 5
                    if word in entry_keywords:
                        score += 3
                    if word in entry_content:
                        score += 1
                
                scored_entries.append({'entry': entry, 'score': score})
            
            scored_entries.sort(key=lambda x: x['score'], reverse=True)
            for item in scored_entries[:3]:
                print(f"     - '{item['entry'].get('title', 'Unknown')}' (score: {item['score']})")

        if confident_docs:
            bot_response_text = await generate_ai_response(user_question, confident_docs[:2])  # Use top 2 confident docs
            await thread.send(bot_response_text)
            print(f"Responded to '{thread.name}' with a RAG-based AI answer ({len(confident_docs)} confident matches).")
        else:
            escalation_message = (
                "I'm sorry, I couldn't find a confident answer in my knowledge base. "
                "I've flagged this for a human support agent to review."
            )
            await thread.send(escalation_message)
            bot_response_text = escalation_message
            print(f"Could not find a confident answer for '{thread.name}'. Escalated.")
    
        # Update forum post in API with bot response (must include all post data for full update)
        if bot_response_text and 'your-vercel-app' not in DATA_API_URL:
            print(f"🔗 Updating forum post with bot response...")
            try:
                # Determine status based on response type
                post_status = 'AI Response' if auto_response or (bot_response_text != "I'm sorry, I couldn't find a confident answer in my knowledge base. I've flagged this for a human support agent to review.") else 'Human Support'
                
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
    
    # Skip bot's own messages to avoid loops
    if message.author == bot.user:
        await bot.process_commands(message)
        return
    
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
                    new_message = {
                        'author': 'User',
                        'content': message.content,
                        'timestamp': message.created_at.isoformat() if hasattr(message.created_at, 'isoformat') else datetime.now().isoformat()
                    }
                    
                    if matching_post:
                        # Update existing post
                        conversation = matching_post.get('conversation', [])
                        conversation.append(new_message)
                        
                        post_update = {
                            'action': 'update',
                            'post': {
                                **matching_post,
                                'conversation': conversation
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
@app_commands.default_permissions(administrator=True)
async def stop(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down...", ephemeral=True)
    print(f"Stop command issued by {interaction.user}. Shutting down.")
    await bot.close()

@bot.tree.command(name="reload", description="Reloads data from dashboard (Admin only).")
@app_commands.default_permissions(administrator=True)
async def reload(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    success = await fetch_data_from_api()
    if success:
        count = await download_rag_to_local()
        await interaction.followup.send(f"✓ Data reloaded successfully from dashboard! Downloaded {count} RAG entries to localrag/.", ephemeral=True)
    else:
        await interaction.followup.send("⚠ Failed to reload data. Using cached data.", ephemeral=True)
    print(f"Reload command issued by {interaction.user}.")

@bot.tree.command(name="mark_as_solve", description="Mark thread as solved and send conversation to analyzer (Staff only).")
@app_commands.default_permissions(administrator=True)
async def mark_as_solve(interaction: discord.Interaction):
    """Mark a thread as solved and analyze the conversation for RAG entry creation"""
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
            
            if 'your-vercel-app' not in DATA_API_URL:
                try:
                    # Get current post
                    async with aiohttp.ClientSession() as session:
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
            
                except Exception as e:
                    print(f"⚠ Error updating forum post status: {e}")
            
            # Return the RAG entry for staff to review
            entry_preview = f"**Title:** {rag_entry.get('title', 'N/A')}\n"
            entry_preview += f"**Content:** {rag_entry.get('content', 'N/A')[:200]}...\n"
            entry_preview += f"**Keywords:** {', '.join(rag_entry.get('keywords', []))}"
            
            await interaction.followup.send(
                f"✅ Thread marked as solved!\n\n"
                f"**Generated RAG Entry:**\n{entry_preview}\n\n"
                f"You can add this to the RAG database from the dashboard.",
                ephemeral=True
            )
            print(f"✓ Marked thread {thread.id} as solved and analyzed conversation")
        else:
            await interaction.followup.send("⚠ Failed to analyze conversation. Thread status updated but no RAG entry generated.", ephemeral=True)
    
    except Exception as e:
        print(f"Error in mark_as_solve command: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

# --- RUN THE BOT ---
if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)