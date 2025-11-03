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
SYSTEM_PROMPT_TEXT = ""  # Fetched from API, fallback to default if not available

# --- BOT SETTINGS (Local File Storage) ---
BOT_SETTINGS_FILE = Path("bot_settings.json")
BOT_SETTINGS = {
    'support_forum_channel_id': SUPPORT_FORUM_CHANNEL_ID,
    'satisfaction_delay': 15,  # Seconds to wait before analyzing satisfaction
    'ai_temperature': 1.0,  # Gemini temperature (0.0-2.0)
    'ai_max_tokens': 2048,  # Max tokens for AI responses
    'last_updated': datetime.now().isoformat()
}

# --- SATISFACTION ANALYSIS TIMERS ---
# Track pending satisfaction analysis tasks per thread
satisfaction_timers = {}  # {thread_id: asyncio.Task}
# Track processed threads to avoid duplicate processing
processed_threads = set()  # {thread_id}

# --- Local RAG Storage ---
LOCALRAG_DIR = Path("localrag")
LOCALRAG_DIR.mkdir(exist_ok=True)

# --- BOT SETTINGS FUNCTIONS ---
def load_bot_settings():
    """Load bot settings from local file"""
    global BOT_SETTINGS, SUPPORT_FORUM_CHANNEL_ID
    try:
        if BOT_SETTINGS_FILE.exists():
            with open(BOT_SETTINGS_FILE, 'r') as f:
                loaded_settings = json.load(f)
                BOT_SETTINGS.update(loaded_settings)
                # Update the forum channel ID if it's in settings
                if 'support_forum_channel_id' in loaded_settings:
                    SUPPORT_FORUM_CHANNEL_ID = int(loaded_settings['support_forum_channel_id'])
                    print(f"✓ Loaded forum channel ID from settings: {SUPPORT_FORUM_CHANNEL_ID}")
                print(f"✓ Loaded bot settings: satisfaction_delay={BOT_SETTINGS.get('satisfaction_delay', 15)}s, "
                      f"temperature={BOT_SETTINGS.get('ai_temperature', 1.0)}, "
                      f"max_tokens={BOT_SETTINGS.get('ai_max_tokens', 2048)}")
                return True
    except Exception as e:
        print(f"⚠ Error loading bot settings: {e}")
    return False

