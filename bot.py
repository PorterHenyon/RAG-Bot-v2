import os
import asyncio
import json
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
bot = commands.Bot(command_prefix="!unused-prefix!", intents=intents)

# --- DATA STORAGE (Synced from Dashboard) ---
RAG_DATABASE = []
AUTO_RESPONSES = []

# --- DATA SYNC FUNCTIONS ---
async def fetch_data_from_api():
    """Fetch RAG entries and auto-responses from the dashboard API"""
    global RAG_DATABASE, AUTO_RESPONSES
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATA_API_URL}") as response:
                if response.status == 200:
                    data = await response.json()
                    RAG_DATABASE = data.get('ragEntries', [])
                    AUTO_RESPONSES = data.get('autoResponses', [])
                    print(f"✓ Synced {len(RAG_DATABASE)} RAG entries and {len(AUTO_RESPONSES)} auto-responses from dashboard.")
                    return True
                else:
                    print(f"⚠ Failed to fetch data from API: Status {response.status}")
                    return False
    except Exception as e:
        print(f"⚠ Error fetching data from API: {e}")
        # Fall back to local data if API fails
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

# --- CORE BOT LOGIC (MIRRORS PLAYGROUND) ---
def get_auto_response(query):
    for response in AUTO_RESPONSES:
        for keyword in response['triggerKeywords']:
            if keyword in query.lower():
                return response['responseText']
    return None

def find_relevant_rag_entries(query, db=RAG_DATABASE):
    query_words = set(query.lower().split())
    scored_entries = []
    for entry in db:
        score = 0
        # Combine all text fields for searching
        search_text = f"{entry['title']} {entry['content']} {' '.join(entry['keywords'])}".lower()
        for word in query_words:
            if word in search_text:
                score += 1
        if score > 0:
            scored_entries.append({'entry': entry, 'score': score})
    scored_entries.sort(key=lambda x: x['score'], reverse=True)
    return [item['entry'] for item in scored_entries]

async def generate_ai_response(query, context_entries):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        context_text = "\n\n".join(
            [f"Title: {entry['title']}\nContent: {entry['content']}" for entry in context_entries]
        )

        prompt = (
            "You are an expert support bot for a complex scripting application called 'Revolution Macro'. "
            "A user has the following question:\n"
            f"\"\"\"{query}\"\"\"\n\n"
            "Using the following context from the knowledge base, provide a helpful and friendly answer. "
            "If the context is highly relevant, you can start with: "
            f"\"Based on our documentation for '{context_entries[0]['title']}', here's what I found:\"\n\n"
            f"Context:\n{context_text}"
        )

        # Run the synchronous generate_content in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, model.generate_content, prompt)
        return response.text
    except Exception as e:
        print(f"An error occurred with the Gemini API: {e}")
        return "I'm sorry, I'm having trouble connecting to my AI brain right now. A human will be with you shortly."

# --- PERIODIC DATA SYNC ---
@tasks.loop(minutes=5)
async def sync_data_task():
    """Periodically sync data from the dashboard"""
    await fetch_data_from_api()

@sync_data_task.before_loop
async def before_sync_task():
    await bot.wait_until_ready()

# --- BOT EVENTS ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    
    # Initial data sync
    await fetch_data_from_api()
    
    # Start periodic sync
    sync_data_task.start()
    
    try:
        synced = await bot.tree.sync()
        print(f'✓ Slash commands synced ({len(synced)} commands).')
    except Exception as e:
        print(f'⚠ Failed to sync commands: {e}')
    
    print('Bot is ready and listening for new forum posts.')
    print('-------------------')

@bot.event
async def on_thread_create(thread):
    if thread.parent_id != SUPPORT_FORUM_CHANNEL_ID:
        return

    # Safely get owner information
    owner_name = "Unknown"
    owner_mention = "there"
    
    try:
        if thread.owner:
            owner_name = getattr(thread.owner, 'name', 'Unknown')
            owner_mention = getattr(thread.owner, 'mention', 'there')
        elif hasattr(thread, 'owner_id') and thread.owner_id:
            try:
                owner = await bot.fetch_user(thread.owner_id)
                owner_name = owner.name
                owner_mention = owner.mention
            except Exception:
                pass
    except Exception as e:
        print(f"⚠ Could not get thread owner: {e}")

    print(f"New forum post created: '{thread.name}' by {owner_name}")
    await thread.send(f"Hi {owner_mention}, thanks for your question! I'm analyzing it now...")

    history = [message async for message in thread.history(limit=1, oldest_first=True)]
    if not history:
        return

    user_question = f"{thread.name}\n{history[0].content}"

    # --- LOGIC FLOW ---
    auto_response = get_auto_response(user_question)
    if auto_response:
        await thread.send(auto_response)
        print(f"Responded to '{thread.name}' with an auto-response.")
        return

    relevant_docs = find_relevant_rag_entries(user_question)

    if relevant_docs:
        bot_response_text = await generate_ai_response(user_question, relevant_docs[:2])  # Use top 2 docs
        await thread.send(bot_response_text)
        print(f"Responded to '{thread.name}' with a RAG-based AI answer.")
    else:
        escalation_message = (
            "I'm sorry, I couldn't find a confident answer in my knowledge base. "
            "I've flagged this for a human support agent to review."
        )
        await thread.send(escalation_message)
        print(f"Could not find a confident answer for '{thread.name}'. Escalated.")

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
        await interaction.followup.send("✓ Data reloaded successfully from dashboard!", ephemeral=True)
    else:
        await interaction.followup.send("⚠ Failed to reload data. Using cached data.", ephemeral=True)
    print(f"Reload command issued by {interaction.user}.")

# --- RUN THE BOT ---
if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