def save_bot_settings():
    """Save bot settings to local file"""
    try:
        BOT_SETTINGS['last_updated'] = datetime.now().isoformat()
        with open(BOT_SETTINGS_FILE, 'w') as f:
            json.dump(BOT_SETTINGS, f, indent=2)
        print(f"✓ Saved bot settings to {BOT_SETTINGS_FILE}")
        return True
    except Exception as e:
        print(f"⚠ Error saving bot settings: {e}")
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
    "You are the official support bot for Revolution Macro - a professional automation application designed for game macroing and task automation.\n\n"
    
    "KEY FEATURES OF REVOLUTION MACRO:\n"
    "- Automated gathering and resource collection\n"
    "- Smart pathing and navigation systems\n"
    "- Task scheduling and prioritization\n"
    "- Auto-deposit and inventory management\n"
    "- License key activation and management\n"
    "- Custom script support and configuration\n"
    "- Anti-AFK and safety features\n"
    "- Multi-instance support\n\n"
    
    "COMMON ISSUES USERS FACE:\n"
    "- Character resetting during tasks (usually auto-deposit conflicts)\n"
    "- Initialization errors (corrupt config files)\n"
    "- License activation limits (HWID management)\n"
    "- Antivirus false positives (requires exceptions)\n"
    "- Pathing stuck/navigation issues (navmesh recalculation needed)\n"
    "- Settings not saving (file permissions)\n"
    "- Game window detection (must use windowed mode)\n\n"
    
    "YOUR ROLE:\n"
    "1. Provide clear, step-by-step solutions\n"
    "2. Use the knowledge base context when available\n"
    "3. Be friendly but professional\n"
    "4. If uncertain, acknowledge it honestly\n"
    "5. Encourage users to ask follow-up questions\n"
    "6. Never make up features that don't exist\n\n"
    
    "RESPONSE GUIDELINES:\n"
    "- Keep answers concise (2-4 paragraphs max)\n"
    "- Use numbered steps for troubleshooting\n"
    "- Reference specific settings/tabs when relevant\n"
    "- Acknowledge if the question is complex and may need human support\n"
    "- Always be encouraging and supportive"
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
        # Use API system prompt if available, otherwise use default
        system_instruction = SYSTEM_PROMPT_TEXT if SYSTEM_PROMPT_TEXT else SYSTEM_PROMPT
        
        # Get AI settings from bot settings
        temperature = BOT_SETTINGS.get('ai_temperature', 1.0)
        max_tokens = BOT_SETTINGS.get('ai_max_tokens', 2048)
        
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=system_instruction
        )
        
        # Configure generation settings
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        
        # User context separated
        user_context = build_user_context(query, context_entries)
        
        # Generate response with custom settings
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(user_context, generation_config=generation_config)
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
            "Set wants_human to true if:\n"
            "- They explicitly ask for human support, staff, or a real person\n"
            "- They seem frustrated and want to escalate"
        )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, model.generate_content, prompt)
        
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
    
    # Load bot settings from file
    load_bot_settings()
    
    print(f'📡 API Configuration:')
    if 'your-vercel-app' in DATA_API_URL:
        print(f'   ⚠ DATA_API_URL not configured (using placeholder)')
        print(f'   ℹ Set DATA_API_URL in .env file to connect to dashboard')
    else:
        print(f'   ✓ DATA_API_URL: {DATA_API_URL}')
    print(f'📺 Forum Channel ID: {SUPPORT_FORUM_CHANNEL_ID}')
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
    
    # Check if we've already processed this thread (prevent duplicates)
    if thread.id in processed_threads:
        print(f"⚠ Thread {thread.id} already processed, skipping duplicate event")
        return
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

    initial_message = history[0].content
    
    # Send greeting embed AFTER we have the initial message (Discord requirement)
    greeting_embed = discord.Embed(
        title="👋 Welcome to Revolution Macro Support!",
        description=f"Hi {owner_mention}! Thanks for reaching out. I'm analyzing your question and will respond shortly with the best answer I can provide.",
        color=0x5865F2  # Discord blurple color
    )
    greeting_embed.add_field(
        name="⚡ What to Expect",
        value="I'll search our knowledge base and provide a detailed answer. If I can't fully help, I'll connect you with our support team!",
        inline=False
    )
    greeting_embed.set_footer(text="Revolution Macro AI Support • Powered by Gemini", icon_url="https://discord.com/assets/f9bb9c4af2b9c32a2c5ee0014661546d.png")
    
    try:
        await thread.send(embed=greeting_embed)
    except discord.errors.Forbidden as e:
        print(f"⚠ Could not send greeting (Discord restriction): {e}")
        # Continue anyway - the important part is answering the question
    user_question = f"{thread.name}\n{initial_message}"
    
    # Send forum post to dashboard API
    await send_forum_post_to_api(thread, owner_name, owner_id or thread.id, owner_avatar_url, initial_message)

    # --- LOGIC FLOW ---
    # Check auto-responses first
    auto_response = get_auto_response(user_question)
    bot_response_text = None
    
    if auto_response:
        # Send auto-response as professional embed
        auto_embed = discord.Embed(
            title="⚡ Quick Answer",
            description=auto_response,
            color=0x5865F2  # Discord blurple for instant responses
        )
        auto_embed.add_field(
            name="💡 Helpful?",
            value="If you need more assistance, feel free to ask!",
            inline=False
        )
        auto_embed.set_footer(text="Revolution Macro • Instant Answer", icon_url="https://discord.com/assets/f9bb9c4af2b9c32a2c5ee0014661546d.png")
        await thread.send(embed=auto_embed)
        bot_response_text = auto_response
        print(f"⚡ Responded to '{thread.name}' with instant auto-response.")
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
            # Found confident matches in knowledge base
            bot_response_text = await generate_ai_response(user_question, confident_docs[:2])  # Use top 2 confident docs
            
            # Send AI response as professional embed
            ai_embed = discord.Embed(
                title="✅ Revolution Macro Support",
                description=bot_response_text,
                color=0x2ECC71  # Green for successful knowledge base matches
            )
            
            # Add field showing which docs were used
            if len(confident_docs) > 0:
                doc_titles = [doc.get('title', 'Unknown') for doc in confident_docs[:2]]
                ai_embed.add_field(
                    name="📚 Based on Documentation",
                    value="\n".join([f"• {title}" for title in doc_titles]),
                    inline=False
                )
                ai_embed.add_field(
                    name="✨ Need More Help?",
                    value="If this doesn't fully solve your issue, let me know and I can provide more details or connect you with our support team!",
                    inline=False
                )
            
            ai_embed.set_footer(text=f"Revolution Macro AI • Using {len(confident_docs)} knowledge base {'entry' if len(confident_docs) == 1 else 'entries'}", icon_url="https://discord.com/assets/f9bb9c4af2b9c32a2c5ee0014661546d.png")
            await thread.send(embed=ai_embed)
            print(f"✅ Responded to '{thread.name}' with RAG-based answer ({len(confident_docs)} documentation {'match' if len(confident_docs) == 1 else 'matches'}).")
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
                    "You are the official Revolution Macro support bot. Revolution Macro is a professional game automation and macroing application.\n\n"
                    
                    "REVOLUTION MACRO FEATURES:\n"
                    "- Automated gathering/farming for various games\n"
                    "- Smart navigation and pathing\n"
                    "- Task scheduling and queue management\n"
                    "- Auto-deposit to storage/hives\n"
                    "- License key system with HWID protection\n"
                    "- Customizable scripts and settings\n"
                    "- Anti-detection and safety features\n\n"
                    
                    "COMMON SOLUTIONS:\n"
                    f"{context_info}\n\n"
                    
                    f"USER'S QUESTION:\n{user_question}\n\n"
                    
                    "INSTRUCTIONS:\n"
                    "1. Provide helpful, specific advice related to Revolution Macro\n"
                    "2. Use step-by-step format for troubleshooting\n"
                    "3. Reference actual Revolution Macro features and settings\n"
                    "4. If the question is very specific or technical, acknowledge that a support agent can provide detailed assistance\n"
                    "5. Be professional, friendly, and encouraging\n"
                    "6. Keep response to 2-4 paragraphs max\n"
                    "7. NEVER make up features - only reference real Revolution Macro capabilities\n\n"
                    
                    "If you're not confident in your answer, be honest and suggest they ask for more details or request human support."
                )
                
                loop = asyncio.get_event_loop()
                ai_response = await loop.run_in_executor(None, model.generate_content, general_prompt)
                bot_response_text = ai_response.text
                
                # Send general AI response with a professional style
                general_ai_embed = discord.Embed(
                    title="💡 Revolution Macro Support",
                    description=bot_response_text,
                    color=0x5865F2  # Discord blurple for brand consistency
                )
                general_ai_embed.add_field(
                    name="📝 Did this help?",
                    value="If this resolves your issue, great! If you need more specific help, just let me know and I'll connect you with our support team.",
                    inline=False
                )
                general_ai_embed.set_footer(text="Revolution Macro AI Assistant • Powered by Gemini", icon_url="https://discord.com/assets/f9bb9c4af2b9c32a2c5ee0014661546d.png")
                await thread.send(embed=general_ai_embed)
                print(f"💡 Responded to '{thread.name}' with Revolution Macro AI assistance (no specific RAG match).")
                
            except Exception as e:
                print(f"⚠ Error generating general AI response: {e}")
                # Fallback: polite message asking for more info
                bot_response_text = (
                    "I'm not entirely sure about this specific question. Could you provide a bit more detail? "
                    "Or if you'd prefer, I can connect you with our support team who can help!"
                )
                
                fallback_embed = discord.Embed(
                    title="🤔 Need More Information",
                    description=bot_response_text,
                    color=0xF39C12  # Yellow/orange for uncertainty
                )
                fallback_embed.set_footer(text="Revolution Macro Support")
                await thread.send(embed=fallback_embed)
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
                    new_message = {
                        'author': 'Bot' if is_bot_message else 'User',
                        'content': message.content if message.content else '[Embed message]',
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
                        new_status = matching_post.get('status', 'Unsolved')
                        if not is_bot_message and has_bot_response and matching_post.get('status') not in ['Solved', 'Closed']:
                            # Cancel any existing timer for this thread
                            thread_id = thread.id
                            if thread_id in satisfaction_timers:
                                satisfaction_timers[thread_id].cancel()
                                print(f"⏰ Cancelled previous satisfaction timer for thread {thread_id}")
                            
                            # Create delayed analysis task (configurable delay)
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
                                    
                                    if satisfaction.get('wants_human'):
                                        # User explicitly wants human support
                                        updated_status = 'Human Support'
                                        
                                        # Send human support embed
                                        human_embed = discord.Embed(
                                            title="👨‍💼 Connecting You with Our Support Team",
                                            description="I understand you'd like to speak with a member of our support team. No problem! Your request has been escalated and our team has been notified.",
                                            color=0x3498DB  # Blue color
                                        )
                                        human_embed.add_field(
                                            name="⏱️ What Happens Next",
                                            value="A Revolution Macro support team member will review your question and respond as soon as possible. Response times are typically under 24 hours.",
                                            inline=False
                                        )
                                        human_embed.add_field(
                                            name="💡 While You Wait",
                                            value="Feel free to add any additional details or screenshots that might help our team assist you better!",
                                            inline=False
                                        )
                                        human_embed.set_footer(text="Revolution Macro Support Team • Human assistance requested")
                                        await thread_channel.send(embed=human_embed)
                                        print(f"👥 User requested human support - thread {thread_id} escalated to staff")
                                        
                                    elif satisfaction.get('satisfied') and satisfaction.get('confidence', 0) > 60:
                                        # User is satisfied - mark as solved
                                        updated_status = 'Solved'
                                        
                                        # Send satisfaction confirmation embed
                                        confirm_embed = discord.Embed(
                                            title="✅ Awesome! Issue Resolved",
                                            description="I'm glad I could help you with this issue! This ticket has been automatically marked as **Solved** and will be locked to keep things organized.",
                                            color=0x2ECC71
                                        )
                                        confirm_embed.add_field(
                                            name="💬 Need More Help?",
                                            value="If you have any other questions, feel free to create a new post anytime. We're here to help!",
                                            inline=False
                                        )
                                        confirm_embed.set_footer(text="Revolution Macro Support • Satisfaction detected automatically")
                                        await thread_channel.send(embed=confirm_embed)
                                        print(f"✅ User satisfaction detected - marking thread {thread_id} as Solved")
                                        
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
                                        
                                        # Automatically create RAG entry from this solved conversation
                                        try:
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
                                            
                                            if rag_entry and 'your-vercel-app' not in DATA_API_URL:
                                                # Save to knowledge base
                                                data_api_url_rag = DATA_API_URL
                                                
                                                async with aiohttp.ClientSession() as rag_session:
                                                    async with rag_session.get(data_api_url_rag) as get_data_response:
                                                        current_data = {'ragEntries': [], 'autoResponses': [], 'slashCommands': []}
                                                        if get_data_response.status == 200:
                                                            current_data = await get_data_response.json()
                                                        
                                                        # Create new RAG entry
                                                        new_rag_entry = {
                                                            'id': f'RAG-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                                                            'title': rag_entry.get('title', 'Auto-generated from solved thread'),
                                                            'content': rag_entry.get('content', ''),
                                                            'keywords': rag_entry.get('keywords', []),
                                                            'createdAt': datetime.now().isoformat(),
                                                            'createdBy': 'Auto-created by bot (user satisfied)'
                                                        }
                                                        
                                                        rag_entries = current_data.get('ragEntries', [])
                                                        rag_entries.append(new_rag_entry)
                                                        
                                                        # Save to API (must include ALL fields)
                                                        save_data = {
                                                            'ragEntries': rag_entries,
                                                            'autoResponses': current_data.get('autoResponses', []),
                                                            'slashCommands': current_data.get('slashCommands', []),
                                                            'botSettings': current_data.get('botSettings', {})
                                                        }
                                                        
                                                        print(f"💾 Saving RAG entry to API...")
                                                        print(f"   Total entries to save: {len(rag_entries)}")
                                                        print(f"   New entry: '{new_rag_entry['title']}'")
                                                        
                                                        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                                                        async with rag_session.post(data_api_url_rag, json=save_data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as save_response:
                                                            response_text = await save_response.text()
                                                            if save_response.status == 200:
                                                                print(f"✅ Auto-created RAG entry: '{new_rag_entry['title']}'")
                                                                print(f"   API response: {response_text[:200]}")
                                                                
                                                                # Update local RAG database
                                                                global RAG_DATABASE
                                                                RAG_DATABASE.append(new_rag_entry)
                                                                
                                                                # Download to local RAG
                                                                await download_rag_to_local()
                                                                
                                                                # Send notification in thread
                                                                rag_notification = discord.Embed(
                                                                    title="📚 Knowledge Base Enhanced!",
                                                                    description="Your conversation has been automatically added to our knowledge base! This means future users with similar questions will get help even faster. Thank you for helping improve Revolution Macro support!",
                                                                    color=0x9B59B6
                                                                )
                                                                rag_notification.add_field(
                                                                    name="✨ New Documentation Entry",
                                                                    value=f"**{new_rag_entry['title']}**\n\nThis will now help other users facing similar issues!",
                                                                    inline=False
                                                                )
                                                                rag_notification.set_footer(text="Revolution Macro Learning System • Automatically generated")
                                                                await thread_channel.send(embed=rag_notification)
                                                            else:
                                                                print(f"❌ Failed to auto-create RAG entry!")
                                                                print(f"   Status: {save_response.status}")
                                                                print(f"   Response: {response_text[:300]}")
                                                                print(f"   URL: {data_api_url_rag}")
                                                                print(f"   Payload: {len(rag_entries)} RAG entries")
                                            else:
                                                print(f"ℹ Skipping RAG entry creation (no entry generated or API not configured)")
                                        except Exception as rag_error:
                                            print(f"⚠ Error auto-creating RAG entry: {rag_error}")
                                            import traceback
                                            traceback.print_exc()
                                        
                                    elif not satisfaction.get('satisfied') and satisfaction.get('confidence', 0) > 60:
                                        # User needs more help - escalate to human
                                        updated_status = 'Human Support'
                                        
                                        # Send escalation embed
                                        escalate_embed = discord.Embed(
                                            title="🔄 Escalating to Support Team",
                                            description="I noticed my previous answer might not have fully resolved your issue. No worries! I've escalated your question to our human support team for more personalized assistance.",
                                            color=0xE67E22
                                        )
                                        escalate_embed.add_field(
                                            name="👨‍💼 Next Steps",
                                            value="A Revolution Macro support team member will review the conversation and provide a more detailed solution shortly.",
                                            inline=False
                                        )
                                        escalate_embed.add_field(
                                            name="📝 Help Us Help You",
                                            value="If you have any error messages, screenshots, or additional details, feel free to share them now!",
                                            inline=False
                                        )
                                        escalate_embed.set_footer(text="Revolution Macro Support • AI-detected escalation needed")
                                        await thread_channel.send(embed=escalate_embed)
                                        print(f"⚠ User needs more help - escalating thread {thread_id} to Human Support")
                                    
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
                            
                            # Store the task
                            satisfaction_timers[thread_id] = asyncio.create_task(delayed_satisfaction_check())
                            delay = BOT_SETTINGS.get('satisfaction_delay', 15)
                            print(f"⏰ Started {delay}-second satisfaction timer for thread {thread_id}")
                        
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
@app_commands.default_permissions(administrator=True)
async def stop(interaction: discord.Interaction):
    await interaction.response.send_message("🛑 Shutting down Revolution Macro bot...", ephemeral=True)
    print(f"Stop command issued by {interaction.user}. Shutting down in 2 seconds...")
    
    # Give time for response to send, then close
    await asyncio.sleep(2)
    print("Closing bot connection...")
    await bot.close()
    print("Bot stopped successfully.")

@bot.tree.command(name="reload", description="Reloads data from dashboard (Admin only).")
@app_commands.default_permissions(administrator=True)
async def reload(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    success = await fetch_data_from_api()
    if success:
        count = await download_rag_to_local()
        await interaction.followup.send(f"✅ Data reloaded successfully from dashboard! Downloaded {count} RAG entries to localrag/.", ephemeral=False)
    else:
        await interaction.followup.send("⚠️ Failed to reload data. Using cached data.", ephemeral=False)
    print(f"Reload command issued by {interaction.user}.")

@bot.tree.command(name="set_forums_id", description="Set the support forum channel ID for the bot to monitor (Admin only).")
@app_commands.default_permissions(administrator=True)
async def set_forums_id(interaction: discord.Interaction, channel_id: str):
    """Set the forum channel ID and save to settings file"""
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
        BOT_SETTINGS['support_forum_channel_id'] = new_channel_id
        
        # Save to file
        if save_bot_settings():
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

@bot.tree.command(name="set_satisfaction_delay", description="Set the delay (in seconds) before analyzing user satisfaction (Admin only).")
@app_commands.default_permissions(administrator=True)
async def set_satisfaction_delay(interaction: discord.Interaction, seconds: int):
    """Set the satisfaction analysis delay"""
    await interaction.response.defer(ephemeral=False)
    
    try:
        if seconds < 5 or seconds > 300:
            await interaction.followup.send("❌ Delay must be between 5 and 300 seconds.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        BOT_SETTINGS['satisfaction_delay'] = seconds
        
        if save_bot_settings():
            await interaction.followup.send(
                f"✅ Satisfaction delay updated to **{seconds} seconds**!\n\n"
                f"The bot will now wait {seconds} seconds after a user's last message before analyzing their satisfaction.",
                ephemeral=False
            )
            print(f"✓ Satisfaction delay updated to {seconds} seconds by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to file.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_satisfaction_delay: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_temperature", description="Set the AI temperature (0.0-2.0) for response generation (Admin only).")
@app_commands.default_permissions(administrator=True)
async def set_temperature(interaction: discord.Interaction, temperature: float):
    """Set the AI temperature"""
    await interaction.response.defer(ephemeral=False)
    
    try:
        if temperature < 0.0 or temperature > 2.0:
            await interaction.followup.send("❌ Temperature must be between 0.0 and 2.0.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        BOT_SETTINGS['ai_temperature'] = temperature
        
        if save_bot_settings():
            temp_desc = "more focused/deterministic" if temperature < 0.7 else "more creative/varied" if temperature > 1.3 else "balanced"
            await interaction.followup.send(
                f"✅ AI temperature updated to **{temperature}**!\n\n"
                f"Responses will be **{temp_desc}**.\n"
                f"Lower = more consistent, Higher = more creative",
                ephemeral=False
            )
            print(f"✓ AI temperature updated to {temperature} by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to file.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_temperature: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_max_tokens", description="Set the maximum tokens for AI responses (Admin only).")
@app_commands.default_permissions(administrator=True)
async def set_max_tokens(interaction: discord.Interaction, max_tokens: int):
    """Set the maximum tokens for AI responses"""
    await interaction.response.defer(ephemeral=False)
    
    try:
        if max_tokens < 100 or max_tokens > 8192:
            await interaction.followup.send("❌ Max tokens must be between 100 and 8192.", ephemeral=False)
            return
        
        global BOT_SETTINGS
        BOT_SETTINGS['ai_max_tokens'] = max_tokens
        
        if save_bot_settings():
            length_desc = "shorter" if max_tokens < 1024 else "longer" if max_tokens > 3072 else "medium"
            await interaction.followup.send(
                f"✅ Max tokens updated to **{max_tokens}**!\n\n"
                f"Responses will be **{length_desc}** (approximately {max_tokens // 4} words max).",
                ephemeral=False
            )
            print(f"✓ Max tokens updated to {max_tokens} by {interaction.user}")
        else:
            await interaction.followup.send("⚠️ Failed to save settings to file.", ephemeral=False)
    except Exception as e:
        print(f"Error in set_max_tokens: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="status", description="Check bot status and current configuration (Admin only).")
@app_commands.default_permissions(administrator=True)
async def status(interaction: discord.Interaction):
    """Show bot status and configuration"""
    await interaction.response.defer(ephemeral=False)
    
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
            name="⏱️ Timers",
            value=f"**Satisfaction Delay:** {BOT_SETTINGS.get('satisfaction_delay', 15)}s\n**Active Timers:** {active_timers}",
            inline=True
        )
        
        status_embed.add_field(
            name="📺 Forum Channel",
            value=channel_info,
            inline=False
        )
        
        status_embed.add_field(
            name="📡 API Connection",
            value=f"{api_status}\n{DATA_API_URL if 'your-vercel-app' not in DATA_API_URL else 'Not configured'}",
            inline=False
        )
        
        status_embed.add_field(
            name="🧠 System Prompt",
            value=f"Using {'custom' if SYSTEM_PROMPT_TEXT else 'default'} prompt ({len(SYSTEM_PROMPT_TEXT or SYSTEM_PROMPT)} characters)",
            inline=False
        )
        
        status_embed.set_footer(text=f"Last updated: {BOT_SETTINGS.get('last_updated', 'Never')}")
        
        await interaction.followup.send(embed=status_embed, ephemeral=False)
        print(f"Status command used by {interaction.user}")
        
    except Exception as e:
        print(f"Error in status command: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=False)

@bot.tree.command(name="check_rag_entries", description="List all loaded RAG knowledge base entries (Admin only).")
@app_commands.default_permissions(administrator=True)
async def check_rag_entries(interaction: discord.Interaction):
    """Show all RAG entries"""
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
@app_commands.default_permissions(administrator=True)
async def check_auto_entries(interaction: discord.Interaction):
    """Show all auto-responses"""
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

@bot.tree.command(name="ask", description="Ask the bot a question using the RAG knowledge base (Staff only).")
@app_commands.default_permissions(administrator=True)
async def ask(interaction: discord.Interaction, question: str):
    """Staff command to query the RAG knowledge base"""
    await interaction.response.defer(ephemeral=False)
    
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
            # Generate AI response
            ai_response = await generate_ai_response(question, relevant_docs[:2])
            
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
                        
                        # Save RAG entry to knowledge base
                        async with session.get(data_api_url) as get_data_response:
                            current_data = {'ragEntries': [], 'autoResponses': []}
                            if get_data_response.status == 200:
                                current_data = await get_data_response.json()
                            
                            # Add new RAG entry
                            new_rag_entry = {
                                'id': f'RAG-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                                'title': rag_entry.get('title', 'Unknown'),
                                'content': rag_entry.get('content', ''),
                                'keywords': rag_entry.get('keywords', []),
                                'createdAt': datetime.now().isoformat(),
                                'createdBy': f'{interaction.user.name} (via /mark_as_solve)'
                            }
                            
                            rag_entries = current_data.get('ragEntries', [])
                            rag_entries.append(new_rag_entry)
                            
                            # Save back to API (include ALL fields to avoid overwriting)
                            save_data = {
                                'ragEntries': rag_entries,
                                'autoResponses': current_data.get('autoResponses', []),
                                'slashCommands': current_data.get('slashCommands', [])
                            }
                            
                            print(f"💾 Attempting to save RAG entry: '{new_rag_entry['title']}'")
                            print(f"   Total RAG entries after save: {len(rag_entries)}")
                            
                            async with session.post(data_api_url, json=save_data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as save_response:
                                if save_response.status == 200:
                                    result = await save_response.json()
                                    print(f"✓ Saved new RAG entry to knowledge base: '{new_rag_entry['title']}'")
                                    print(f"✓ API response: {result}")
                                    
                                    # Update local RAG database
                                    global RAG_DATABASE
                                    RAG_DATABASE.append(new_rag_entry)
                                    
                                    # Download to local RAG
                                    await download_rag_to_local()
                                    
                                    # Send success message to user
                                    await interaction.followup.send(
                                        f"✅ Thread marked as solved and RAG entry saved!\n\n"
                                        f"**Title:** {new_rag_entry['title']}\n"
                                        f"**ID:** {new_rag_entry['id']}\n\n"
                                        f"You can view it in the **RAG Management** tab on the dashboard.",
                                        ephemeral=True
                                    )
                                else:
                                    text = await save_response.text()
                                    print(f"⚠ Failed to save RAG entry: Status {save_response.status}, Response: {text[:100]}")
                                    await interaction.followup.send(
                                        f"❌ Failed to save RAG entry to API.\n"
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