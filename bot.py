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
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("⚠️ Pinecone not installed - install with: pip install pinecone")
except Exception as e:
    # Handle case where pinecone-client is still installed (conflict)
    PINECONE_AVAILABLE = False
    print(f"⚠️ Pinecone import error: {e}")
    print("   Remove pinecone-client and install pinecone: pip uninstall pinecone-client && pip install pinecone")

# --- Configuration ---
load_dotenv()

# COST OPTIMIZATION: Prefer Pinecone when available (saves Railway CPU costs)
# Pinecone Configuration
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'rag-bot-index')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')  # Default to us-east-1
# Optional: skip embedding bootstrap on this worker to avoid CPU/memory load
SKIP_EMBEDDING_BOOTSTRAP = os.getenv('SKIP_EMBEDDING_BOOTSTRAP', '').lower() == 'true'

# COST OPTIMIZATION: ONLY enable embeddings if Pinecone is configured (prevents expensive local CPU usage)
# NEVER use local CPU-based vector search - it's too expensive!
# If Pinecone is configured, use it (cost-effective). Otherwise, use keyword search (free, no CPU cost).
HAS_PINECONE_CONFIG = PINECONE_AVAILABLE and PINECONE_API_KEY
ENABLE_EMBEDDINGS_EXPLICIT = os.getenv('ENABLE_EMBEDDINGS', '').lower() == 'true'

# CRITICAL: Only enable embeddings if Pinecone is configured (prevents expensive Railway CPU usage)
# Even if ENABLE_EMBEDDINGS=true is set, don't enable if Pinecone isn't configured
if ENABLE_EMBEDDINGS_EXPLICIT and not HAS_PINECONE_CONFIG:
    print("⚠️ WARNING: ENABLE_EMBEDDINGS=true but Pinecone not configured!")
    print("   ⚠️ Disabling embeddings to prevent expensive Railway CPU usage")
    print("   💡 Set PINECONE_API_KEY to enable cost-effective vector search")
    ENABLE_EMBEDDINGS = False
else:
    # Auto-enable embeddings if Pinecone is available (cost-effective cloud-based search)
    ENABLE_EMBEDDINGS = ENABLE_EMBEDDINGS_EXPLICIT or HAS_PINECONE_CONFIG

# Use Pinecone if available and embeddings are enabled
USE_PINECONE = ENABLE_EMBEDDINGS and HAS_PINECONE_CONFIG

# 1. LOAD ENVIRONMENT VARIABLES FROM .env FILE
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
SUPPORT_FORUM_CHANNEL_ID_STR = os.getenv('SUPPORT_FORUM_CHANNEL_ID')
DISCORD_GUILD_ID_STR = os.getenv('DISCORD_GUILD_ID', '1265864190883532872')  # Server ID for slash command sync
DATA_API_URL = os.getenv('DATA_API_URL', 'https://your-vercel-app.vercel.app/api/data')

# Load API keys from environment variable
# All keys (GEMINI_API_KEY, GEMINI_API_KEY_2 through GEMINI_API_KEY_6) are used for all operations
GEMINI_API_KEYS = []

# Load GEMINI_API_KEY (primary key)
env_key = os.getenv('GEMINI_API_KEY')
if env_key:
    GEMINI_API_KEYS.append(env_key)
    print(f"✓ Loaded API key from GEMINI_API_KEY")

# Load additional keys (GEMINI_API_KEY_2 through GEMINI_API_KEY_20 - supports up to 20 keys)
# The system will automatically use all available keys for rotation
for i in range(2, 21):  # Support up to 20 keys total (GEMINI_API_KEY + GEMINI_API_KEY_2 through GEMINI_API_KEY_20)
    additional_key = os.getenv(f'GEMINI_API_KEY_{i}')
    if additional_key and additional_key not in GEMINI_API_KEYS:
        GEMINI_API_KEYS.append(additional_key)
        print(f"✓ Loaded API key from GEMINI_API_KEY_{i}")

# --- Initial Validation ---
if not DISCORD_BOT_TOKEN:
    print("FATAL ERROR: 'DISCORD_BOT_TOKEN' not found in environment.")
    exit()

if not GEMINI_API_KEYS:
    print("FATAL ERROR: No Gemini API keys found in environment.")
    print("   Set GEMINI_API_KEY or GEMINI_API_KEY_2 through GEMINI_API_KEY_20")
    exit()

# Validate keys are not empty
valid_keys = [key for key in GEMINI_API_KEYS if key and len(key.strip()) > 10]
if len(valid_keys) != len(GEMINI_API_KEYS):
    print(f"⚠️ WARNING: Some API keys are invalid (empty or too short)")
    print(f"   Loaded {len(valid_keys)} valid key(s) out of {len(GEMINI_API_KEYS)} total")
    GEMINI_API_KEYS = valid_keys
    if not GEMINI_API_KEYS:
        print("FATAL ERROR: No valid API keys found after validation")
        exit()

print(f"✓ Loaded {len(GEMINI_API_KEYS)} valid API key(s) for all operations (forum posts, /ask, etc.)")

# COST OPTIMIZATION: Show cost-optimized status
# Debug: Log actual values to diagnose
env_enable = os.getenv('ENABLE_EMBEDDINGS', 'NOT_SET')
print(f"🔍 DEBUG: ENABLE_EMBEDDINGS env='{env_enable}', ENABLE_EMBEDDINGS_EXPLICIT={ENABLE_EMBEDDINGS_EXPLICIT}, HAS_PINECONE_CONFIG={HAS_PINECONE_CONFIG}")
print(f"🔍 DEBUG: ENABLE_EMBEDDINGS={ENABLE_EMBEDDINGS}, USE_PINECONE={USE_PINECONE}")

if USE_PINECONE:
    print("🌲 Pinecone vector search enabled - cost-effective cloud-based vector search (Railway CPU saved!)")
    print("   ✅ All vector operations offloaded to Pinecone - minimal Railway costs")
elif ENABLE_EMBEDDINGS and not HAS_PINECONE_CONFIG:
    print("⚠️ WARNING: Embeddings enabled but Pinecone not configured!")
    print("   ⚠️ This should not happen - embeddings disabled to prevent expensive Railway CPU usage")
    print("   💡 Set PINECONE_API_KEY to enable cost-effective vector search")
else:
    print("💡 Using keyword-based search (cost-effective, no CPU-intensive operations)")
    if HAS_PINECONE_CONFIG:
        print(f"   💡 Pinecone is configured (API key present) but ENABLE_EMBEDDINGS={ENABLE_EMBEDDINGS}")
        print(f"   💡 Set ENABLE_EMBEDDINGS=true in Railway to enable vector search")

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

# --- GEMINI API KEY ROTATION SYSTEM ---
class GeminiKeyManager:
    """Manages multiple Gemini API keys with intelligent rotation, load balancing, and rate limit handling"""
    
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_key_index = 0
        
        # Initialize tracking dictionaries
        key_short_names = [key[:10] + '...' for key in api_keys]
        self.key_usage_count = {name: 0 for name in key_short_names}  # Total usage per key
        self.key_success_count = {name: 0 for name in key_short_names}  # Successful calls per key
        self.key_error_count = {name: 0 for name in key_short_names}  # Error count per key
        self.key_rate_limited = {name: False for name in key_short_names}  # Rate limit status
        self.key_rate_limit_time = {name: None for name in key_short_names}  # When rate limit occurred
        self.key_last_used = {name: None for name in key_short_names}  # Last usage timestamp
        
        # Optimize rotation based on number of keys
        # More keys = more frequent rotation to distribute load evenly
        # This ensures each key gets roughly equal usage over time
        if len(api_keys) >= 10:
            self.calls_per_key = 2  # Very frequent rotation with many keys
        elif len(api_keys) >= 6:
            self.calls_per_key = 3  # Frequent rotation with 6+ keys
        elif len(api_keys) >= 3:
            self.calls_per_key = 4  # Moderate rotation with 3-5 keys
        else:
            self.calls_per_key = 5  # Less frequent with 1-2 keys
        
        self.current_key_calls = 0  # Track calls on current key
        self.rate_limit_cooldown = 60  # Seconds to wait before retrying rate-limited key
        
        print(f"✓ Initialized GeminiKeyManager with {len(api_keys)} key(s) for rotation")
        if len(api_keys) > 1:
            print(f"   🔄 Keys will rotate every {self.calls_per_key} calls to distribute load evenly")
            print(f"   📊 Load balancing enabled with health tracking")
    
    def get_current_key(self):
        """Get the current active API key"""
        return self.api_keys[self.current_key_index]
    
    def get_recent_call_count(self, key_index):
        """Get number of API calls in the last minute for a key"""
        key_short = self.api_keys[key_index][:10] + '...'
        if key_short not in gemini_api_calls_by_key:
            return 0
        
        api_calls = gemini_api_calls_by_key[key_short]
        now = datetime.now()
        # Count calls in last 60 seconds
        recent_count = sum(1 for call_time in api_calls 
                          if (now - call_time).total_seconds() <= 60)
        return recent_count
    
    def get_key_health_score(self, key_index):
        """Calculate health score for a key (higher is better)"""
        key_short = self.api_keys[key_index][:10] + '...'
        
        # Skip if rate limited (unless cooldown expired)
        if self.key_rate_limited[key_short]:
            limit_time = self.key_rate_limit_time[key_short]
            if limit_time:
                time_since_limit = (datetime.now() - limit_time).total_seconds()
                if time_since_limit < self.rate_limit_cooldown:
                    return -1000  # Very low score if still rate limited
                else:
                    # Rate limit expired, reset it
                    self.key_rate_limited[key_short] = False
                    self.key_rate_limit_time[key_short] = None
        
        # CRITICAL: Check recent calls in last minute (rate limit is 10/min)
        recent_calls = self.get_recent_call_count(key_index)
        
        # Heavily penalize keys close to or at the limit
        if recent_calls >= 10:
            return -2000  # Way over limit - never use
        elif recent_calls >= 8:
            return -500   # Very close to limit - avoid
        elif recent_calls >= 6:
            return -100  # Getting close - prefer others
        elif recent_calls >= 4:
            return 10    # Moderate usage - low priority
        
        # Calculate health score based on:
        # - Success rate (higher is better)
        # - Recent usage (prefer less recently used keys for load balancing)
        total_calls = self.key_usage_count[key_short]
        errors = self.key_error_count[key_short]
        success_calls = self.key_success_count[key_short]
        
        # If key has errors but no total calls tracked, it means errors occurred but usage wasn't tracked
        # This can happen if errors occur during model creation before the actual API call
        if total_calls == 0 and errors > 0:
            # Key has errors but no tracked usage - heavily penalize
            return -400 - (errors * 20)
        
        # If key has errors, check error rate
        if total_calls > 0 and errors > 0:
            if errors > success_calls:
                # More errors than successes - very bad
                return -500 - (errors * 10)
            error_rate = errors / total_calls
            if error_rate > 0.5:  # More than 50% error rate
                return -300 - (errors * 5)
            elif error_rate > 0.3:  # More than 30% error rate
                return -100 - (errors * 2)
        
        if total_calls == 0 and errors == 0:
            return 200  # New/unused keys with no errors get very high priority
        
        success_rate = self.key_success_count[key_short] / total_calls if total_calls > 0 else 1.0
        error_rate = self.key_error_count[key_short] / total_calls if total_calls > 0 else 0.0
        
        # Base score from success/error rate (heavily penalize errors)
        health_score = (success_rate * 100) - (error_rate * 100)  # Increased penalty for errors
        
        # Big bonus for keys with few recent calls (main factor)
        if recent_calls == 0:
            health_score += 150  # Huge bonus for unused keys
        elif recent_calls == 1:
            health_score += 100
        elif recent_calls == 2:
            health_score += 50
        elif recent_calls == 3:
            health_score += 20
        
        # Prefer keys that haven't been used recently (load balancing)
        if self.key_last_used[key_short]:
            time_since_use = (datetime.now() - self.key_last_used[key_short]).total_seconds()
            if time_since_use > 30:  # Bonus for keys not used in last 30 seconds
                health_score += 30
            elif time_since_use > 10:
                health_score += 10
        
        return health_score
    
    def get_best_key_index(self):
        """Get the index of the healthiest available key with fewest recent calls"""
        best_index = self.current_key_index
        best_score = self.get_key_health_score(self.current_key_index)
        best_recent_calls = self.get_recent_call_count(self.current_key_index)
        
        # Check all keys to find the best one
        for i in range(len(self.api_keys)):
            if i == self.current_key_index:
                continue
            
            # Skip rate-limited keys
            key_short = self.api_keys[i][:10] + '...'
            if self.key_rate_limited[key_short]:
                limit_time = self.key_rate_limit_time[key_short]
                if limit_time:
                    time_since_limit = (datetime.now() - limit_time).total_seconds()
                    if time_since_limit < self.rate_limit_cooldown:
                        continue  # Skip this key, still rate limited
            
            score = self.get_key_health_score(i)
            recent_calls = self.get_recent_call_count(i)
            
            # Prefer keys with fewer recent calls, even if score is slightly lower
            # This prevents hitting rate limits
            if recent_calls < best_recent_calls:
                best_score = score
                best_index = i
                best_recent_calls = recent_calls
            elif recent_calls == best_recent_calls and score > best_score:
                # Same recent call count, prefer better health score
                best_score = score
                best_index = i
        
        return best_index
    
    def rotate_key(self, force_round_robin=False):
        """Intelligently rotate to the best available key, or use round-robin if forced"""
        original_index = self.current_key_index
        original_key_short = self.api_keys[original_index][:10] + '...'
        
        # Check if current key is approaching limit (proactive rotation)
        current_recent_calls = self.get_recent_call_count(original_index)
        if current_recent_calls >= 7 and not force_round_robin:
            print(f"⚠️ Key {original_key_short} has {current_recent_calls}/10 calls in last minute - proactively rotating")
            force_round_robin = False  # Use smart rotation to find best key
        
        if force_round_robin:
            # Round-robin but skip rate-limited keys
            attempts = 0
            while attempts < len(self.api_keys):
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                key_short = self.api_keys[self.current_key_index][:10] + '...'
                recent_calls = self.get_recent_call_count(self.current_key_index)
                
                # Skip if rate limited or too many recent calls
                if not self.key_rate_limited[key_short] and recent_calls < 8:
                    break
                attempts += 1
        else:
            # Smart rotation: find the healthiest key with fewest recent calls
            best_index = self.get_best_key_index()
            self.current_key_index = best_index
        
        # Final check: if selected key is still problematic, find any available key
        key_short = self.api_keys[self.current_key_index][:10] + '...'
        recent_calls = self.get_recent_call_count(self.current_key_index)
        
        if self.key_rate_limited[key_short] or recent_calls >= 8:
            # Emergency: find ANY key that's available
            for i in range(len(self.api_keys)):
                test_key_short = self.api_keys[i][:10] + '...'
                test_recent = self.get_recent_call_count(i)
                if not self.key_rate_limited[test_key_short] and test_recent < 8:
                    self.current_key_index = i
                    key_short = test_key_short
                    recent_calls = test_recent
                    break
        
        # Reset call counter for new key
        self.current_key_calls = 0
        
        if original_index != self.current_key_index:
            print(f"🔄 Rotated from key {original_key_short} ({self.get_recent_call_count(original_index)} recent) to key {key_short} ({recent_calls} recent)")
        
        return self.api_keys[self.current_key_index]
    
    def get_next_key(self):
        """Get next available key - uses smart rotation"""
        return self.rotate_key()
    
    def mark_key_rate_limited(self, key):
        """Mark a key as rate limited"""
        key_short = key[:10] + '...'
        self.key_rate_limited[key_short] = True
        self.key_rate_limit_time[key_short] = datetime.now()
        self.key_error_count[key_short] = self.key_error_count.get(key_short, 0) + 1
        print(f"⚠️ Key {key_short} hit rate limit, switching to next key")
        # Immediately rotate to a different key
        self.rotate_key(force_round_robin=True)
    
    def mark_key_success(self, key):
        """Mark that a key was used successfully - reduces error count to give key a fresh start"""
        key_short = key[:10] + '...'
        self.key_success_count[key_short] = self.key_success_count.get(key_short, 0) + 1
        self.key_last_used[key_short] = datetime.now()
        # Reduce error count on success (errors were likely transient)
        # This gives keys a chance to recover from temporary issues
        current_errors = self.key_error_count.get(key_short, 0)
        if current_errors > 0:
            # Reduce error count by 1 for each success (up to half the error count)
            reduction = min(1, current_errors // 2)
            self.key_error_count[key_short] = max(0, current_errors - reduction)
            if self.key_error_count[key_short] == 0:
                print(f"✅ Key {key_short} error count reset - key is working well now")
    
    def mark_key_error(self, key, is_rate_limit=False):
        """Mark that a key encountered an error - only for confirmed persistent errors"""
        key_short = key[:10] + '...'
        # Only increment error count if we're sure it's a persistent issue
        # Transient errors (rate limits, timeouts) are handled separately
        if not is_rate_limit:  # Rate limits are temporary, don't count as permanent errors
            self.key_error_count[key_short] = self.key_error_count.get(key_short, 0) + 1
            # Also increment usage count so error rate can be calculated accurately
            if self.key_usage_count[key_short] == 0:
                self.key_usage_count[key_short] = 1
        if is_rate_limit:
            self.mark_key_rate_limited(key)
    
    def track_usage(self, key):
        """Track that a key was used and rotate if needed"""
        key_short = key[:10] + '...'
        self.key_usage_count[key_short] = self.key_usage_count.get(key_short, 0) + 1
        self.current_key_calls += 1
        
        # Check recent calls for this key
        key_index = self.api_keys.index(key) if key in self.api_keys else self.current_key_index
        recent_calls = self.get_recent_call_count(key_index)
        
        # Proactive rotation strategies:
        # 1. If key has 6+ calls in last minute, rotate immediately
        # 2. Otherwise, rotate after N calls to distribute load
        if len(self.api_keys) > 1:
            if recent_calls >= 6:
                print(f"🔄 Key {key_short} has {recent_calls} recent calls - rotating proactively")
                self.rotate_key()
            elif self.current_key_calls >= self.calls_per_key:
                # Normal rotation after N calls
                self.rotate_key()
    
    def get_usage_stats(self):
        """Get comprehensive usage statistics for all keys"""
        stats = {}
        for i, key in enumerate(self.api_keys):
            key_short = key[:10] + '...'
            total = self.key_usage_count[key_short]
            success = self.key_success_count[key_short]
            errors = self.key_error_count[key_short]
            rate_limited = self.key_rate_limited[key_short]
            
            stats[key_short] = {
                'total_calls': total,
                'successful_calls': success,
                'errors': errors,
                'success_rate': (success / total * 100) if total > 0 else 0,
                'rate_limited': rate_limited,
                'health_score': self.get_key_health_score(i)
            }
        return stats
    
    def create_model(self, model_name, **kwargs):
        """Create a GenerativeModel with the current key (with proactive rotation)"""
        key = self.get_current_key()
        self.track_usage(key)  # This will rotate if needed
        
        # Configure genai with current key (may have rotated)
        current_key = self.get_current_key()
        genai.configure(api_key=current_key)
        
        # Create and return model
        return genai.GenerativeModel(model_name, **kwargs)
    
    def create_model_with_retry(self, model_name, **kwargs):
        """Create a GenerativeModel with automatic key rotation"""
        # Try each key once, rotating through all keys
        tried_keys = set()
        max_attempts = len(self.api_keys) * 2  # Try each key up to 2 times
        
        for attempt in range(max_attempts):
            current_key = self.get_current_key()
            key_short = current_key[:15] + '...'
            
            # If we've tried this key recently, rotate
            if current_key in tried_keys and attempt > 0:
                self.rotate_key(force_round_robin=True)
                current_key = self.get_current_key()
                key_short = current_key[:15] + '...'
            
            tried_keys.add(current_key)
            
            try:
                # Configure and create model
                genai.configure(api_key=current_key)
                model = genai.GenerativeModel(model_name, **kwargs)
                print(f"✅ Created model {model_name} with key {key_short}")
                return model
            except Exception as e:
                error_str = str(e).lower()
                # If it's a model not found error, try alternative models
                if 'not found' in error_str or 'invalid' in error_str or 'not available' in error_str:
                    # Try alternative models
                    alternatives = [
                        'gemini-2.5-flash',  # Current model
                        'gemini-2.5-pro',
                        'gemini-2.5-flash-lite',
                        'gemini-pro',
                        'gemini-flash-latest',
                        'gemini-pro-latest'
                    ]
                    for alt_model in alternatives:
                        if alt_model != model_name:
                            try:
                                genai.configure(api_key=current_key)
                                model = genai.GenerativeModel(alt_model, **kwargs)
                                print(f"✅ Created alternative model {alt_model} with key {key_short}")
                                return model
                            except:
                                continue
                # Rotate to next key and try again
                if attempt < max_attempts - 1:
                    self.rotate_key(force_round_robin=True)
                    import time
                    time.sleep(0.2)
                    continue
                else:
                    # Last attempt failed
                    raise Exception(f"Failed to create model: {str(e)[:200]}")
        
        raise Exception("All API keys exhausted")

# Initialize key manager (all keys used for all operations)
gemini_key_manager = GeminiKeyManager(GEMINI_API_KEYS)

# Test API keys on startup to verify they work (non-blocking - bot will start even if test fails)
print(f"\n🔍 Testing API keys on startup (quick validation)...")
test_passed = False
working_keys = []
for i, test_key in enumerate(GEMINI_API_KEYS, 1):
    try:
        key_short = test_key[:15] + '...'
        genai.configure(api_key=test_key)
        # Try multiple model names to find one that works (Gemini 1.5 was shut down Sep 2025, use 2.5)
        test_models = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.5-flash-lite', 'gemini-pro']
        test_model = None
        for model_name in test_models:
            try:
                test_model = genai.GenerativeModel(model_name)
                break  # Found a working model
            except:
                continue
        
        if test_model is None:
            raise Exception("No working model found")
        
        # Simple test - just try to generate content (no timeout option, let it use default)
        test_response = test_model.generate_content("Hi")
        if test_response and hasattr(test_response, 'text') and test_response.text:
            print(f"   ✅ Key {i} ({key_short}) works!")
            working_keys.append(i)
            test_passed = True
        else:
            print(f"   ⚠️ Key {i} ({key_short}) responded but no text")
    except Exception as test_error:
        error_str = str(test_error).lower()
        error_msg = str(test_error)[:150]
        if 'api key' in error_str or 'auth' in error_str or '403' in error_str or 'leaked' in error_str or 'permission denied' in error_str:
            print(f"   ❌ Key {i} INVALID/LEAKED: {error_msg}")
        elif 'quota' in error_str or 'rate limit' in error_str or '429' in error_str:
            print(f"   ⚠️ Key {i} rate limited (temporary): {error_msg}")
        elif 'timeout' in error_str:
            print(f"   ⚠️ Key {i} timeout (may still work): {error_msg}")
        else:
            print(f"   ⚠️ Key {i} test failed: {error_msg}")

if test_passed:
    print(f"✓ Startup test: {len(working_keys)}/{len(GEMINI_API_KEYS)} key(s) working ({', '.join(map(str, working_keys))})\n")
else:
    print(f"\n⚠️ WARNING: Startup test failed for all keys!")
    print(f"   The bot will still try to use them (test may have been too strict)")
    print(f"   Check Railway logs when making actual API calls to see real errors")
    print(f"   Verify keys at: https://aistudio.google.com/app/apikey\n")

# Configure with first key (will be reconfigured per-request)
if gemini_key_manager.api_keys:
    try:
        genai.configure(api_key=gemini_key_manager.get_current_key())
        print(f"✓ Initialized genai with first key")
    except Exception as e:
        print(f"⚠️ Failed to configure genai with first key: {e}")
        print(f"   Will configure per-request instead")

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
FRIEND_SERVER_ID = 1221433387772805260  # Friend's server - ONLY /ask command allowed, everyone can use it

# --- IMPORTANT FOR FUTURE DEVELOPERS ---
# When adding new commands, you MUST add this check at the start of your command handler:
#   if is_friend_server(interaction):
#       await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
#       return
# This ensures the friend's server ONLY gets /ask, even when new features are added.

# --- DATA STORAGE (Synced from Dashboard) ---
RAG_DATABASE = []
AUTO_RESPONSES = []
SYSTEM_PROMPT_TEXT = ""  # Fetched from API, fallback to default if not available
LEADERBOARD_DATA = {
    'month': '',  # Format: "2025-12" for December 2025
    'scores': {}  # {user_id: {'username': 'Name', 'solved_count': 5, 'avatar_url': 'https://...'}}
}

# --- VECTOR EMBEDDINGS FOR RAG ---
# Initialize embedding model (lazy load on first use)
_embedding_model = None
_pinecone_index = None
_rag_embeddings = {}  # {entry_id: embedding_vector} - Fallback for non-Pinecone mode
_rag_embeddings_version = 0  # Increment when RAG database changes

def get_embedding_model():
    """Lazy load the embedding model (non-blocking, will fallback if fails)"""
    global _embedding_model
    
    # CPU OPTIMIZATION: Skip embeddings if disabled
    if not ENABLE_EMBEDDINGS:
        return None
    
    if _embedding_model is None:
        print("🔧 Loading embedding model for vector search...")
        try:
            # Use a lightweight, fast model for embeddings
            # Model should be pre-cached in Docker image, so this should be fast
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embedding model loaded")
        except Exception as e:
            print(f"⚠️ Failed to load embedding model: {e}")
            print("   Bot will continue with keyword-based search")
            print("   Embeddings will be available after model loads successfully")
            return None
    return _embedding_model

def init_pinecone():
    """Initialize Pinecone connection and index"""
    global _pinecone_index
    
    if not USE_PINECONE:
        return None
    
    if _pinecone_index is not None:
        return _pinecone_index
    
    try:
        print("🌲 Initializing Pinecone connection...")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists, create if not
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        
        if PINECONE_INDEX_NAME not in existing_indexes:
            print(f"🌲 Creating Pinecone index '{PINECONE_INDEX_NAME}'...")
            # COST OPTIMIZATION: Skip loading embedding model if bootstrap is disabled
            # Use default dimension (384 for all-MiniLM-L6-v2) to avoid blocking startup
            if SKIP_EMBEDDING_BOOTSTRAP:
                dimension = 384  # Default for all-MiniLM-L6-v2
                print(f"   Using default dimension {dimension} (SKIP_EMBEDDING_BOOTSTRAP=true)")
            else:
                # Get embedding dimension from model
                model = get_embedding_model()
                if model is None:
                    # Default dimension for all-MiniLM-L6-v2
                    dimension = 384
                else:
                    # Test encode to get dimension
                    test_embedding = model.encode("test", convert_to_numpy=True)
                    dimension = len(test_embedding)
            
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=PINECONE_ENVIRONMENT
                )
            )
            print(f"✅ Created Pinecone index '{PINECONE_INDEX_NAME}' with dimension {dimension}")
        else:
            print(f"✅ Using existing Pinecone index '{PINECONE_INDEX_NAME}'")
        
        _pinecone_index = pc.Index(PINECONE_INDEX_NAME)
        print("✅ Pinecone initialized successfully")
        return _pinecone_index
        
    except Exception as e:
        print(f"⚠️ Failed to initialize Pinecone: {e}")
        print("   Falling back to local vector storage")
        _pinecone_index = None
        return None

def compute_rag_embeddings():
    """Compute embeddings for all RAG entries and store ONLY in Pinecone (cost optimization)
    
    Railway cost optimization: All vector storage and search happens in Pinecone.
    No local storage unless Pinecone is completely unavailable.
    """
    global _rag_embeddings, _rag_embeddings_version
    
    if SKIP_EMBEDDING_BOOTSTRAP:
        print("⚠️ SKIP_EMBEDDING_BOOTSTRAP=true - skipping embedding computation on this worker. Seed Pinecone externally.")
        return
    
    model = get_embedding_model()
    if model is None:
        return
    
    print(f"🔄 Computing embeddings for {len(RAG_DATABASE)} RAG entries...")
    
    # COST OPTIMIZATION: Always try Pinecone first - it's much cheaper than Railway CPU
    index = init_pinecone() if USE_PINECONE else None
    
    if index:
        # Use Pinecone for storage (cost-effective - offloads from Railway)
        print("🌲 Storing embeddings in Pinecone (cost-optimized - Railway CPU saved)...")
        vectors_to_upsert = []
        
        for entry in RAG_DATABASE:
            entry_id = entry.get('id', '')
            if not entry_id:
                continue
            
            # Combine title, content, and keywords for embedding
            title = entry.get('title', '')
            content = entry.get('content', '')
            keywords = ' '.join(entry.get('keywords', []))
            
            # Create a combined text for embedding
            combined_text = f"{title}\n{keywords}\n{content[:500]}"  # Limit content to avoid huge embeddings
            
            try:
                # Compute embedding (minimal CPU - just encoding)
                embedding = model.encode(combined_text, convert_to_numpy=True)
                embedding_list = embedding.tolist()
                
                # Prepare metadata (store full entry data in Pinecone)
                metadata = {
                    'title': title[:1000],  # Pinecone metadata limit
                    'content': content[:1000],
                    'keywords': ' '.join(entry.get('keywords', []))[:500],
                    'entry_id': entry_id  # Store ID for reference
                }
                
                vectors_to_upsert.append({
                    'id': entry_id,
                    'values': embedding_list,
                    'metadata': metadata
                })
            except Exception as e:
                print(f"⚠️ Failed to compute embedding for entry {entry_id}: {e}")
                continue
        
        # Batch upsert to Pinecone (upsert in chunks of 100 for efficiency)
        try:
            chunk_size = 100
            for i in range(0, len(vectors_to_upsert), chunk_size):
                chunk = vectors_to_upsert[i:i + chunk_size]
                index.upsert(vectors=chunk)
            print(f"✅ Upserted {len(vectors_to_upsert)} embeddings to Pinecone (Railway CPU saved!)")
            
            # COST OPTIMIZATION: Clear local storage when using Pinecone to save Railway memory
            _rag_embeddings = {}
            print("💡 Cleared local embeddings cache (using Pinecone only - saves Railway memory)")
        except Exception as e:
            print(f"⚠️ Failed to upsert to Pinecone: {e}")
            print("   Falling back to local storage (temporary - fix Pinecone connection)")
            index = None
    
    # COST OPTIMIZATION: Don't use local CPU storage - it's expensive!
    # If Pinecone is unavailable, just skip embeddings and use keyword search instead
    if not index:
        print("⚠️ Pinecone unavailable - skipping embeddings to save Railway CPU costs")
        print("   Bot will use keyword-based search (free, no CPU cost)")
        print("   💡 Set PINECONE_API_KEY to enable cost-effective vector search")
        # Clear any existing embeddings to save memory
        _rag_embeddings = {}
        # Don't compute embeddings locally - keyword search is free and doesn't use CPU
        print("   ✅ Skipped local embedding computation (saves Railway CPU costs)")
    
    _rag_embeddings_version += 1
    print(f"✅ Embedding computation complete (version {_rag_embeddings_version})")

async def compute_embeddings_background():
    """Background task to compute embeddings without blocking bot startup"""
    try:
        # Small delay to let bot finish startup
        await asyncio.sleep(2)
        compute_rag_embeddings()
    except Exception as e:
        print(f"⚠️ Error in background embedding computation: {e}")
        print("   Bot will continue with keyword-based search until embeddings are ready")

# Cooldown tracking for /ask command on friends server (1 minute cooldown)
ask_cooldowns = {}  # {user_id: last_used_timestamp}

# Track support notification messages so we can delete them when classification is done
support_notification_messages = {}  # {thread_id: message_id}

# --- BOT SETTINGS (Stored in Vercel KV API - NO local files) ---
BOT_SETTINGS = {
    'support_forum_channel_id': SUPPORT_FORUM_CHANNEL_ID,
    'ai_temperature': 1.0,  # Gemini temperature (0.0-2.0)
    'ai_max_tokens': 2048,  # Max tokens for AI responses
    'ignored_post_ids': [],  # Post IDs to ignore (e.g., rules post)
    'post_inactivity_hours': 12,  # Hours before escalating old posts to High Priority
    'high_priority_check_interval_hours': 1.0,  # Hours between high priority checks (0.25 = 15 min, 1.0 = 1 hour)
    'solved_post_retention_days': 30,  # Days to keep solved/closed posts before deletion
    'unsolved_tag_id': None,  # Discord tag ID for "Unsolved" posts
    'resolved_tag_id': None,  # Discord tag ID for "Resolved" posts
    'issue_type_tag_ids': {},  # Map issue types to Discord tag IDs (e.g., {'Bug/Error': '123456789'})
    'support_notification_channel_id': '1436918674069000212',  # Channel ID for high priority notifications (string to prevent JS precision loss)
    'support_role_id': None,  # Support role ID to ping (optional)
    'last_updated': datetime.now().isoformat()
}

# --- GEMINI API RATE LIMITING (tracked per key now) ---
from collections import deque

# Track API calls per key (for monitoring)
gemini_api_calls_by_key = {key[:10] + '...': deque(maxlen=100) for key in GEMINI_API_KEYS}

# Cache for AI responses (reduces duplicate API calls)
ai_response_cache = {}  # {query_hash: (response, timestamp)}
AI_CACHE_TTL = 3600  # Cache responses for 1 hour

# Hash for data change detection (skip unnecessary syncs)
last_data_hash = None

async def check_rate_limit(key_manager=None, api_calls_dict=None):
    """Check if we can make a Gemini API call without hitting rate limit
    Proactively rotates to best key before hitting limits
    
    Args:
        key_manager: The GeminiKeyManager to use (defaults to gemini_key_manager for backward compatibility)
        api_calls_dict: Dictionary tracking API calls per key (defaults to gemini_api_calls_by_key)
    """
    if key_manager is None:
        key_manager = gemini_key_manager
    if api_calls_dict is None:
        api_calls_dict = gemini_api_calls_by_key
    
    current_key = key_manager.get_current_key()
    key_short = current_key[:10] + '...'
    
    if key_short not in api_calls_dict:
        api_calls_dict[key_short] = deque(maxlen=100)
    
    api_calls = api_calls_dict[key_short]
    now = datetime.now()
    
    # Remove calls older than 1 minute
    while api_calls and (now - api_calls[0]).total_seconds() > 60:
        api_calls.popleft()
    
    recent_count = len(api_calls)
    
    # Proactive rotation: if we're at 7+ calls, rotate to a better key
    if recent_count >= 7:
        print(f"⚠️ Key {key_short} has {recent_count}/10 calls - proactively rotating to better key")
        key_manager.rotate_key()
        new_key = key_manager.get_current_key()
        new_key_short = new_key[:10] + '...'
        
        # Check the new key
        if new_key_short not in api_calls_dict:
            api_calls_dict[new_key_short] = deque(maxlen=100)
        new_api_calls = api_calls_dict[new_key_short]
        
        # Clean old calls
        while new_api_calls and (now - new_api_calls[0]).total_seconds() > 60:
            new_api_calls.popleft()
        
        new_recent_count = len(new_api_calls)
        
        if new_recent_count >= 10:
            # All keys are at limit, must wait
            if new_api_calls:
                oldest_call = new_api_calls[0]
                wait_time = 60 - (now - oldest_call).total_seconds()
                print(f"⚠️ ALL KEYS AT LIMIT: {new_recent_count}/10 calls. Waiting {wait_time:.1f}s...")
                return False
            return True
        else:
            print(f"✓ Rotated to key {new_key_short} with {new_recent_count}/10 calls")
            return True
    
    # Check if we're at the hard limit (10 per minute per key)
    if recent_count >= 10:
        # Try rotating to a better key
        key_manager.rotate_key()
        new_key = key_manager.get_current_key()
        new_key_short = new_key[:10] + '...'
        
        if new_key_short != key_short:
            print(f"⚠️ Key {key_short} at limit ({recent_count}/10), rotated to {new_key_short}")
            return True  # Can proceed with new key
        else:
            # No better key available, must wait
            oldest_call = api_calls[0]
            wait_time = 60 - (now - oldest_call).total_seconds()
            print(f"⚠️ RATE LIMIT: {recent_count}/10 API calls in last minute. Waiting {wait_time:.1f}s...")
            return False
    
    return True

def track_api_call(key_manager=None, api_calls_dict=None):
    """Track that we made a Gemini API call
    
    Args:
        key_manager: The GeminiKeyManager to use (defaults to gemini_key_manager for backward compatibility)
        api_calls_dict: Dictionary tracking API calls per key (defaults to gemini_api_calls_by_key)
    """
    if key_manager is None:
        key_manager = gemini_key_manager
    if api_calls_dict is None:
        api_calls_dict = gemini_api_calls_by_key
    
    current_key = key_manager.get_current_key()
    key_short = current_key[:10] + '...'
    
    if key_short not in api_calls_dict:
        api_calls_dict[key_short] = deque(maxlen=100)
    
    api_calls_dict[key_short].append(datetime.now())
    usage_stats = key_manager.get_usage_stats()
    total_keys = len(key_manager.api_keys)
    current_index = key_manager.current_key_index
    print(f"📊 Using key {key_short} ({current_index + 1}/{total_keys}) | Calls on this key: {key_manager.current_key_calls}/{key_manager.calls_per_key} | Total usage: {usage_stats}")

# --- SATISFACTION ANALYSIS TIMERS ---
# Track pending satisfaction analysis tasks per thread
satisfaction_timers = {}  # {thread_id: asyncio.Task} - tracks active satisfaction analysis timers
# Track processed threads to avoid duplicate processing
# Use dict with timestamps to enable cleanup of old entries
processed_threads = {}  # {thread_id: timestamp}
# Track threads currently being processed (lock to prevent race conditions)
processing_threads = set()  # {thread_id}
# Track threads escalated to human support (bot stops responding)
escalated_threads = set()  # {thread_id}
# Track what type of response was given per thread (for satisfaction flow)
thread_response_type = {}  # {thread_id: 'auto' | 'ai' | None}
# Store images per thread for escalation (images are PIL Image objects)
thread_images = {}  # {thread_id: [image_parts]}
# Track threads manually closed with no_review (don't create RAG entries)
no_review_threads = set()  # {thread_id}
# Track how many times "not solved" has been clicked per thread (to prevent duplicate "Let Me Try Again" responses)
not_solved_retry_count = {}  # {thread_id: count}

# REMOVED: No local storage - all data in Vercel KV API only

# --- SIMPLE, LOW-COST SATISFACTION ANALYZER (prevents NameError and avoids heavy API calls) ---
async def analyze_user_satisfaction(user_messages):
    """Lightweight heuristic satisfaction analysis to keep flow running without external calls."""
    if not user_messages:
        return {'satisfied': False, 'wants_human': False, 'confidence': 0}
    
    text = " ".join(m.lower() for m in user_messages if m)
    satisfied_keywords = ["thanks", "thank you", "fixed", "resolved", "works now", "great", "appreciate"]
    unhappy_keywords = ["not working", "still", "doesn't", "broken", "issue", "problem", "help", "wtf", "no", "not fixed"]
    wants_human_keywords = ["human", "agent", "support", "escalate", "talk to", "someone"]
    
    score = 0
    if any(k in text for k in satisfied_keywords):
        score += 2
    if any(k in text for k in unhappy_keywords):
        score -= 2
    wants_human = any(k in text for k in wants_human_keywords) or score < 0
    
    satisfied = score > 0
    confidence = min(100, max(10, 60 + (score * 10))) if score != 0 else 40
    return {
        'satisfied': satisfied,
        'wants_human': wants_human,
        'confidence': confidence
    }

# --- PAGINATED HIGH PRIORITY POSTS VIEW ---
class HighPriorityPostsView(discord.ui.View):
    """Paginated view for browsing high priority posts"""
    
    def __init__(self, posts, page_size=10):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.posts = posts
        self.page_size = page_size
        self.current_page = 0
        # Calculate total pages, ensure at least 1 page even if empty
        self.total_pages = max(1, (len(posts) + page_size - 1) // page_size) if posts else 1
        
        # Note: Button states will be set after super().__init__() creates them
        # We'll disable them in a post_init if needed
    
    def get_page_posts(self):
        """Get posts for current page"""
        start = self.current_page * self.page_size
        end = start + self.page_size
        return self.posts[start:end]
    
    def create_embed(self, guild_id):
        """Create embed for current page"""
        page_posts = self.get_page_posts()
        
        embed = discord.Embed(
            title=f"🚨 High Priority Posts (Page {self.current_page + 1}/{self.total_pages})",
            description=f"Showing {len(self.posts)} total high priority post(s)",
            color=0xE74C3C  # Red for high priority
        )
        
        # Build compact list of posts using markdown format
        # Split into multiple fields if needed (Discord limit: 1024 chars per field value)
        post_entries = []
        for i, post in enumerate(page_posts, start=self.current_page * self.page_size + 1):
            thread_id = post.get('postId')
            post_title = post.get('postTitle', 'Unknown Post')
            op_username = post.get('user', {}).get('username', 'Unknown')
            
            # Truncate title if too long to prevent field overflow
            max_title_length = 80
            if len(post_title) > max_title_length:
                post_title = post_title[:max_title_length - 3] + "..."
            
            # Get last activity time
            updated_at = post.get('updatedAt') or post.get('createdAt', '')
            activity_info = ""
            if updated_at:
                try:
                    # Try ISO format first (most common)
                    if 'T' in updated_at:
                        updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    else:
                        # Fallback to strptime
                        updated_dt = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                    
                    now = datetime.now(updated_dt.tzinfo) if hasattr(updated_dt, 'tzinfo') and updated_dt.tzinfo else datetime.now()
                    # Remove timezone info for comparison if present
                    if hasattr(updated_dt, 'replace') and updated_dt.tzinfo:
                        updated_dt = updated_dt.replace(tzinfo=None)
                    if hasattr(now, 'replace') and now.tzinfo:
                        now = now.replace(tzinfo=None)
                    
                    time_diff = now - updated_dt
                    if time_diff.days > 0:
                        activity_info = f" ({time_diff.days}d ago)"
                    elif time_diff.seconds // 3600 > 0:
                        activity_info = f" ({time_diff.seconds // 3600}h ago)"
                    elif time_diff.seconds // 60 > 0:
                        activity_info = f" ({time_diff.seconds // 60}m ago)"
                    else:
                        activity_info = " (just now)"
                except:
                    pass
            
            post_url = f"https://discord.com/channels/{guild_id}/{thread_id}"
            # Compact format: [Post title - OP Username](link)
            post_entries.append(f"{i}. [{post_title} - {op_username}]({post_url}){activity_info}")
        
        # Split posts across multiple fields to stay under 1024 char limit per field
        max_field_length = 1000  # Keep some buffer under 1024 limit
        current_field_content = []
        current_length = 0
        
        for entry in post_entries:
            entry_length = len(entry) + 1  # +1 for newline
            
            # If adding this entry would exceed limit, create a field and start new one
            if current_length + entry_length > max_field_length and current_field_content:
                # Only first field gets a name, continuation fields are empty (cleaner look)
                embed.add_field(
                    name="High Priority Posts",
                    value="\n".join(current_field_content),
                    inline=False
                )
                current_field_content = []
                current_length = 0
            
            current_field_content.append(entry)
            current_length += entry_length
        
        # Add the last field if there's content
        if current_field_content:
            # Only show field name if this is the first/only field, otherwise leave empty
            field_name = "High Priority Posts" if len(embed.fields) == 0 else ""
            embed.add_field(
                name=field_name,
                value="\n".join(current_field_content) or "No posts on this page",
                inline=False
            )
        
        embed.set_footer(text=f"Use the buttons below to navigate • Total: {len(self.posts)} posts")
        return embed
    
    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.primary, disabled=True, row=0)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            # Update button states directly
            self.prev_button.disabled = self.current_page == 0
            self.next_button.disabled = self.current_page >= self.total_pages - 1
            # Update embed
            embed = self.create_embed(interaction.guild_id)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary, row=0)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            # Update button states directly
            self.prev_button.disabled = self.current_page == 0
            self.next_button.disabled = self.current_page >= self.total_pages - 1
            # Update embed
            embed = self.create_embed(interaction.guild_id)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, custom_id="hp_refresh")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refresh the list"""
        await interaction.response.defer()
        # Reload posts from API (this would need to be implemented)
        # For now, just acknowledge
        await interaction.followup.send("⚠️ Refresh not yet implemented. Use the navigation buttons.", ephemeral=True)

# --- SIMPLE SOLVED BUTTON VIEW ---
class SolvedButton(discord.ui.View):
    """Interactive buttons for user feedback on bot responses"""
    
    def __init__(self, thread_id, conversation, response_type='ai', image_parts=None):
        super().__init__(timeout=None)  # Buttons never expire
        self.thread_id = thread_id
        self.conversation = conversation
        self.response_type = response_type
        self.image_parts = image_parts  # Store images for escalation
    
    @discord.ui.button(label="Yes, this solved my issue", style=discord.ButtonStyle.green, emoji="✅")
    async def solved_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle when user confirms issue is solved"""
        try:
            await interaction.response.defer()
        except discord.errors.InteractionResponded:
            # Already responded, ignore
            pass
        except Exception as e:
            print(f"⚠ Error deferring interaction: {e}")
            try:
                await interaction.response.send_message("Processing...", ephemeral=True)
            except:
                pass
        
        thread = interaction.channel
        print(f"✅ User clicked SOLVED button for thread {self.thread_id}")
        
        # Disable all buttons
        try:
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
        except Exception as edit_error:
            print(f"⚠ Could not disable buttons: {edit_error}")
            # Continue anyway - buttons might already be disabled
        
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
        try:
            await interaction.response.defer()
        except discord.errors.InteractionResponded:
            # Already responded, ignore
            pass
        except Exception as e:
            print(f"⚠ Error deferring interaction: {e}")
            try:
                await interaction.response.send_message("Processing...", ephemeral=True)
            except:
                pass
        
        thread = interaction.channel
        print(f"❌ User clicked NOT SOLVED button for thread {self.thread_id}")
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        # Track retry attempts - if we've already tried once, escalate to human
        current_retry_count = not_solved_retry_count.get(self.thread_id, 0)
        not_solved_retry_count[self.thread_id] = current_retry_count + 1
        
        # If this is the second time clicking "not solved", escalate to human instead of trying again
        if current_retry_count >= 1:
            print(f"🔄 User clicked NOT SOLVED for the second time - escalating to human support")
            user_who_clicked = interaction.user if hasattr(interaction, 'user') else None
            
            # Send followup to complete the deferred interaction (fixes "thinking" issue)
            try:
                await interaction.followup.send("🔄 Escalating to human support...", ephemeral=True)
            except Exception as followup_error:
                print(f"⚠ Could not send followup message: {followup_error}")
            
            await self._escalate_to_human(thread, user_who_clicked)
            return
        
        # First time clicking "not solved" - try AI response
        print(f"🔄 User clicked NOT SOLVED - generating AI response (attempt {current_retry_count + 1})...")
        
        try:
            # Get user's question from conversation
            user_messages = [msg.get('content', '') for msg in self.conversation if msg.get('author') == 'User']
            user_question = ' '.join(user_messages[:2]) if user_messages else "Help with this issue"
            
            if not user_question or user_question.strip() == "":
                # Fallback: try to get thread name or last message
                try:
                    if hasattr(thread, 'name') and thread.name:
                        user_question = thread.name
                    else:
                        user_question = "Help with this issue"
                except:
                    user_question = "Help with this issue"
            
            print(f"📝 User question for AI: '{user_question[:100]}...'")
            
            # DISABLED: Image processing - skip images to avoid AI connection issues
            escalation_images = None
            print(f"🖼️ Skipping image processing (disabled)")
            
            # ALWAYS try to find RAG entries and use them
            relevant_docs = find_relevant_rag_entries(user_question)
            print(f"📚 Found {len(relevant_docs)} relevant knowledge base entries")
            
            # Generate AI response - ALWAYS use knowledge base if available
            ai_response = await generate_ai_response(user_question, relevant_docs[:2] if relevant_docs else [], escalation_images)
            
            # Check if AI actually returned a response or just an error message
            if not ai_response or "having trouble connecting" in ai_response.lower() or "human support agent" in ai_response.lower():
                print(f"❌ AI failed to generate response, escalating to human")
                user_who_clicked = interaction.user if hasattr(interaction, 'user') else None
                await self._escalate_to_human(thread, user_who_clicked)
                return
            
            # Send AI response with buttons
            # Truncate description if too long (Discord limit is 4096 characters)
            max_description_length = 4096
            truncated_response = ai_response
            if len(ai_response) > max_description_length:
                truncated_response = ai_response[:max_description_length-3] + "..."
            
            ai_embed = discord.Embed(
                title="💡 Let Me Try Again",
                description=truncated_response,
                color=0x5865F2
            )
            ai_embed.add_field(
                name="💬 Better?",
                value="Let me know if this helps!",
                inline=False
            )
            
            # Add knowledge base references if we used them
            if relevant_docs:
                doc_titles = [doc.get('title', 'Unknown') for doc in relevant_docs[:2]]
                ai_embed.add_field(
                    name="📚 Knowledge Base References",
                    value="\n".join([f"• {title}" for title in doc_titles]),
                    inline=False
                )
                ai_embed.set_footer(text=f"Revolution Macro AI • Based on {len(relevant_docs)} knowledge base entries")
            else:
                ai_embed.set_footer(text="Revolution Macro AI")
            
            # Add solved button
            solved_view = SolvedButton(self.thread_id)
            await thread.send(embed=ai_embed, view=solved_view)
            thread_response_type[self.thread_id] = 'ai'
            
            # Classify issue and apply tag (same as first response)
            issue_type = classify_issue(user_question)
            await apply_issue_type_tag(thread, issue_type)
            
            # Update forum post with classification
            if 'your-vercel-app' not in DATA_API_URL:
                try:
                    forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
                    async with aiohttp.ClientSession() as session:
                        async with session.get(forum_api_url, timeout=aiohttp.ClientTimeout(total=10)) as get_resp:
                            if get_resp.status == 200:
                                all_posts = await get_resp.json()
                                current_post = None
                                for p in all_posts:
                                    if p.get('postId') == str(self.thread_id) or p.get('id') == f'POST-{self.thread_id}':
                                        current_post = p
                                        break
                                
                                if current_post:
                                    current_post['issueType'] = issue_type
                                    update_payload = {'action': 'update', 'post': current_post}
                                    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                                    async with session.post(forum_api_url, json=update_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as post_response:
                                        if post_response.status == 200:
                                            print(f"✓ Classified issue as: {issue_type} (second attempt)")
                except Exception as e:
                    print(f"⚠ Could not update issue classification: {e}")
            
            await update_forum_post_status(self.thread_id, 'AI Response')
            
            # Send followup to complete the deferred interaction (fixes "thinking" issue)
            try:
                await interaction.followup.send("✅ Generated a new response below!", ephemeral=True)
            except Exception as followup_error:
                print(f"⚠ Could not send followup message: {followup_error}")
            
            print(f"✅ Sent AI follow-up response to thread {self.thread_id} (with classification and tagging)")
            
        except Exception as ai_error:
            print(f"❌ Error generating AI follow-up: {ai_error}")
            import traceback
            traceback.print_exc()
            # Escalate to human on error
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
        notification_msg = await thread.send(embed=escalate_embed)
        # Track this message so we can delete it when classification is done
        support_notification_messages[self.thread_id] = notification_msg.id
        
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
                        headers = {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'Accept-Encoding': 'gzip, deflate'
                        }
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
    """Save bot settings to API (persists across deployments)
    
    This saves ALL bot settings including:
    - Tag IDs (issue_type_tag_ids, user_issue_tag_id, bug_tag_id, crash_tag_id, rdp_tag_id)
    - Forum channel IDs
    - AI settings (temperature, max_tokens)
    - Notification settings
    - All other BOT_SETTINGS
    
    Settings are persisted in Vercel KV/Redis and survive bot restarts.
    """
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
                
                # CRITICAL FIX: Merge current API settings with our settings
                # This prevents overwriting settings that were changed elsewhere
                existing_settings = current_data.get('botSettings', {})
                
                # Start with existing API settings
                full_bot_settings = existing_settings.copy()
                
                # Update with current BOT_SETTINGS (our changes take priority)
                full_bot_settings.update(BOT_SETTINGS)
                
                # Include system prompt if we have it
                if SYSTEM_PROMPT_TEXT:
                    full_bot_settings['systemPrompt'] = SYSTEM_PROMPT_TEXT
                    print(f"🔍 DEBUG: Including custom system prompt ({len(SYSTEM_PROMPT_TEXT)} chars)")
                
                current_data['botSettings'] = full_bot_settings
                
                # Debug: Show what we're saving
                print(f"🔍 DEBUG: Saving botSettings to API")
                print(f"🔍 DEBUG: support_notification_channel_id = {BOT_SETTINGS.get('support_notification_channel_id')}")
                print(f"🔍 DEBUG: systemPrompt included = {bool(full_bot_settings.get('systemPrompt'))}")
                
                # Save back to API with compression
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate'
                }
                async with session.post(DATA_API_URL, json=current_data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as save_response:
                    if save_response.status == 200:
                        print(f"✅ Saved bot settings to API (persisted to Vercel KV/Redis)")
                        print(f"   Saved settings: {list(BOT_SETTINGS.keys())}")
                        return True
                    else:
                        error_text = await save_response.text()
                        print(f"⚠ Failed to save bot settings: Status {save_response.status}")
                        print(f"   Error: {error_text[:200]}")
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
    """Fetch RAG entries, auto-responses, system prompt, and leaderboard from the dashboard API"""
    global RAG_DATABASE, AUTO_RESPONSES, SYSTEM_PROMPT_TEXT, LEADERBOARD_DATA, last_data_hash
    
    # Skip API call if URL is still the placeholder
    if 'your-vercel-app' in DATA_API_URL:
        print("ℹ Skipping API sync - Vercel URL not configured. Bot will use local data.")
        load_local_fallback_data()
        return False
    
    print(f"🔗 Attempting to fetch data from: {DATA_API_URL}")
    
    try:
        # Use compression headers to reduce transfer size
        headers = {'Accept-Encoding': 'gzip, deflate', 'Accept': 'application/json'}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DATA_API_URL}", headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    new_rag = data.get('ragEntries', [])
                    new_auto = data.get('autoResponses', [])
                    new_settings = data.get('botSettings', {})
                    new_leaderboard = data.get('leaderboard', {'month': '', 'scores': {}})
                    
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
                    
                    # Check if data actually changed using hash
                    import hashlib
                    data_to_hash = json.dumps({
                        'rag': [r.get('id') for r in new_rag],
                        'auto': [a.get('id') for a in new_auto],
                        'leaderboard': LEADERBOARD_DATA.get('month', '')
                    }, sort_keys=True)
                    current_hash = hashlib.md5(data_to_hash.encode()).hexdigest()
                    
                    if last_data_hash == current_hash:
                        print(f"✓ Data unchanged (hash match) - skipping update to save resources")
                        return True
                    
                    # Update data
                    RAG_DATABASE = new_rag
                    AUTO_RESPONSES = new_auto
                    LEADERBOARD_DATA = new_leaderboard
                    last_data_hash = current_hash
                    
                    # COST OPTIMIZATION: Only recompute embeddings if RAG data changed
                    # All embeddings stored in Pinecone (saves Railway CPU/memory costs)
                    if ENABLE_EMBEDDINGS:
                        if SKIP_EMBEDDING_BOOTSTRAP:
                            print("⚠️ Embeddings enabled but SKIP_EMBEDDING_BOOTSTRAP=true. Not computing embeddings on this worker. Seed Pinecone externally.")
                        elif rag_changed:
                            print("🔄 RAG database changed - uploading embeddings to Pinecone...")
                            compute_rag_embeddings()  # Stores in Pinecone, not Railway memory
                        elif len(RAG_DATABASE) > 0:
                            # Check if Pinecone has embeddings, if not compute them
                            if USE_PINECONE:
                                index = init_pinecone()
                                if index:
                                    try:
                                        stats = index.describe_index_stats()
                                        if stats.total_vector_count == 0:
                                            print("🔄 Pinecone index empty - uploading initial embeddings...")
                                            compute_rag_embeddings()
                                        else:
                                            print(f"✅ Pinecone has {stats.total_vector_count} vectors - no recompute needed")
                                    except:
                                        print("🔄 Computing initial embeddings for Pinecone...")
                                        compute_rag_embeddings()
                            else:
                                # COST OPTIMIZATION: Don't compute embeddings locally - use keyword search instead
                                print("⚠️ Pinecone not configured - skipping embeddings to save Railway CPU costs")
                                print("   Bot will use keyword-based search (free, no CPU cost)")
                                print("   💡 Set PINECONE_API_KEY to enable cost-effective vector search")
                    else:
                        print("ℹ Embeddings disabled - using keyword search only (set ENABLE_EMBEDDINGS=true for Pinecone)")
                    
                    # Update system prompt if available
                    if new_settings and 'systemPrompt' in new_settings:
                        SYSTEM_PROMPT_TEXT = new_settings['systemPrompt']
                        print(f"✓ Loaded custom system prompt from API ({len(SYSTEM_PROMPT_TEXT)} characters)")
                    
                    # Load bot settings from API (persists across deployments!)
                    if new_settings:
                        # IMPORTANT: Keep defaults, only override with API values (prevents reset on missing fields)
                        # This ensures that if API doesn't have a field, we keep the default
                        settings_to_merge = {k: v for k, v in new_settings.items() if k != 'systemPrompt'}
                        if settings_to_merge:
                            # Merge: Defaults stay, API overrides only what it has
                            for key, value in settings_to_merge.items():
                                if value is not None:  # Only update if API has a value
                                    BOT_SETTINGS[key] = value
                            
                            print(f"✓ Loaded bot settings from API (persisted across deployments)")
                            print(f"   satisfaction_delay={BOT_SETTINGS.get('satisfaction_delay', 30)}s, "
                                  f"temperature={BOT_SETTINGS.get('ai_temperature', 1.0)}, "
                                  f"retention={BOT_SETTINGS.get('solved_post_retention_days', 30)}d, "
                                  f"notification_channel={BOT_SETTINGS.get('support_notification_channel_id', 'Not set')}")
                            
                            # Update task intervals if they changed
                            old_interval = BOT_SETTINGS.get('high_priority_check_interval_hours', 2.0)
                            new_interval = BOT_SETTINGS.get('high_priority_check_interval_hours', 2.0)
                            if old_interval != new_interval and check_old_posts.is_running():
                                try:
                                    check_old_posts.change_interval(hours=new_interval)
                                    print(f"✓ Updated check_old_posts interval to {new_interval} hours")
                                except Exception as interval_error:
                                    print(f"⚠ Could not update check_old_posts interval: {interval_error}")
                    else:
                        # No settings in API yet - save our defaults to establish them
                        print(f"ℹ️ No settings in API - saving defaults to establish baseline")
                        await save_bot_settings_to_api()
                    
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

async def increment_leaderboard(user: discord.User):
    """Increment solved count for a staff member"""
    from datetime import datetime
    
    current_month = datetime.now().strftime("%Y-%m")
    
    # Reset if new month
    if LEADERBOARD_DATA['month'] != current_month:
        print(f"🔄 New month detected! Resetting leaderboard from {LEADERBOARD_DATA['month']} to {current_month}")
        LEADERBOARD_DATA['month'] = current_month
        LEADERBOARD_DATA['scores'] = {}
    
    user_id = str(user.id)
    
    # Initialize or increment user's score
    if user_id not in LEADERBOARD_DATA['scores']:
        LEADERBOARD_DATA['scores'][user_id] = {
            'username': user.display_name,
            'solved_count': 0,
            'avatar_url': str(user.display_avatar.url) if user.display_avatar else ''
        }
    
    LEADERBOARD_DATA['scores'][user_id]['solved_count'] += 1
    LEADERBOARD_DATA['scores'][user_id]['username'] = user.display_name  # Update in case they changed name
    LEADERBOARD_DATA['scores'][user_id]['avatar_url'] = str(user.display_avatar.url) if user.display_avatar else ''
    
    print(f"📊 Leaderboard: {user.display_name} now has {LEADERBOARD_DATA['scores'][user_id]['solved_count']} solved threads this month")
    
    # Save to API
    await save_leaderboard_to_api()

async def save_leaderboard_to_api():
    """Save leaderboard data back to the dashboard API"""
    if 'your-vercel-app' in DATA_API_URL:
        return  # Skip if not configured
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {'action': 'update_leaderboard', 'leaderboard': LEADERBOARD_DATA}
            async with session.post(DATA_API_URL, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print(f"✓ Leaderboard saved to dashboard")
                    return True
    except Exception as e:
        print(f"⚠ Failed to save leaderboard: {e}")
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
def classify_issue(question: str) -> str:
    """Classify issue type using regex patterns (simple classification)"""
    import re
    question_lower = question.lower()
    
    # Issue type patterns (regex-based classification)
    issue_patterns = {
        'Bug/Error': [r'\b(error|crash|bug|broken|not working|doesn\'t work|failed|failure)\b'],
        'Performance': [r'\b(slow|lag|freeze|frozen|stuck|hanging|performance|fps|frame)\b'],
        'Installation/Setup': [r'\b(install|setup|download|update|install|configure|activation|license)\b'],
        'Display/Graphics': [r'\b(display|graphics|screen|visual|render|flicker|glitch|resolution|scaling)\b'],
        'Connection/Network': [r'\b(connection|network|connect|disconnect|timeout|offline|server)\b'],
        'Account/Authentication': [r'\b(account|login|password|auth|sign in|sign up|register)\b'],
        'Feature Request': [r'\b(add|feature|request|suggest|improve|enhance|new)\b'],
        'Question/Help': [r'\b(how|what|why|where|when|help|question|tutorial|guide)\b'],
        'Macro/Automation': [r'\b(macro|automation|auto|gather|collect|farm|path|navigation)\b'],
        'Other': []  # Default fallback
    }
    
    # Check each pattern
    for issue_type, patterns in issue_patterns.items():
        if issue_type == 'Other':
            continue  # Skip default
        for pattern in patterns:
            if re.search(pattern, question_lower):
                return issue_type
    
    # Default to 'Other' if no pattern matches
    return 'Other'

async def apply_issue_type_tag(thread, issue_type):
    """Apply a Discord forum tag based on issue type using configured tag IDs (only bot/mods can add tags)"""
    try:
        # Get the parent forum channel
        if not hasattr(thread, 'parent') or not thread.parent:
            print(f"⚠ Could not get parent channel for thread {thread.id}")
            return
        
        parent_channel = thread.parent
        if not isinstance(parent_channel, discord.ForumChannel):
            print(f"⚠ Parent channel is not a ForumChannel")
            return
        
        # Get tag IDs from bot settings
        tag_ids = BOT_SETTINGS.get('issue_type_tag_ids', {})
        tag_id = tag_ids.get(issue_type)
        
        if not tag_id:
            print(f"⚠ No tag ID configured for issue type '{issue_type}'. Use /set_tag_id to configure.")
            return
        
        # Get available tags from the forum channel
        available_tags = parent_channel.available_tags
        
        # Find tag by ID
        matching_tag = None
        try:
            tag_id_int = int(tag_id)
            for tag in available_tags:
                if tag.id == tag_id_int:
                    matching_tag = tag
                    break
        except (ValueError, TypeError):
            print(f"⚠ Invalid tag ID '{tag_id}' for issue type '{issue_type}'. Tag ID must be a number.")
            return
        
        if matching_tag:
            # Get current applied tags
            current_tags = list(thread.applied_tags) if hasattr(thread, 'applied_tags') and thread.applied_tags else []
            
            # Check if tag is already applied
            if matching_tag not in current_tags:
                # Add the tag
                current_tags.append(matching_tag)
                try:
                    await thread.edit(applied_tags=current_tags)
                    print(f"✓ Applied tag '{matching_tag.name}' (ID: {matching_tag.id}) to thread {thread.id} for issue type '{issue_type}'")
                except discord.errors.Forbidden:
                    print(f"⚠ Bot doesn't have permission to edit tags on thread {thread.id}")
                except Exception as e:
                    print(f"⚠ Could not apply tag: {e}")
            else:
                print(f"ℹ Tag '{matching_tag.name}' already applied to thread {thread.id}")
        else:
            print(f"⚠ Tag ID {tag_id} not found in forum channel. Available tags: {[(t.id, t.name) for t in available_tags]}")
            print(f"   Use /list_forum_tags to see available tag IDs, then use /set_tag_id to configure.")
    except Exception as e:
        print(f"⚠ Error applying issue type tag: {e}")
        import traceback
        traceback.print_exc()

async def remove_support_notification(thread_id):
    """Remove support notification message when issue is classified"""
    if thread_id in support_notification_messages:
        try:
            thread = bot.get_channel(thread_id)
            if thread:
                msg_id = support_notification_messages[thread_id]
                try:
                    msg = await thread.fetch_message(msg_id)
                    await msg.delete()
                    print(f"✓ Removed support notification message from thread {thread_id}")
                    del support_notification_messages[thread_id]
                except discord.NotFound:
                    # Message already deleted
                    del support_notification_messages[thread_id]
                except Exception as e:
                    print(f"⚠ Could not delete notification message: {e}")
        except Exception as e:
            print(f"⚠ Error removing support notification: {e}")

def get_auto_response(query: str) -> str | None:
    """Check if query matches any auto-response triggers - STRICT matching: only use if user asks exactly what auto response has"""
    import re
    query_lower = query.lower().strip()
    
    # Debug: Log what we're checking
    if len(AUTO_RESPONSES) == 0:
        print(f"⚠ No auto-responses loaded. Query: '{query[:50]}...'")
    
    for auto_response in AUTO_RESPONSES:
        trigger_keywords = auto_response.get('triggerKeywords', [])
        response_text = auto_response.get('responseText', '')
        
        # STRICT MATCHING: Check if the query is asking EXACTLY what the auto-response covers
        # This means ALL trigger keywords should be present, or the query should be very similar to the response topic
        
        # Method 1: Check if ALL trigger keywords are present (exact match)
        all_keywords_present = True
        matched_keywords = []
        for keyword in trigger_keywords:
            keyword_lower = keyword.lower()
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            if re.search(pattern, query_lower):
                matched_keywords.append(keyword)
            else:
                all_keywords_present = False
        
        # Method 2: Check if query is very similar to response text (fuzzy match for exact questions)
        # Extract key phrases from response text
        response_lower = response_text.lower()
        # Simple check: if query contains most words from response title/name, it's likely asking exactly that
        auto_name = auto_response.get('name', '').lower()
        
        # Only use auto-response if:
        # 1. ALL trigger keywords are present, OR
        # 2. Query is very similar to the auto-response name/topic (80%+ keyword match)
        if all_keywords_present and len(trigger_keywords) > 0:
            print(f"✓ Auto-response matched (ALL keywords): '{auto_response.get('name', 'Unknown')}' (keywords: {matched_keywords})")
            print(f"   Query was: '{query[:100]}...'")
            return response_text
        
        # Check if query is asking exactly about this topic (high keyword match ratio)
        if len(trigger_keywords) > 0:
            match_ratio = len(matched_keywords) / len(trigger_keywords)
            # Require at least 80% of keywords to match, and at least 2 keywords
            if match_ratio >= 0.8 and len(matched_keywords) >= 2:
                print(f"✓ Auto-response matched (high match ratio): '{auto_response.get('name', 'Unknown')}' ({len(matched_keywords)}/{len(trigger_keywords)} keywords)")
                print(f"   Query was: '{query[:100]}...'")
                return response_text
    
    # Debug: Log what we checked if no match
    if AUTO_RESPONSES:
        all_keywords = [kw for auto in AUTO_RESPONSES for kw in auto.get('triggerKeywords', [])]
        print(f"ℹ No auto-response match (using AI instead). Checked {len(AUTO_RESPONSES)} auto-responses with {len(all_keywords)} total keywords.")
        print(f"   Query was: '{query[:100]}...'")
    
    return None

def find_relevant_rag_entries(query, db=RAG_DATABASE, top_k=5, similarity_threshold=0.2):
    """Find relevant RAG entries using vector similarity search (Pinecone or local fallback)
    
    Args:
        query: User's question
        db: RAG database to search (defaults to RAG_DATABASE)
        top_k: Number of top results to return
        similarity_threshold: Minimum cosine similarity score (0.0-1.0)
    
    Returns:
        List of relevant RAG entries sorted by similarity
    """
    model = get_embedding_model()
    
    # Fallback to keyword search if embeddings not available
    if model is None:
        print("⚠️ Using keyword-based search (embeddings not available)")
        return find_relevant_rag_entries_keyword(query, db)
    
    # Try Pinecone first if available
    index = init_pinecone() if USE_PINECONE else None
    
    if index:
        try:
            # COST OPTIMIZATION: Use Pinecone for all vector operations (saves Railway CPU)
            # Compute query embedding (minimal CPU - just encoding)
            query_embedding = model.encode(query, convert_to_numpy=True)
            query_embedding_list = query_embedding.tolist()
            
            # Query Pinecone (all similarity computation happens in Pinecone cloud)
            query_results = index.query(
                vector=query_embedding_list,
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            # Process results - reconstruct entries from Pinecone metadata
            # This avoids needing to store full entries in Railway memory
            results = []
            all_matches = []
            for match in query_results.matches:
                entry_id = match.id
                metadata = match.metadata or {}
                similarity_score = float(match.score)
                
                # Reconstruct entry from Pinecone metadata (saves Railway memory)
                # Try to get full entry from db first (for complete data), fallback to metadata
                entry = next((e for e in db if e.get('id') == entry_id), None)
                if not entry:
                    # Fallback: reconstruct from metadata if not in local db
                    entry = {
                        'id': entry_id,
                        'title': metadata.get('title', 'Unknown'),
                        'content': metadata.get('content', ''),
                        'keywords': metadata.get('keywords', '').split() if metadata.get('keywords') else []
                    }
                
                all_matches.append({
                    'entry': entry,
                    'similarity': similarity_score
                })
                
                # Pinecone returns scores as similarity (0-1), filter by threshold
                if similarity_score >= similarity_threshold:
                    results.append({
                        'entry': entry,
                        'similarity': similarity_score
                    })
            
            # Log all matches for debugging (even below threshold)
            if all_matches:
                top_similarity = all_matches[0]['similarity']
                print(f"🌲 Pinecone search: Found {len(query_results.matches)} total matches, {len(results)} above threshold {similarity_threshold}")
                print(f"   Top similarity: {top_similarity:.3f}")
                for i, item in enumerate(all_matches[:5], 1):
                    entry_title = item['entry'].get('title', 'Unknown')
                    above_threshold = "✓" if item['similarity'] >= similarity_threshold else "⚠"
                    print(f"   {above_threshold} {i}. '{entry_title}' (similarity: {item['similarity']:.3f})")
            else:
                print(f"⚠️ Pinecone returned no matches at all")
                print(f"   Total RAG entries in database: {len(db)}")
            
            # If no results above threshold but we have matches, use top match anyway (lenient fallback)
            if not results and all_matches:
                print(f"⚠️ No matches above threshold {similarity_threshold}, but using top match anyway (similarity: {all_matches[0]['similarity']:.3f})")
                results = [all_matches[0]]
            
            return [item['entry'] for item in results]
            
        except Exception as e:
            print(f"⚠️ Error in Pinecone search: {e}")
            import traceback
            traceback.print_exc()
            print("   Falling back to keyword-based search (saves Railway CPU costs)")
            return find_relevant_rag_entries_keyword(query, db)
    
    # COST OPTIMIZATION: Don't use local CPU-based vector search - it's expensive!
    # If Pinecone is not available, use keyword search instead (free, no CPU cost)
    print("⚠️ Pinecone not available - using keyword-based search (cost-effective, no CPU cost)")
    print("   💡 Set PINECONE_API_KEY to enable cost-effective vector search")
    return find_relevant_rag_entries_keyword(query, db)

def find_relevant_rag_entries_keyword(query, db=RAG_DATABASE):
    """Fallback keyword-based search (used when embeddings unavailable)"""
    query_words = set(query.lower().split())
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'be'}
    query_words = {word for word in query_words if word not in stopwords}

    scored_entries = []
    for entry in db:
        score = 0
        entry_title = entry.get('title', '').lower()
        entry_content = entry.get('content', '').lower()
        entry_keywords = ' '.join(entry.get('keywords', [])).lower()

        for word in query_words:
            if word in entry_title:
                score += 5
            if word in entry_keywords:
                score += 3
            if word in entry_content:
                score += 1

        if score > 0:
            scored_entries.append({'entry': entry, 'score': score})

    scored_entries.sort(key=lambda x: x['score'], reverse=True)
    
    if scored_entries:
        print(f"📊 Keyword search: Found {len(scored_entries)} relevant entries (top score: {scored_entries[0]['score']})")
    
    return [item['entry'] for item in scored_entries[:5]]

SYSTEM_PROMPT = (
    "You are Revolution Macro support bot for Bee Swarm Simulator (BSS). You are an expert on BSS game mechanics and Revolution Macro automation.\n\n"
    
    "CRITICAL RULES:\n"
    "1. Read the POST TITLE first - it contains the key issue\n"
    "2. ALWAYS attempt a direct answer based on title + message\n"
    "3. Use knowledge base if available\n"
    "4. Keep answers SHORT and actionable (2-4 sentences MAX)\n"
    "5. Reference specific BSS/Revolution Macro settings when relevant\n"
    "6. If you truly can't help, acknowledge human support is available\n\n"
    
    "BEE SWARM SIMULATOR (BSS) KNOWLEDGE:\n"
    "- Fields: Sunflower, Dandelion, Blue Flower, Clover, Spider, Mountain Top, Rose, Stump, Cactus, Pine Tree, Pineapple Patch, Bamboo Field, etc.\n"
    "- Resources: Pollen (gathered from flowers), Honey (converted from pollen), Nectar (from flowers), Tickets, etc.\n"
    "- Bees: Different bee types (Basic, Rare, Epic, Legendary, Mythic, etc.) with different abilities\n"
    "  - Red bees: Attack-focused, convert pollen to honey\n"
    "  - Blue bees: Gather-focused, collect more pollen\n"
    "  - White bees: Convert-focused, convert pollen faster\n"
    "- Hives: Where bees are stored, need to claim hive slots\n"
    "- Quests: NPC quests, daily quests, repeatable quests\n"
    "- Events: Robobear challenges, Beesmas, etc.\n"
    "- Mechanics: Conversion (pollen to honey), gathering, movement, field switching\n\n"
    
    "REVOLUTION MACRO FOR BSS FEATURES:\n"
    "- Auto-gathering: Automatically collects pollen from flowers in fields\n"
    "- Auto-conversion: Converts pollen to honey automatically\n"
    "- Hive claiming: Automatically claims hive slots\n"
    "- Field navigation: Smart pathfinding between fields\n"
    "- Quest automation: Auto-completes quests\n"
    "- Robobear automation: Handles Robobear challenges\n"
    "- Planter automation: Manages planters automatically\n"
    "- Auto-deposit: Deposits honey to hive\n"
    "- Movement settings: BSS speed, routing, alignment modes\n"
    "- Hive detection: Detects and claims correct hive slots\n\n"
    
    "COMMON BSS MACRO ISSUES & SOLUTIONS:\n"
    "- Character spinning/walking in circles: Camera mode must be Classic/Default in Roblox, not fullscreen, display scaling 100%\n"
    "- Not claiming hive: Hive claim method must be set to 'detect' in Settings → Game → Join\n"
    "- Not detecting hive: Close game first, then start macro so it can detect properly\n"
    "- Alignment failed: Enable High Alignment mode in Settings → Game → Routing → Use High Alignment\n"
    "- Speed mismatch: BSS speed in macro must match in-game speed (check gear icon, no speed buffs)\n"
    "- Low FPS issues: Enable High Alignment mode for more reliable pathing\n"
    "- Character resetting: Auto-deposit may conflict with gathering, check Pause While Converting Honey\n"
    "- Wrong field: Check routing settings, field selection, and pathfinding\n"
    "- Not converting honey: Check conversion settings, ensure not stuck in gather loop\n"
    "- Red cannon issues: Check cannon settings, ensure proper field selection\n\n"
    
    "HOW TO ANSWER:\n"
    "✅ GOOD: 'For spinning issues: 1. Set Roblox camera to Classic/Default 2. Turn off fullscreen 3. Set display scaling to 100%'\n"
    "❌ BAD: 'Could you clarify what's happening?' [Wasting time!]\n\n"
    "✅ GOOD: 'Hive detection issues? Close the game first, then start the macro. Also check Settings → Game → Join → Hive claim method is set to detect.'\n"
    "❌ BAD: 'This could be several things...' [Too vague!]\n\n"
    "✅ GOOD: 'Alignment failed? Enable High Alignment mode: Settings → Game → Routing → Use High Alignment. This uses more reliable paths.'\n"
    "❌ BAD: 'Try checking your settings' [Not specific enough!]\n\n"
    
    "RESPONSE FORMAT:\n"
    "- Start with the solution, not questions\n"
    "- Use numbered steps for troubleshooting\n"
    "- Reference exact settings paths (Settings → Game → Join → Hive claim method)\n"
    "- Mention BSS-specific terms correctly (pollen, honey, fields, bees, hives)\n"
    "- Be concise but complete\n\n"
    
    "IF YOU CAN'T HELP:\n"
    "Say: 'I don't have specific info on this BSS issue. Our support team can help - they usually respond within 24 hours.'\n\n"
    
    "Remember: POST TITLE = Main clue. Answer directly with BSS-specific solutions. Be SHORT but accurate. Human support is backup."
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

async def download_images_for_gemini(attachments):
    """Download images from Discord attachments and prepare for Gemini vision model"""
    image_parts = []
    try:
        for attachment in attachments:
            # Only process images
            if attachment.content_type and "image" in attachment.content_type:
                try:
                    print(f"📥 Downloading image: {attachment.filename}")
                    
                    # Download the image with timeout
                    image_bytes = await asyncio.wait_for(attachment.read(), timeout=10.0)
                    
                    # Validate image size (max 20MB)
                    if len(image_bytes) > 20 * 1024 * 1024:
                        print(f"⚠ Image {attachment.filename} too large ({len(image_bytes) / 1024 / 1024:.1f}MB), skipping")
                        continue
                    
                    # Gemini accepts image bytes directly
                    import PIL.Image
                    import io
                    image = PIL.Image.open(io.BytesIO(image_bytes))
                    
                    # Convert to RGB if needed
                    if image.mode in ('RGBA', 'LA', 'P'):
                        rgb_image = PIL.Image.new('RGB', image.size, (255, 255, 255))
                        if image.mode == 'P':
                            image = image.convert('RGBA')
                        rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                        image = rgb_image
                    elif image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    image_parts.append(image)
                    print(f"✅ Image prepared: {attachment.filename} ({image.size[0]}x{image.size[1]})")
                except asyncio.TimeoutError:
                    print(f"⚠ Timeout downloading image: {attachment.filename}")
                    continue
                except Exception as img_error:
                    print(f"⚠ Error processing image {attachment.filename}: {img_error}")
                    continue
        
        return image_parts if image_parts else None
    
    except Exception as e:
        print(f"⚠ Error in download_images_for_gemini: {e}")
        return None

async def generate_ai_response(query, context_entries, image_parts=None):
    """Generate an AI response using Gemini API with knowledge base context - SIMPLIFIED
    
    Args:
        query: The user's question
        context_entries: Relevant RAG entries to use as context
        image_parts: Optional images to include
    """
    from datetime import datetime
    import hashlib
    
    # Use the main key manager (all keys available for all operations)
    key_manager = gemini_key_manager
    api_calls_dict = gemini_api_calls_by_key
    
    if not key_manager:
        raise Exception("No key manager available")
    
    if not key_manager.api_keys or len(key_manager.api_keys) == 0:
        print("❌ CRITICAL: No API keys available in key manager!")
        return "I'm having trouble connecting to my AI service right now. A human support agent will help you shortly."
    
    print(f"🔑 Key manager has {len(key_manager.api_keys)} key(s) available")
    
    # Check cache first (skip if images provided)
    if not image_parts:
        # Create cache key from query + context IDs
        context_ids = [c.get('id', '') for c in context_entries] if context_entries else []
        cache_key = hashlib.md5(f"{query.lower()}:{':'.join(sorted(context_ids))}".encode()).hexdigest()
        
        # Check if we have a cached response
        if cache_key in ai_response_cache:
            cached_response, cached_time = ai_response_cache[cache_key]
            age = (datetime.now() - cached_time).total_seconds()
            if age < AI_CACHE_TTL:
                print(f"✓ Using cached AI response (age: {int(age)}s)")
                return cached_response
            else:
                # Expired, remove from cache
                del ai_response_cache[cache_key]
    
    # DISABLED: Image processing
    image_parts = None
    
    # Use API system prompt if available, otherwise use default
    system_instruction = SYSTEM_PROMPT_TEXT if SYSTEM_PROMPT_TEXT else SYSTEM_PROMPT
    
    # Get AI settings from bot settings
    temperature = BOT_SETTINGS.get('ai_temperature', 1.0)
    max_tokens = BOT_SETTINGS.get('ai_max_tokens', 2048)
    
    # Try models in order - Gemini 1.5 was shut down Sep 2025, use 2.5 models
    models_to_try = [
        'gemini-2.5-flash',  # Current model (replaced 1.5-flash)
        'gemini-2.5-pro',   # Advanced model
        'gemini-2.5-flash-lite',  # Cost-effective variant
        'gemini-pro',  # Legacy fallback
        'gemini-flash-latest',  # Legacy fallback
        'gemini-pro-latest'  # Legacy fallback
    ]
    
    # Log knowledge base usage
    if context_entries:
        print(f"📚 Using {len(context_entries)} knowledge base entries:")
        for entry in context_entries[:2]:
            print(f"   - {entry.get('title', 'Unknown')}")
    else:
        print(f"⚠️ No knowledge base entries provided - using AI general knowledge")
    
    # Check rate limit before making API call
    if not await check_rate_limit(key_manager, api_calls_dict):
        print(f"⚠️ Rate limit reached, waiting before generating response...")
        # Wait for rate limit to clear
        current_key = key_manager.get_current_key()
        key_short = current_key[:10] + '...'
        api_calls = api_calls_dict.get(key_short, deque())
        if api_calls:
            oldest_call = api_calls[0]
            wait_time = 60 - (datetime.now() - oldest_call).total_seconds()
            if wait_time > 0:
                print(f"   Waiting {wait_time:.1f}s for rate limit to clear...")
                await asyncio.sleep(wait_time)
        # Try rotating to a different key
        key_manager.rotate_key(force_round_robin=True)
    
    # Use key manager for automatic rotation
    current_key = key_manager.get_current_key()
    print(f"🤖 Generating AI response with key {current_key[:15]}...")
    
    for model_name in models_to_try:
        try:
            print(f"🔧 Trying model '{model_name}'...")
            
            # Use key manager to create model (handles rotation automatically)
            # Try with system_instruction first, fallback to without if needed
            model = None
            model_error = None
            
            # Try to create model - try with system_instruction first, then without
            model = None
            try:
                model = key_manager.create_model_with_retry(model_name, system_instruction=system_instruction)
            except Exception as e:
                # If system_instruction fails, try without it
                try:
                    model = key_manager.create_model_with_retry(model_name)
                except Exception as e2:
                    # Both failed, continue to next model
                    print(f"   ⚠️ Model '{model_name}' failed, trying next model...")
                    continue
            
            if model is None:
                continue
            
            # Configure generation settings
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            # Build user context WITH KNOWLEDGE BASE
            user_context = build_user_context(query, context_entries)
            
            # Generate response - log which key is being used
            current_key = key_manager.get_current_key()
            key_short = current_key[:15] + '...'
            print(f"💬 Calling Gemini API with key {key_short} and model {model_name}...")
            
            # Track the API call BEFORE making it to prevent race conditions
            # This ensures concurrent requests see the updated count immediately
            track_api_call(key_manager, api_calls_dict)
            
            loop = asyncio.get_event_loop()
            
            # Define function outside lambda to avoid closure issues
            def generate_sync():
                try:
                    return model.generate_content(user_context, generation_config=generation_config)
                except Exception as sync_error:
                    # Re-raise with more context
                    raise Exception(f"API call failed in sync context: {type(sync_error).__name__}: {str(sync_error)}") from sync_error
            
            try:
                print(f"   📡 Making API call to Gemini...")
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, generate_sync),
                    timeout=30.0
                )
                print(f"   ✓ Received response from API")
            except asyncio.TimeoutError:
                print(f"   ⚠️ Timeout waiting for API response from '{model_name}' (30s)")
                key_manager.mark_key_error(current_key, is_rate_limit=False)
                continue
            except Exception as api_error:
                error_str = str(api_error).lower()
                print(f"   ⚠️ API call failed: {str(api_error)[:200]}")
                
                # Handle quota vs rate limits differently
                if 'resource exhausted' in error_str and 'quota' in error_str:
                    # Billing quota exceeded
                    key_short_err = current_key[:10] + '...'
                    print(f"   ❌ QUOTA EXCEEDED (billing): All keys from same account share quota")
                    key_manager.key_rate_limited[key_short_err] = True
                    key_manager.key_rate_limit_time[key_short_err] = datetime.now()
                    key_manager.rotate_key(force_round_robin=True)
                elif 'rate limit' in error_str or ('429' in error_str and 'quota' not in error_str):
                    # Per-minute rate limit (temporary)
                    key_short_err = current_key[:10] + '...'
                    key_manager.key_rate_limited[key_short_err] = True
                    key_manager.key_rate_limit_time[key_short_err] = datetime.now()
                    key_manager.rotate_key(force_round_robin=True)
                # Try next model
                continue
            
            # Check if response has text attribute BEFORE marking success
            if not hasattr(response, 'text'):
                print(f"   ⚠️ Response object missing 'text' attribute: {type(response)}")
                print(f"   Response object: {response}")
                key_manager.mark_key_error(current_key, is_rate_limit=False)
                continue
            
            # Mark the current key as successful (API call succeeded)
            key_manager.mark_key_success(current_key)
            print(f"✅ API call succeeded with key {key_short}")
            
            response_text = response.text
            
            # Check if response is empty
            if not response_text or len(response_text.strip()) == 0:
                print(f"   ⚠️ Empty response from '{model_name}', trying next model...")
                continue
            
            # Cache the response (if no images)
            if not image_parts and 'cache_key' in locals():
                ai_response_cache[cache_key] = (response_text, datetime.now())
                print(f"✓ Cached AI response (cache size: {len(ai_response_cache)})")
                
                # Clean old cache entries if cache gets too large (prevent memory leaks)
                if len(ai_response_cache) > 100:
                    sorted_cache = sorted(ai_response_cache.items(), key=lambda x: x[1][1])
                    for old_key, _ in sorted_cache[:20]:
                        del ai_response_cache[old_key]
                    print(f"✓ Cleaned cache (now {len(ai_response_cache)} entries)")
                
                # Also clean expired entries periodically (prevent memory leaks)
                current_time = datetime.now()
                expired_keys = [
                    key for key, (_, timestamp) in ai_response_cache.items()
                    if (current_time - timestamp).total_seconds() > AI_CACHE_TTL
                ]
                for key in expired_keys:
                    del ai_response_cache[key]
                if expired_keys:
                    print(f"✓ Cleaned {len(expired_keys)} expired cache entries")
            
            # Success!
            print(f"✅ SUCCESS! Got {len(response_text)} character response from '{model_name}'")
            if context_entries:
                print(f"   📚 Response based on {len(context_entries)} knowledge base entries")
            return response_text
                
        except asyncio.TimeoutError:
            # Timeout is transient - don't mark as permanent error, just try next model
            print(f"   ⚠️ Timeout with '{model_name}' (transient), trying next model...")
            continue
        except Exception as e:
            error_msg = str(e).lower()
            error_type = type(e).__name__
            current_key = key_manager.get_current_key()
            
            print(f"   ❌ '{model_name}' failed: {error_type}: {str(e)[:200]}")
            
            # Print full traceback for debugging
            import traceback
            print(f"   Full error details:")
            traceback.print_exc()
            
            # If it's a model error, try next model. Otherwise, might be key issue
            if 'model' in error_msg and ('not found' in error_msg or 'invalid' in error_msg):
                print(f"   ⚠️ Model '{model_name}' not available, trying next...")
                continue
            elif 'resource exhausted' in error_msg.lower() and 'quota' in error_msg.lower():
                # Check if it's free tier limit (20/day) vs paid tier quota
                is_free_tier = 'free_tier' in error_msg.lower() or 'free tier' in error_msg.lower() or 'limit: 20' in error_msg
                key_short = current_key[:10] + '...'
                if is_free_tier:
                    print(f"   ❌ FREE TIER LIMIT EXCEEDED (20 requests/day per model)")
                    print(f"   💡 This key is on the FREE tier - only 20 requests/day allowed!")
                    print(f"   💡 Upgrade to PAID tier: https://aistudio.google.com/app/apikey")
                    print(f"   💡 Paid tier has 1500 requests/minute - much higher limits")
                else:
                    print(f"   ❌ QUOTA EXCEEDED (billing limit): {error_msg[:150]}")
                    print(f"   💡 All keys from the same Google account share the same quota.")
                    print(f"   💡 Check billing: https://console.cloud.google.com/billing")
                    print(f"   💡 Or use keys from different Google accounts.")
                # Mark as rate limited temporarily so we don't keep trying this key
                key_manager.key_rate_limited[key_short] = True
                key_manager.key_rate_limit_time[key_short] = datetime.now()
                continue
            elif 'rate limit' in error_msg.lower() or ('429' in error_msg and 'quota' not in error_msg.lower()):
                # Actual rate limit (per-minute) - temporary, will reset
                key_short = current_key[:10] + '...'
                key_manager.key_rate_limited[key_short] = True
                key_manager.key_rate_limit_time[key_short] = datetime.now()
                print(f"   ⚠️ Rate limit detected (temporary, per-minute), will try next key/model...")
                continue
            elif 'api key' in error_msg or 'auth' in error_msg or '403' in error_msg or 'permission denied' in error_msg or 'leaked' in error_msg:
                # API key error - only mark if we've seen this multiple times (might be transient)
                # Don't mark on first failure
                print(f"   ⚠️ Possible API key issue (might be transient)...")
                if 'leaked' in error_msg:
                    # Leaked keys are definitely invalid - mark after checking
                    key_manager.mark_key_error(current_key, is_rate_limit=False)
                    print(f"   ❌ API key appears to be leaked. Get a new key: https://aistudio.google.com/app/apikey")
                else:
                    # Other auth errors might be transient - don't mark immediately
                    print(f"   ⚠️ Auth error (will retry with next model/key)...")
                print(f"   Full error: {str(e)[:200]}")
                # Still try next model in case it's model-specific
                continue
            elif 'model' in error_msg and ('not found' in error_msg or 'invalid' in error_msg):
                # Model compatibility issue - not a key error, just try next model
                print(f"   ⚠️ Model compatibility issue, trying next model...")
                continue
            else:
                # Transient error - don't mark as permanent error, just try next model
                print(f"   ⚠️ Transient error, trying next model...")
                continue
    
    # All models failed
    print(f"\n{'='*60}")
    print(f"❌ ALL MODELS FAILED!")
    print(f"{'='*60}")
    try:
        current_key_short = key_manager.get_current_key()[:20] if key_manager.get_current_key() else "N/A"
        total_keys = len(key_manager.api_keys)
        usage_stats = key_manager.get_usage_stats()
        
        print(f"   Total API keys loaded: {total_keys}")
        print(f"   Current key: {current_key_short}...")
        print(f"   Query attempted: {query[:100]}")
        print(f"   Context entries: {len(context_entries)}")
        
        # Show key health status
        print(f"\n   Key Health Status:")
        all_quota_limited = True
        for key_short, stats in usage_stats.items():
            rate_limited = "🔴 RATE LIMITED" if stats.get('rate_limited', False) else "🟢 OK"
            success_rate = stats.get('success_rate', 0)
            total_calls = stats.get('total_calls', 0)
            print(f"     {key_short}: {rate_limited} | {total_calls} calls | {success_rate:.0f}% success")
            if not stats.get('rate_limited', False):
                all_quota_limited = False
        
        if all_quota_limited and total_keys > 1:
            print(f"\n   ⚠️ ALL KEYS HITTING QUOTA LIMITS!")
            print(f"   💡 All API keys from the same Google account share the same billing quota.")
            print(f"   💡 Check your quota/billing: https://console.cloud.google.com/billing")
            print(f"   💡 Or use keys from different Google accounts (different billing).")
        else:
            print(f"\n   ⚠️ If you see 'leaked' or '403' errors above, your API key needs to be replaced.")
            print(f"   📝 Get a new key: https://aistudio.google.com/app/apikey")
            print(f"   Then update GEMINI_API_KEY in Railway environment variables and restart the bot.")
    except Exception as e:
        print(f"   ERROR getting key info: {e}")
        import traceback
        traceback.print_exc()
    print(f"{'='*60}\n")
    
    # Try one final direct test to see if API works at all
    try:
        print("🔍 Running final diagnostic test...")
        test_key = key_manager.get_current_key()
        genai.configure(api_key=test_key)
        test_model = genai.GenerativeModel('gemini-2.5-flash')
        test_response = test_model.generate_content("Say hello")
        print(f"   ✓ Direct API test SUCCEEDED: {test_response.text[:50]}")
        print(f"   ⚠️ This means the API works, but something in generate_ai_response failed")
    except Exception as test_error:
        print(f"   ✗ Direct API test FAILED: {test_error}")
        import traceback
        traceback.print_exc()
    
    return "I'm having trouble connecting to my AI service right now. A human support agent will help you shortly."


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
@tasks.loop(hours=6)  # Sync every 6 hours (reduced frequency to save CPU costs)
async def sync_data_task():
    """Periodically sync data from the dashboard"""
    await fetch_data_from_api()

@tasks.loop(hours=24)  # Check daily for month reset
async def check_leaderboard_reset():
    """Check if it's a new month and reset leaderboard"""
    from datetime import datetime
    
    try:
        current_month = datetime.now().strftime("%Y-%m")
        
        if LEADERBOARD_DATA['month'] and LEADERBOARD_DATA['month'] != current_month:
            old_month = datetime.strptime(LEADERBOARD_DATA['month'], "%Y-%m").strftime("%B %Y")
            print(f"🔄 New month detected! Resetting leaderboard from {old_month} to {datetime.now().strftime('%B %Y')}")
            
            # Log final standings before reset
            if LEADERBOARD_DATA['scores']:
                sorted_staff = sorted(LEADERBOARD_DATA['scores'].items(), key=lambda x: x[1]['solved_count'], reverse=True)
                print(f"📊 Final standings for {old_month}:")
                for i, (user_id, data) in enumerate(sorted_staff[:5], 1):
                    print(f"   {i}. {data.get('username', 'Unknown')}: {data.get('solved_count', 0)} solved")
            
            # Reset for new month
            LEADERBOARD_DATA['month'] = current_month
            LEADERBOARD_DATA['scores'] = {}
            await save_leaderboard_to_api()
            print(f"✅ Leaderboard reset for new month: {datetime.now().strftime('%B %Y')}")
        elif not LEADERBOARD_DATA['month']:
            # Initialize month if not set
            LEADERBOARD_DATA['month'] = current_month
            await save_leaderboard_to_api()
            print(f"✅ Initialized leaderboard for {datetime.now().strftime('%B %Y')}")
    except Exception as e:
        print(f"⚠ Error in check_leaderboard_reset task: {e}")
    # All data stored in memory (loaded from API) - no local files

@sync_data_task.before_loop
async def before_sync_task():
    await bot.wait_until_ready()

# --- BOT EVENTS ---
@tasks.loop(hours=6)  # Run every 6 hours
async def cleanup_processed_threads():
    """Clean up old processed threads and prevent memory leaks"""
    global processed_threads, support_notification_messages, thread_images, thread_response_type, not_solved_retry_count
    global satisfaction_timers, escalated_threads, no_review_threads, processing_threads, ask_cooldowns
    
    try:
        now = datetime.now()
        cleanup_count = 0
        
        # Clean up processed_threads older than 48 hours
        old_threads = [
            thread_id for thread_id, timestamp in processed_threads.items()
            if (now - timestamp).total_seconds() > 172800  # 48 hours
        ]
        for thread_id in old_threads:
            del processed_threads[thread_id]
            cleanup_count += 1
        
        # Clean up support_notification_messages for threads that no longer exist
        old_notifications = [
            thread_id for thread_id in support_notification_messages.keys()
            if thread_id not in processed_threads or (thread_id in processed_threads and (now - processed_threads[thread_id]).total_seconds() > 172800)
        ]
        for thread_id in old_notifications:
            del support_notification_messages[thread_id]
            cleanup_count += 1
        
        # Clean up thread_images (PIL images can be large)
        old_images = [
            thread_id for thread_id in thread_images.keys()
            if thread_id not in processed_threads or (thread_id in processed_threads and (now - processed_threads[thread_id]).total_seconds() > 86400)  # 24 hours
        ]
        for thread_id in old_images:
            # Close PIL images before deleting to free memory
            for img in thread_images[thread_id]:
                try:
                    if hasattr(img, 'close'):
                        img.close()
                except:
                    pass
            del thread_images[thread_id]
            cleanup_count += 1
        
        # Clean up other thread tracking dicts
        old_response_types = [
            thread_id for thread_id in thread_response_type.keys()
            if thread_id not in processed_threads or (thread_id in processed_threads and (now - processed_threads[thread_id]).total_seconds() > 172800)
        ]
        for thread_id in old_response_types:
            del thread_response_type[thread_id]
            cleanup_count += 1
        
        old_retry_counts = [
            thread_id for thread_id in not_solved_retry_count.keys()
            if thread_id not in processed_threads or (thread_id in processed_threads and (now - processed_threads[thread_id]).total_seconds() > 172800)
        ]
        for thread_id in old_retry_counts:
            del not_solved_retry_count[thread_id]
            cleanup_count += 1
        
        # Clean up satisfaction timers (cancel old tasks)
        old_timers = [
            thread_id for thread_id in satisfaction_timers.keys()
            if thread_id not in processed_threads or (thread_id in processed_threads and (now - processed_threads[thread_id]).total_seconds() > 172800)
        ]
        for thread_id in old_timers:
            timer_task = satisfaction_timers.get(thread_id)
            if timer_task and not timer_task.done():
                timer_task.cancel()
            del satisfaction_timers[thread_id]
            cleanup_count += 1
        
        # Clean up escalated_threads set
        old_escalated = [
            thread_id for thread_id in escalated_threads
            if thread_id not in processed_threads or (thread_id in processed_threads and (now - processed_threads[thread_id]).total_seconds() > 172800)
        ]
        for thread_id in old_escalated:
            escalated_threads.discard(thread_id)
            cleanup_count += 1
        
        # Clean up no_review_threads set
        old_no_review = [
            thread_id for thread_id in no_review_threads
            if thread_id not in processed_threads or (thread_id in processed_threads and (now - processed_threads[thread_id]).total_seconds() > 172800)
        ]
        for thread_id in old_no_review:
            no_review_threads.discard(thread_id)
            cleanup_count += 1
        
        # Clean up processing_threads set (should be empty, but clean up any stuck entries)
        old_processing = [
            thread_id for thread_id in processing_threads
            if thread_id not in processed_threads or (thread_id in processed_threads and (now - processed_threads[thread_id]).total_seconds() > 86400)  # 24 hours
        ]
        for thread_id in old_processing:
            processing_threads.discard(thread_id)
            cleanup_count += 1
        
        # Clean up ask_cooldowns (older than 1 hour)
        old_cooldowns = [
            user_id for user_id, timestamp in ask_cooldowns.items()
            if (now - timestamp).total_seconds() > 3600  # 1 hour
        ]
        for user_id in old_cooldowns:
            del ask_cooldowns[user_id]
            cleanup_count += 1
        
        if cleanup_count > 0:
            print(f"🧹 Memory cleanup: Removed {len(old_threads)} threads, {len(old_notifications)} notifications, {len(old_images)} images, {len(old_response_types)} response types, {len(old_retry_counts)} retry counts, {len(old_timers)} timers, {len(old_escalated)} escalated, {len(old_no_review)} no_review, {len(old_processing)} processing, {len(old_cooldowns)} cooldowns")
    except Exception as e:
        print(f"⚠️ Error in cleanup_processed_threads: {e}")
        import traceback
        traceback.print_exc()

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

async def notify_support_channel_summary(ping_support=False):
    """Send a paginated summary of all high priority posts to the support channel
    
    Args:
        ping_support: If True, ping the support role. If False, don't ping (default: False)
    """
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
                
                # Sort by recency/activity (most recent first)
                # Use updatedAt if available, otherwise use createdAt
                def get_sort_key(post):
                    updated_at = post.get('updatedAt') or post.get('createdAt', '')
                    if updated_at:
                        try:
                            # Try ISO format first (most common)
                            if 'T' in updated_at:
                                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            else:
                                # Fallback to strptime
                                dt = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                            return dt.timestamp()
                        except:
                            try:
                                # Try common formats
                                for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S']:
                                    try:
                                        dt = datetime.strptime(updated_at, fmt)
                                        return dt.timestamp()
                                    except:
                                        continue
                            except:
                                pass
                    # If parsing fails, put at end (oldest)
                    return 0
                
                high_priority_posts.sort(key=get_sort_key, reverse=True)
                
                # Build initial message (with optional ping)
                support_role_id = BOT_SETTINGS.get('support_role_id')
                initial_message = ""
                if ping_support and support_role_id:
                    initial_message = f"<@&{support_role_id}>\n\n"
                
                # Create paginated view
                view = HighPriorityPostsView(high_priority_posts, page_size=10)
                embed = view.create_embed(DISCORD_GUILD_ID)
                
                # Send the message with paginated embed
                if initial_message:
                    await support_channel.send(initial_message, embed=embed, view=view)
                else:
                    await support_channel.send(embed=embed, view=view)
                
                print(f"✅ Sent paginated high priority summary to support channel ({len(high_priority_posts)} posts, ping={ping_support})")
    
    except Exception as e:
        print(f"❌ Error sending support notification summary: {e}")
        import traceback
        traceback.print_exc()

# REMOVED: Local backups disabled - all data stored in Vercel KV API only
# Users can download backups anytime with /export_data command

@tasks.loop(hours=4)  # Check every 4 hours (optimized to save CPU costs)
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
                                            
                                            notification_msg = await thread_channel.send(embed=escalate_embed)
                                            # Track this message so we can delete it when classification is done
                                            support_notification_messages[thread_id] = notification_msg.id
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
                    # Send summary of all high priority posts to support channel (ping on new escalation)
                    await notify_support_channel_summary(ping_support=True)
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
    
    # CPU OPTIMIZATION: Only compute embeddings if enabled
    # COST OPTIMIZATION: Initialize Pinecone on startup if enabled
    # This ensures all vector operations use Pinecone (saves Railway CPU costs)
    if USE_PINECONE:
        print("🌲 Initializing Pinecone for cost-optimized vector search...")
        init_pinecone()  # Initialize connection early
    
    # COST OPTIMIZATION: Only compute embeddings if Pinecone is available
    # Never compute embeddings locally - it's expensive and increases Railway costs!
    if ENABLE_EMBEDDINGS and len(RAG_DATABASE) > 0:
        if USE_PINECONE:
            # Check if Pinecone needs initial embeddings
            index = init_pinecone()
            if index:
                try:
                    stats = index.describe_index_stats()
                    if stats.total_vector_count == 0:
                        if SKIP_EMBEDDING_BOOTSTRAP:
                            print("⚠️ Pinecone index empty, but SKIP_EMBEDDING_BOOTSTRAP=true. Skipping compute to avoid worker CPU usage. Seed index externally.")
                        else:
                            print("🔄 Pinecone index empty - computing initial embeddings in background...")
                            bot.loop.create_task(compute_embeddings_background())
                    else:
                        print(f"✅ Pinecone already has {stats.total_vector_count} vectors - ready to use!")
                except:
                    if SKIP_EMBEDDING_BOOTSTRAP:
                        print("⚠️ Could not describe Pinecone index and bootstrap is skipped. Seed index externally.")
                    else:
                        print("🔄 Computing initial embeddings for Pinecone in background...")
                        bot.loop.create_task(compute_embeddings_background())
        else:
            # COST OPTIMIZATION: Don't compute embeddings locally - use keyword search instead
            print("⚠️ Pinecone not configured - skipping embeddings to save Railway CPU costs")
            print("   Bot will use keyword-based search (free, no CPU cost)")
            print("   💡 Set PINECONE_API_KEY to enable cost-effective vector search")
    elif not ENABLE_EMBEDDINGS:
        print("ℹ Using keyword search only (cost-effective, no CPU cost)")
        if HAS_PINECONE_CONFIG:
            print("   💡 Pinecone is configured - set ENABLE_EMBEDDINGS=true to enable vector search")

    # Start periodic sync
    sync_data_task.start()
    check_leaderboard_reset.start()
    
    # Start old post check task
    if not check_old_posts.is_running():
        check_old_posts.start()
        print("✓ Started background task: check_old_posts (runs every 4 hours)")
    
    # Start cleanup task for old solved posts
    if not cleanup_old_solved_posts.is_running():
        cleanup_old_solved_posts.start()
        print("✓ Started background task: cleanup_old_solved_posts (runs daily)")
    
    # Start cleanup task for processed_threads memory leak prevention
    if not cleanup_processed_threads.is_running():
        cleanup_processed_threads.start()
        print("✓ Started background task: cleanup_processed_threads (runs every 6 hours)")
    
    # No local backups - all data in Vercel KV (use /export_data to download anytime)
    
    try:
        # ULTRA-SIMPLE APPROACH: Sync separately to each guild
        guild = discord.Object(id=DISCORD_GUILD_ID)
        friend_guild = discord.Object(id=FRIEND_SERVER_ID)
        
        # 0. Remove /translate from global commands FIRST (before any copying)
        # Try multiple times to ensure it's removed
        for attempt in range(3):
            try:
                bot.tree.remove_command("translate", guild=None)  # Remove from global
                print(f'🗑️ Removed /translate from global commands (attempt {attempt + 1})')
            except Exception as e:
                if attempt == 2:  # Last attempt
                    print(f'   (translate not in global commands or already removed)')
                pass
        
        # 1. Sync ALL commands to main guild
        print(f'🔄 Syncing ALL commands to main guild {DISCORD_GUILD_ID}...')
        bot.tree.copy_global_to(guild=guild)
        
        # Remove translate from main guild AFTER copying (in case it was copied)
        try:
            bot.tree.remove_command("translate", guild=guild)
            print(f'🗑️ Removed /translate from main guild')
        except Exception as e:
            print(f'   (translate not in main guild: {e})')
        
        synced_main = await bot.tree.sync(guild=guild)
        print(f'✓ {len(synced_main)} commands synced to main guild')
        
        # 2. For friend's guild: Explicitly add ONLY /ask command
        print(f'🔄 Setting up friend\'s guild {FRIEND_SERVER_ID}...')
        
        # Clear all commands from friend guild first
        try:
            # Get current commands
            current_commands = bot.tree.get_commands(guild=friend_guild)
            for cmd in current_commands:
                bot.tree.remove_command(cmd.name, guild=friend_guild)
                print(f'   Removed /{cmd.name} from friend guild')
        except Exception as e:
            print(f'   ⚠ Error clearing commands: {e}')
        
        # Copy global commands temporarily to get /ask
        bot.tree.copy_global_to(guild=friend_guild)
        
        # Get all commands and remove everything except /ask (including translate)
        all_commands = bot.tree.get_commands(guild=friend_guild)
        print(f'   Found {len(all_commands)} commands in friend guild')
        
        # Remove everything except /ask (especially translate)
        for cmd in all_commands:
            if cmd.name != "ask":
                try:
                    bot.tree.remove_command(cmd.name, guild=friend_guild)
                    if cmd.name == "translate":
                        print(f'   🗑️ Removed /translate from friend guild')
                    else:
                        print(f'   Removed /{cmd.name} from friend guild')
                except Exception as e:
                    print(f'   ⚠ Could not remove /{cmd.name}: {e}')
        
        # Verify /ask exists
        final_commands = bot.tree.get_commands(guild=friend_guild)
        ask_exists = any(cmd.name == "ask" for cmd in final_commands)
        
        if not ask_exists:
            print(f'   ⚠ /ask not found! Adding it explicitly...')
            # The /ask command should already be registered globally, so copy it
            bot.tree.copy_global_to(guild=friend_guild)
        
        # Now sync only the remaining command(s)
        synced_friend = await bot.tree.sync(guild=friend_guild)
        print(f'✓ {len(synced_friend)} command(s) synced to friend\'s guild: {[c.name for c in synced_friend]}')
        
        if len(synced_friend) == 1 and synced_friend[0].name == "ask":
            print(f'✅ SUCCESS: Only /ask on friend\'s server!')
        else:
            print(f'⚠ Unexpected commands on friend server: {[c.name for c in synced_friend]}')
            print(f'   Make sure /ask command is registered globally')
        
        print(f'\n✅ Command sync complete!')
        print(f'   • Main guild: {len(synced_main)} commands')
        print(f'   • Friend guild: {len(synced_friend)} command(s)')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')
        import traceback
        traceback.print_exc()
    
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

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Global error handler for all slash commands - ensures commands always respond"""
    print(f"❌ Error in slash command '{interaction.command.name if interaction.command else 'unknown'}': {type(error).__name__}: {str(error)}")
    import traceback
    traceback.print_exc()
    
    # Try to respond to the interaction if it hasn't been responded to yet
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ An error occurred: {str(error)[:200]}",
                ephemeral=True
            )
        else:
            # Already responded, try followup
            await interaction.followup.send(
                f"❌ An error occurred: {str(error)[:200]}",
                ephemeral=True
            )
    except discord.errors.InteractionResponded:
        # Already responded, try followup
        try:
            await interaction.followup.send(
                f"❌ An error occurred: {str(error)[:200]}",
                ephemeral=True
            )
        except:
            pass
    except Exception as e:
        print(f"⚠ Failed to send error message to user: {e}")
        # Last resort: try to edit if possible
        try:
            if interaction.response.is_done():
                await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)
        except:
            pass

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
        
        # Get guild ID for Discord URL
        guild_id = thread.guild.id if thread.guild else DISCORD_GUILD_ID
        discord_url = f"https://discord.com/channels/{guild_id}/{thread.id}"
        
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
                'discordUrl': discord_url,  # Direct link to Discord thread
                'conversation': [
                    {
                        'author': 'User',
                        'content': initial_message,
                        'timestamp': datetime.now().isoformat()
                    }
                ]
            }
        }
        
        # Use compression to reduce transfer size
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(forum_api_url, json=post_data, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print(f"✅ Forum post saved to dashboard (persisted to Vercel KV/Redis): '{thread.name}' by {owner_name}")
                else:
                    text = await response.text()
                    print(f"⚠ Failed to save forum post to API: Status {response.status}")
                    print(f"   Response: {text[:200]}")
                    print(f"   API URL: {forum_api_url}")
                    print(f"   Request body: {json.dumps(post_data)[:200]}")
                    print(f"   ⚠️ Forum post will not persist - check API configuration")
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
    
    # Check if we've already fully processed this thread (within last 24 hours)
    if thread.id in processed_threads:
        # Check if entry is old (more than 24 hours)
        entry_time = processed_threads[thread.id]
        if (datetime.now() - entry_time).total_seconds() > 86400:  # 24 hours
            # Remove old entry
            del processed_threads[thread.id]
        else:
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
            processed_threads[thread.id] = datetime.now()
            processing_threads.remove(thread.id)  # Release lock
            return
    except Exception as check_error:
        print(f"⚠ Could not check for existing bot messages: {check_error}")
    
    # Mark as processed to prevent future duplicates (with timestamp for cleanup)
    processed_threads[thread.id] = datetime.now()

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
    
    # Get the initial message from thread history (with retry)
    history = []
    retry_count = 0
    max_retries = 3
    while not history and retry_count < max_retries:
        try:
            history = [message async for message in thread.history(limit=1, oldest_first=True)]
            if not history:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"⚠ No initial message found in thread {thread.id}, retrying ({retry_count}/{max_retries})...")
                    await asyncio.sleep(2)  # Wait longer for Discord to process
                else:
                    print(f"❌ No initial message found in thread {thread.id} after {max_retries} attempts")
                    processing_threads.remove(thread.id)  # Release lock
                    return
        except Exception as history_error:
            retry_count += 1
            print(f"⚠ Error fetching thread history (attempt {retry_count}/{max_retries}): {history_error}")
            if retry_count < max_retries:
                await asyncio.sleep(2)
            else:
                print(f"❌ Failed to fetch thread history after {max_retries} attempts")
                processing_threads.remove(thread.id)  # Release lock
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
    
    # DISABLED: Image processing - skip images to avoid AI connection issues
    image_parts = None
    if has_attachments and "image" in attachment_types:
        print(f"🖼️ User attached {attachment_types.count('image')} image(s) - skipping image analysis (disabled)")
        # image_parts = None  # Don't process images
    
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
        notification_msg = await thread.send(embed=human_escalation_embed)
        # Track this message so we can delete it when classification is done
        support_notification_messages[thread_id] = notification_msg.id
        
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
        
        # Store images for potential escalation
        if image_parts:
            thread_images[thread_id] = image_parts
            print(f"💾 Stored {len(image_parts)} image(s) for thread {thread_id} (for escalation if needed)")
        
            # Add solved button
            solved_view = SolvedButton(thread_id)
            await thread.send(embed=auto_embed, view=solved_view)
            bot_response_text = auto_response
            thread_response_type[thread_id] = 'auto'  # Track that we gave an auto-response
            
            # Classify issue and remove notification if present
            issue_type = classify_issue(user_question)
            await remove_support_notification(thread_id)
            
            # Apply tag to Discord thread based on issue type
            await apply_issue_type_tag(thread, issue_type)
            
            # Update forum post with classification
            if 'your-vercel-app' not in DATA_API_URL:
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
                                    current_post['issueType'] = issue_type
                                    update_payload = {'action': 'update', 'post': current_post}
                                    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                                    async with session.post(forum_api_url, json=update_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as post_response:
                                        if post_response.status == 200:
                                            print(f"✓ Classified issue as: {issue_type}")
                except Exception as e:
                    print(f"⚠ Could not update issue classification: {e}")
            
            print(f"⚡ Responded to '{thread.name}' with instant auto-response.")
    else:
        # PRIORITIZE PINECONE: Use Pinecone vector search first (same as /ask command)
        print(f"🔍 Forum post: Searching RAG database for: '{user_question[:50]}...'")
        relevant_docs = find_relevant_rag_entries(user_question, RAG_DATABASE, top_k=5, similarity_threshold=0.2)
        
        # Log Pinecone results
        if relevant_docs:
            print(f"📊 Forum post: Found {len(relevant_docs)} relevant RAG entries using {'Pinecone' if USE_PINECONE else 'keyword'} search")
            for i, doc in enumerate(relevant_docs[:3], 1):
                print(f"   {i}. '{doc.get('title', 'Unknown')}'")
        else:
            print(f"⚠ Forum post: No RAG entries found via {'Pinecone' if USE_PINECONE else 'keyword'} search")
            # Fallback to keyword matching if Pinecone found nothing
            print(f"🔍 Falling back to keyword-based search...")
            query_words = set(user_question.lower().split())
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'be'}
            query_words = {word for word in query_words if word not in stopwords}
            
            all_scored_entries = []
            for entry in RAG_DATABASE:
                score = 0
                entry_title = entry.get('title', '').lower()
                entry_keywords = ' '.join(entry.get('keywords', [])).lower()
                entry_content = entry.get('content', '').lower()
                
                for word in query_words:
                    if f" {word} " in f" {entry_title} " or entry_title.startswith(word) or entry_title.endswith(word):
                        score += 5
                    elif word in entry_title:
                        score += 3
                    if f" {word} " in f" {entry_keywords} " or entry_keywords.startswith(word) or entry_keywords.endswith(word):
                        score += 4
                    elif word in entry_keywords:
                        score += 2
                    if word in entry_content:
                        score += 1
                
                if score > 0:
                    all_scored_entries.append({'entry': entry, 'score': score})
                    print(f"   ✓ Keyword match: '{entry.get('title', 'Unknown')}' (score: {score})")
            
            all_scored_entries.sort(key=lambda x: x['score'], reverse=True)
            relevant_docs = [item['entry'] for item in all_scored_entries[:5]]
        
        # Use Pinecone results (or keyword fallback) as confident_docs
        confident_docs = relevant_docs

        if confident_docs:
            # Found matches in knowledge base - use top entries
            num_to_use = min(3, len(confident_docs))  # Use up to 3 best matches
            bot_response_text = None
            try:
                bot_response_text = await generate_ai_response(user_question, confident_docs[:num_to_use], image_parts)
                if not bot_response_text or len(bot_response_text.strip()) == 0:
                    # Fallback if response is empty
                    bot_response_text = None  # Will trigger fallback below
                    print(f"⚠️ generate_ai_response returned empty, using fallback")
            except Exception as ai_error:
                print(f"❌ Error generating AI response: {ai_error}")
                import traceback
                traceback.print_exc()
                bot_response_text = None  # Will trigger fallback below
            
            # Ensure we have a response before sending - show RAG content directly if AI failed
            if not bot_response_text or len(bot_response_text.strip()) == 0:
                # Final fallback - show RAG content directly
                top_doc = confident_docs[0]
                doc_title = top_doc.get('title', 'Relevant Entry')
                doc_content = top_doc.get('content', '')
                content_preview = doc_content[:1500] + "..." if len(doc_content) > 1500 else doc_content
                bot_response_text = f"I found information in my knowledge base about **{doc_title}**:\n\n{content_preview}\n\n*Note: I'm having trouble connecting to my AI service right now, but here's the relevant information from my knowledge base.*"
                print(f"⚠️ Using RAG content fallback for '{thread.name}'")
            
            # Send AI response - SHORTER AND SIMPLER
            try:
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
                
                # Store images for potential escalation
                if image_parts:
                    thread_images[thread_id] = image_parts
                    print(f"💾 Stored {len(image_parts)} image(s) for thread {thread_id}")
                
                # Add solved button
                solved_view = SolvedButton(thread_id)
                await thread.send(embed=ai_embed, view=solved_view)
                thread_response_type[thread_id] = 'ai'  # Track that we gave an AI response
                
                # Show which entries were used in terminal
                print(f"✅ Responded to '{thread.name}' with RAG-based answer using {num_to_use} knowledge base {'entry' if num_to_use == 1 else 'entries'}:")
                for i, doc in enumerate(confident_docs[:num_to_use], 1):
                    print(f"   {i}. '{doc.get('title', 'Unknown')}'")
            except Exception as send_error:
                print(f"❌ CRITICAL: Failed to send response embed to thread {thread_id}: {send_error}")
                import traceback
                traceback.print_exc()
                # Last resort: try to send plain text
                try:
                    await thread.send(f"✅ **Solution**\n\n{bot_response_text[:1900]}\n\n*I found this in my knowledge base but had trouble formatting it properly.*")
                    print(f"⚠️ Sent plain text fallback for '{thread.name}'")
                except Exception as final_error:
                    print(f"❌ CRITICAL: Even plain text send failed: {final_error}")
            
            # Classify issue and remove notification if present
            issue_type = classify_issue(user_question)
            await remove_support_notification(thread_id)
            
            # Apply tag to Discord thread based on issue type
            await apply_issue_type_tag(thread, issue_type)
            
            # Update forum post with classification
            if 'your-vercel-app' not in DATA_API_URL:
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
                                    current_post['issueType'] = issue_type
                                    update_payload = {'action': 'update', 'post': current_post}
                                    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                                    async with session.post(forum_api_url, json=update_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as post_response:
                                        if post_response.status == 200:
                                            print(f"✓ Classified issue as: {issue_type}")
                except Exception as e:
                    print(f"⚠ Could not update issue classification: {e}")
        else:
            # No confident match - generate AI response using general Revolution Macro knowledge
            print(f"⚠ No confident RAG match found. Attempting AI response with general knowledge...")
            
            try:
                # Build context from auto-responses to give AI some Revolution Macro knowledge
                auto_response_context = []
                for auto_resp in AUTO_RESPONSES:
                    auto_response_context.append(f"- {auto_resp.get('name', '')}: {auto_resp.get('responseText', '')}")
                
                context_info = "\n".join(auto_response_context) if auto_response_context else "No additional context available."
                
                # Create a simple context entry from auto-responses for generate_ai_response
                general_context_entry = {
                    'title': 'Revolution Macro General Information',
                    'content': (
                        "Revolution Macro is a game automation tool.\n\n"
                        "FEATURES:\n"
                        "- Auto farming/gathering\n"
                        "- Smart navigation\n"
                        "- Auto-deposit\n"
                        "- License system\n\n"
                        f"Additional context:\n{context_info}"
                    ),
                    'keywords': ['revolution', 'macro', 'general', 'help']
                }
                
                # Use generate_ai_response to ensure images are processed correctly
                # Pass image_parts so vision model is used if images are present
                bot_response_text = await generate_ai_response(user_question, [general_context_entry], image_parts)
                
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
                
                # Store images for potential escalation
                if image_parts:
                    thread_images[thread_id] = image_parts
                    print(f"💾 Stored {len(image_parts)} image(s) for thread {thread_id}")
                
                # Add satisfaction buttons (pass images for escalation)
                button_view = SatisfactionButtons(thread_id, conversation, 'ai', image_parts)
                await thread.send(embed=general_ai_embed, view=button_view)
                thread_response_type[thread_id] = 'ai'  # Track that we gave an AI response
                
                # Classify issue and remove notification if present
                issue_type = classify_issue(user_question)
                await remove_support_notification(thread_id)
                # Update forum post with classification
                if 'your-vercel-app' not in DATA_API_URL:
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
                                        current_post['issueType'] = issue_type
                                        update_payload = {'action': 'update', 'post': current_post}
                                        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
                                        async with session.post(forum_api_url, json=update_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as post_response:
                                            if post_response.status == 200:
                                                print(f"✓ Classified issue as: {issue_type}")
                    except Exception as e:
                        print(f"⚠ Could not update issue classification: {e}")
                
                print(f"💡 Responded to '{thread.name}' with Revolution Macro AI assistance (no specific RAG match).")
                
            except Exception as e:
                print(f"⚠ Error generating general AI response: {e}")
                import traceback
                traceback.print_exc()
                # Fallback: shorter message
                bot_response_text = "I couldn't find specific information in my knowledge base for your question, and I'm having trouble connecting to my AI service right now. A human support agent will help you shortly."
                
                try:
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
                    
                    # Store images for potential escalation (even for fallback)
                    if image_parts:
                        thread_images[thread_id] = image_parts
                    
                    # Add satisfaction buttons (pass images for escalation)
                    button_view = SatisfactionButtons(thread_id, conversation, 'ai', image_parts)
                    await thread.send(embed=fallback_embed, view=button_view)
                    thread_response_type[thread_id] = 'ai'  # Track as AI attempt
                    print(f"⚠ Sent fallback response for '{thread.name}' (AI generation failed).")
                except Exception as send_error:
                    print(f"❌ CRITICAL: Failed to send fallback embed to thread {thread_id}: {send_error}")
                    # Last resort: try plain text
                    try:
                        await thread.send(bot_response_text)
                        print(f"⚠️ Sent plain text fallback for '{thread.name}'")
                    except Exception as final_error:
                        print(f"❌ CRITICAL: Even plain text send failed: {final_error}")
    
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
        if 'image_parts' in locals() and image_parts:
            try:
                for img in image_parts:
                    try:
                        img.close()
                    except:
                        pass
                print(f"🗑️ Final cleanup: Released {len(image_parts)} image(s) from memory")
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
                                # Update conversation immediately
                                post_update = {
                                    'action': 'update',
                                    'post': {
                                        **matching_post,
                                        'conversation': conversation,
                                        'status': new_status
                                    }
                                }
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
                                                    
                                                    # Generate AI response (ALWAYS, with or without RAG)
                                                    # Note: on_message handler doesn't have access to original images
                                                    if relevant_docs:
                                                        print(f"📚 Found {len(relevant_docs)} RAG entries for AI response")
                                                        ai_response = await generate_ai_response(user_question, relevant_docs[:2], None)
                                                    else:
                                                        print(f"💭 No RAG entries - AI using general knowledge")
                                                        ai_response = await generate_ai_response(user_question, [], None)
                                                    
                                                    print(f"✅ AI response generated ({len(ai_response)} chars)")
                                                    
                                                    # Send the AI response
                                                    # Truncate description if too long (Discord limit is 4096 characters)
                                                    max_description_length = 4096
                                                    truncated_response = ai_response
                                                    if len(ai_response) > max_description_length:
                                                        truncated_response = ai_response[:max_description_length-3] + "..."
                                                    
                                                    ai_embed = discord.Embed(
                                                        title="💡 Let Me Try Again",
                                                        description=truncated_response,
                                                        color=0x5865F2
                                                    )
                                                    ai_embed.add_field(
                                                        name="💬 Better?",
                                                        value="Let me know by clicking a button below!",
                                                        inline=False
                                                    )
                                                    ai_embed.set_footer(text="Revolution Macro AI")
                                                    
                                                    # Add solved button
                                                    solved_view = SolvedButton(thread_id)
                                                    await thread_channel.send(embed=ai_embed, view=solved_view)
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
        if thread_id in processed_threads:
            del processed_threads[thread_id]
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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

@bot.tree.command(name="purge_forum_posts", description="Delete all forum posts except the main ones (ignored posts) (Admin only).")
async def purge_forum_posts(interaction: discord.Interaction):
    """Purge all forum posts except those in the ignore list"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Skip API call if URL is not configured
        if 'your-vercel-app' in DATA_API_URL:
            await interaction.followup.send("⚠️ Dashboard API not configured. Cannot purge forum posts.", ephemeral=False)
            return
        
        # Get ignored post IDs (these are the "main" posts to keep)
        ignored_post_ids = BOT_SETTINGS.get('ignored_post_ids', [])
        
        # Fetch all forum posts from API
        forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        
        async with aiohttp.ClientSession() as session:
            # Get all posts
            async with session.get(forum_api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as get_resp:
                if get_resp.status != 200:
                    await interaction.followup.send(f"❌ Failed to fetch forum posts from API. Status: {get_resp.status}", ephemeral=False)
                    return
                
                all_posts = await get_resp.json()
                
                if not all_posts or len(all_posts) == 0:
                    await interaction.followup.send("ℹ️ No forum posts found to purge.", ephemeral=False)
                    return
                
                # Filter posts to delete (exclude ignored ones)
                posts_to_delete = []
                posts_to_keep = []
                
                for post in all_posts:
                    post_id = str(post.get('postId', ''))
                    post_id_with_prefix = post.get('id', '')  # Format: POST-123456
                    
                    # Check if this post should be kept (is in ignore list)
                    should_keep = False
                    if post_id in ignored_post_ids:
                        should_keep = True
                    elif post_id_with_prefix.replace('POST-', '') in ignored_post_ids:
                        should_keep = True
                    elif post_id_with_prefix in ignored_post_ids:
                        should_keep = True
                    
                    if should_keep:
                        posts_to_keep.append(post)
                    else:
                        posts_to_delete.append(post)
                
                if len(posts_to_delete) == 0:
                    await interaction.followup.send(
                        f"ℹ️ No posts to delete. All {len(posts_to_keep)} post(s) are in the ignore list (main posts).",
                        ephemeral=False
                    )
                    return
                
                # Delete each post
                deleted_count = 0
                failed_count = 0
                
                for post in posts_to_delete:
                    post_id = post.get('id', post.get('postId', ''))
                    if not post_id:
                        continue
                    
                    try:
                        # Use DELETE method
                        delete_data = {'postId': post_id}
                        async with session.delete(forum_api_url, json=delete_data, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as delete_resp:
                            if delete_resp.status == 200:
                                deleted_count += 1
                            else:
                                # Try POST method with action='delete' as fallback
                                delete_data_post = {'action': 'delete', 'postId': post_id}
                                async with session.post(forum_api_url, json=delete_data_post, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as post_resp:
                                    if post_resp.status == 200:
                                        deleted_count += 1
                                    else:
                                        failed_count += 1
                                        print(f"⚠ Failed to delete post {post_id}: {post_resp.status}")
                    except Exception as delete_error:
                        failed_count += 1
                        print(f"⚠ Error deleting post {post_id}: {delete_error}")
                
                # Create result embed
                result_embed = discord.Embed(
                    title="🗑️ Forum Posts Purge Complete",
                    color=0xFF6B6B if failed_count > 0 else 0x2ECC71
                )
                
                result_embed.add_field(
                    name="📊 Summary",
                    value=(
                        f"**Total posts:** {len(all_posts)}\n"
                        f"**Kept (main posts):** {len(posts_to_keep)}\n"
                        f"**Deleted:** {deleted_count}\n"
                        f"**Failed:** {failed_count}"
                    ),
                    inline=False
                )
                
                if len(posts_to_keep) > 0:
                    kept_list = []
                    for post in posts_to_keep[:10]:  # Show max 10
                        post_title = post.get('postTitle', 'Unknown')[:50]
                        post_id = post.get('postId', post.get('id', 'Unknown'))
                        kept_list.append(f"• {post_title} (ID: {post_id})")
                    
                    if len(posts_to_keep) > 10:
                        kept_list.append(f"... and {len(posts_to_keep) - 10} more")
                    
                    result_embed.add_field(
                        name="✅ Kept Posts (Main Posts)",
                        value="\n".join(kept_list) if kept_list else "None",
                        inline=False
                    )
                
                result_embed.set_footer(text="Revolution Macro Bot")
                
                await interaction.followup.send(embed=result_embed, ephemeral=False)
                print(f"✓ Purged {deleted_count} forum posts (kept {len(posts_to_keep)} main posts) by {interaction.user}")
                
    except Exception as e:
        print(f"Error in purge_forum_posts: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_unsolved_tag_id", description="Set the Discord tag ID for 'Unsolved' posts (Admin only).")
async def set_unsolved_tag_id(interaction: discord.Interaction, tag_id: str):
    """Set the unsolved tag ID"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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

@bot.tree.command(name="list_forum_tags", description="List all available tags in the support forum channel (Admin only).")
async def list_forum_tags(interaction: discord.Interaction):
    """List all available forum tags with their IDs"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        forum_channel_id = BOT_SETTINGS.get('support_forum_channel_id', SUPPORT_FORUM_CHANNEL_ID)
        forum_channel = bot.get_channel(forum_channel_id)
        
        if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
            await interaction.followup.send(f"❌ Forum channel not found or invalid. Channel ID: {forum_channel_id}", ephemeral=True)
            return
        
        available_tags = forum_channel.available_tags
        
        if not available_tags:
            await interaction.followup.send("⚠️ No tags found in the forum channel. Create tags in the channel settings first.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏷️ Available Forum Tags",
            description=f"Tags in **{forum_channel.name}**:",
            color=0x5865F2
        )
        
        tags_text = ""
        for tag in available_tags:
            emoji = tag.emoji if tag.emoji else ""
            tags_text += f"{emoji} **{tag.name}**\n`ID: {tag.id}`\n\n"
        
        embed.add_field(name="Tags", value=tags_text[:1024], inline=False)
        embed.set_footer(text=f"Use /set_tag_id to configure which tag to use for each issue type")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"list_forum_tags command used by {interaction.user}")
        
    except Exception as e:
        print(f"Error in list_forum_tags: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_tag_id", description="Set the Discord tag ID for an issue type (Admin only).")
async def set_tag_id(interaction: discord.Interaction, issue_type: str, tag_id: str):
    """Set the tag ID for a specific issue type"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    # Valid issue types
    valid_issue_types = [
        'Bug/Error', 'Performance', 'Installation/Setup', 'Display/Graphics',
        'Connection/Network', 'Account/Authentication', 'Feature Request',
        'Question/Help', 'Macro/Automation', 'Other'
    ]
    
    if issue_type not in valid_issue_types:
        await interaction.followup.send(
            f"❌ Invalid issue type. Valid types:\n" + "\n".join(f"• {t}" for t in valid_issue_types),
            ephemeral=True
        )
        return
    
    try:
        # Validate tag ID is a number
        tag_id_int = int(tag_id)
        
        # Verify tag exists in forum channel
        forum_channel_id = BOT_SETTINGS.get('support_forum_channel_id', SUPPORT_FORUM_CHANNEL_ID)
        forum_channel = bot.get_channel(forum_channel_id)
        
        if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
            await interaction.followup.send(f"❌ Forum channel not found. Channel ID: {forum_channel_id}", ephemeral=True)
            return
        
        available_tags = forum_channel.available_tags
        tag_found = False
        tag_name = None
        
        for tag in available_tags:
            if tag.id == tag_id_int:
                tag_found = True
                tag_name = tag.name
                break
        
        if not tag_found:
            await interaction.followup.send(
                f"❌ Tag ID {tag_id} not found in forum channel.\n"
                f"Use `/list_forum_tags` to see available tag IDs.",
                ephemeral=True
            )
            return
        
        # Initialize issue_type_tag_ids if it doesn't exist
        if 'issue_type_tag_ids' not in BOT_SETTINGS:
            BOT_SETTINGS['issue_type_tag_ids'] = {}
        
        # Set the tag ID
        BOT_SETTINGS['issue_type_tag_ids'][issue_type] = str(tag_id_int)
        
        # Save to API
        await save_bot_settings_to_api()
        
        embed = discord.Embed(
            title="✅ Tag ID Set",
            description=f"Set tag ID for **{issue_type}** to `{tag_id_int}`",
            color=0x2ECC71
        )
        embed.add_field(name="Tag Name", value=tag_name, inline=True)
        embed.add_field(name="Tag ID", value=str(tag_id_int), inline=True)
        embed.set_footer(text="The bot will now automatically tag posts with this tag when the issue type is detected.")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"set_tag_id command used by {interaction.user}: {issue_type} -> {tag_id_int}")
        
    except ValueError:
        await interaction.followup.send(f"❌ Invalid tag ID. Tag ID must be a number.", ephemeral=True)
    except Exception as e:
        print(f"Error in set_tag_id: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="list_tag_ids", description="List all configured issue type tag IDs (Admin only).")
async def list_tag_ids(interaction: discord.Interaction):
    """List all configured tag IDs for issue types"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        tag_ids = BOT_SETTINGS.get('issue_type_tag_ids', {})
        
        # Check if any tags are configured (issue types or special tags)
        has_special_tags = any([
            BOT_SETTINGS.get('user_issue_tag_id'),
            BOT_SETTINGS.get('bug_tag_id'),
            BOT_SETTINGS.get('crash_tag_id'),
            BOT_SETTINGS.get('rdp_tag_id')
        ])
        
        if not tag_ids and not has_special_tags:
            await interaction.followup.send("⚠️ No tag IDs configured. Use `/set_tag_id`, `/set_user_issue_tag_id`, `/set_bug_tag_id`, etc. to configure tags.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏷️ Configured Tags",
            description="All configured tag IDs:",
            color=0x5865F2
        )
        
        # Get forum channel to show tag names
        forum_channel_id = BOT_SETTINGS.get('support_forum_channel_id', SUPPORT_FORUM_CHANNEL_ID)
        forum_channel = bot.get_channel(forum_channel_id)
        available_tags = {}
        if forum_channel and isinstance(forum_channel, discord.ForumChannel):
            for tag in forum_channel.available_tags:
                available_tags[tag.id] = tag.name
        
        # Build tags text
        tags_text = ""
        
        # Issue type tags
        if tag_ids:
            tags_text += "**Auto-Classified Issue Types:**\n"
            for issue_type, tag_id_str in tag_ids.items():
                tag_id_int = int(tag_id_str)
                tag_name = available_tags.get(tag_id_int, "Unknown")
                tags_text += f"• **{issue_type}**: `{tag_id_str}` ({tag_name})\n"
            tags_text += "\n"
        
        # Special tags
        special_tags = []
        if BOT_SETTINGS.get('user_issue_tag_id'):
            special_tags.append(("User Issue", BOT_SETTINGS['user_issue_tag_id']))
        if BOT_SETTINGS.get('bug_tag_id'):
            special_tags.append(("Bug", BOT_SETTINGS['bug_tag_id']))
        if BOT_SETTINGS.get('crash_tag_id'):
            special_tags.append(("Crash", BOT_SETTINGS['crash_tag_id']))
        if BOT_SETTINGS.get('rdp_tag_id'):
            special_tags.append(("RDP", BOT_SETTINGS['rdp_tag_id']))
        
        if special_tags:
            tags_text += "**Special Tags:**\n"
            for tag_name, tag_id_str in special_tags:
                tag_id_int = int(tag_id_str)
                discord_tag_name = available_tags.get(tag_id_int, "Unknown")
                tags_text += f"• **{tag_name}**: `{tag_id_str}` ({discord_tag_name})\n"
        
        if not tags_text:
            tags_text = "No tags configured."
        
        embed.add_field(name="Configured Tags", value=tags_text[:1024] or "None", inline=False)
        embed.set_footer(text="Use /set_tag_id, /set_user_issue_tag_id, /set_bug_tag_id, etc. to configure tags")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"list_tag_ids command used by {interaction.user}")
        
    except Exception as e:
        print(f"Error in list_tag_ids: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="clear_tag_id", description="Clear the tag ID for an issue type (Admin only).")
async def clear_tag_id(interaction: discord.Interaction, issue_type: str):
    """Clear the tag ID for a specific issue type"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    tag_ids = BOT_SETTINGS.get('issue_type_tag_ids', {})
    
    if issue_type not in tag_ids:
        await interaction.followup.send(f"❌ No tag ID configured for '{issue_type}'.", ephemeral=True)
        return
    
    # Remove the tag ID
    del tag_ids[issue_type]
    BOT_SETTINGS['issue_type_tag_ids'] = tag_ids
    
    # Save to API
    await save_bot_settings_to_api()
    
    await interaction.followup.send(f"✅ Cleared tag ID for **{issue_type}**. The bot will no longer tag posts with this issue type.", ephemeral=True)
    print(f"clear_tag_id command used by {interaction.user}: {issue_type}")

@bot.tree.command(name="set_user_issue_tag_id", description="Set the Discord tag ID for user-reported issues (Admin only).")
async def set_user_issue_tag_id(interaction: discord.Interaction, tag_id: str):
    """Set the tag ID for user-reported issues"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        tag_id_int = int(tag_id)
        
        # Verify tag exists
        forum_channel_id = BOT_SETTINGS.get('support_forum_channel_id', SUPPORT_FORUM_CHANNEL_ID)
        forum_channel = bot.get_channel(forum_channel_id)
        
        if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
            await interaction.followup.send(f"❌ Forum channel not found. Channel ID: {forum_channel_id}", ephemeral=True)
            return
        
        available_tags = forum_channel.available_tags
        tag_found = False
        tag_name = None
        
        for tag in available_tags:
            if tag.id == tag_id_int:
                tag_found = True
                tag_name = tag.name
                break
        
        if not tag_found:
            await interaction.followup.send(
                f"❌ Tag ID {tag_id} not found in forum channel.\n"
                f"Use `/list_forum_tags` to see available tag IDs.",
                ephemeral=True
            )
            return
        
        BOT_SETTINGS['user_issue_tag_id'] = str(tag_id_int)
        await save_bot_settings_to_api()
        
        embed = discord.Embed(
            title="✅ User Issue Tag ID Set",
            description=f"Set tag ID for user-reported issues to `{tag_id_int}`",
            color=0x2ECC71
        )
        embed.add_field(name="Tag Name", value=tag_name, inline=True)
        embed.add_field(name="Tag ID", value=str(tag_id_int), inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"set_user_issue_tag_id command used by {interaction.user}: {tag_id_int}")
        
    except ValueError:
        await interaction.followup.send(f"❌ Invalid tag ID. Tag ID must be a number.", ephemeral=True)
    except Exception as e:
        print(f"Error in set_user_issue_tag_id: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_bug_tag_id", description="Set the Discord tag ID for bug reports (Admin only).")
async def set_bug_tag_id(interaction: discord.Interaction, tag_id: str):
    """Set the tag ID for bug reports"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        tag_id_int = int(tag_id)
        
        # Verify tag exists
        forum_channel_id = BOT_SETTINGS.get('support_forum_channel_id', SUPPORT_FORUM_CHANNEL_ID)
        forum_channel = bot.get_channel(forum_channel_id)
        
        if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
            await interaction.followup.send(f"❌ Forum channel not found. Channel ID: {forum_channel_id}", ephemeral=True)
            return
        
        available_tags = forum_channel.available_tags
        tag_found = False
        tag_name = None
        
        for tag in available_tags:
            if tag.id == tag_id_int:
                tag_found = True
                tag_name = tag.name
                break
        
        if not tag_found:
            await interaction.followup.send(
                f"❌ Tag ID {tag_id} not found in forum channel.\n"
                f"Use `/list_forum_tags` to see available tag IDs.",
                ephemeral=True
            )
            return
        
        BOT_SETTINGS['bug_tag_id'] = str(tag_id_int)
        await save_bot_settings_to_api()
        
        embed = discord.Embed(
            title="✅ Bug Tag ID Set",
            description=f"Set tag ID for bug reports to `{tag_id_int}`",
            color=0x2ECC71
        )
        embed.add_field(name="Tag Name", value=tag_name, inline=True)
        embed.add_field(name="Tag ID", value=str(tag_id_int), inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"set_bug_tag_id command used by {interaction.user}: {tag_id_int}")
        
    except ValueError:
        await interaction.followup.send(f"❌ Invalid tag ID. Tag ID must be a number.", ephemeral=True)
    except Exception as e:
        print(f"Error in set_bug_tag_id: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_crash_tag_id", description="Set the Discord tag ID for crash reports (Admin only).")
async def set_crash_tag_id(interaction: discord.Interaction, tag_id: str):
    """Set the tag ID for crash reports"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        tag_id_int = int(tag_id)
        
        # Verify tag exists
        forum_channel_id = BOT_SETTINGS.get('support_forum_channel_id', SUPPORT_FORUM_CHANNEL_ID)
        forum_channel = bot.get_channel(forum_channel_id)
        
        if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
            await interaction.followup.send(f"❌ Forum channel not found. Channel ID: {forum_channel_id}", ephemeral=True)
            return
        
        available_tags = forum_channel.available_tags
        tag_found = False
        tag_name = None
        
        for tag in available_tags:
            if tag.id == tag_id_int:
                tag_found = True
                tag_name = tag.name
                break
        
        if not tag_found:
            await interaction.followup.send(
                f"❌ Tag ID {tag_id} not found in forum channel.\n"
                f"Use `/list_forum_tags` to see available tag IDs.",
                ephemeral=True
            )
            return
        
        BOT_SETTINGS['crash_tag_id'] = str(tag_id_int)
        await save_bot_settings_to_api()
        
        embed = discord.Embed(
            title="✅ Crash Tag ID Set",
            description=f"Set tag ID for crash reports to `{tag_id_int}`",
            color=0x2ECC71
        )
        embed.add_field(name="Tag Name", value=tag_name, inline=True)
        embed.add_field(name="Tag ID", value=str(tag_id_int), inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"set_crash_tag_id command used by {interaction.user}: {tag_id_int}")
        
    except ValueError:
        await interaction.followup.send(f"❌ Invalid tag ID. Tag ID must be a number.", ephemeral=True)
    except Exception as e:
        print(f"Error in set_crash_tag_id: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_rdp_tag_id", description="Set the Discord tag ID for RDP issues (Admin only).")
async def set_rdp_tag_id(interaction: discord.Interaction, tag_id: str):
    """Set the tag ID for RDP issues"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        tag_id_int = int(tag_id)
        
        # Verify tag exists
        forum_channel_id = BOT_SETTINGS.get('support_forum_channel_id', SUPPORT_FORUM_CHANNEL_ID)
        forum_channel = bot.get_channel(forum_channel_id)
        
        if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
            await interaction.followup.send(f"❌ Forum channel not found. Channel ID: {forum_channel_id}", ephemeral=True)
            return
        
        available_tags = forum_channel.available_tags
        tag_found = False
        tag_name = None
        
        for tag in available_tags:
            if tag.id == tag_id_int:
                tag_found = True
                tag_name = tag.name
                break
        
        if not tag_found:
            await interaction.followup.send(
                f"❌ Tag ID {tag_id} not found in forum channel.\n"
                f"Use `/list_forum_tags` to see available tag IDs.",
                ephemeral=True
            )
            return
        
        BOT_SETTINGS['rdp_tag_id'] = str(tag_id_int)
        await save_bot_settings_to_api()
        
        embed = discord.Embed(
            title="✅ RDP Tag ID Set",
            description=f"Set tag ID for RDP issues to `{tag_id_int}`",
            color=0x2ECC71
        )
        embed.add_field(name="Tag Name", value=tag_name, inline=True)
        embed.add_field(name="Tag ID", value=str(tag_id_int), inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"set_rdp_tag_id command used by {interaction.user}: {tag_id_int}")
        
    except ValueError:
        await interaction.followup.send(f"❌ Invalid tag ID. Tag ID must be a number.", ephemeral=True)
    except Exception as e:
        print(f"Error in set_rdp_tag_id: {e}")
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_satisfaction_delay", description="Set the delay (in seconds) before analyzing user satisfaction (Admin only).")
async def set_satisfaction_delay(interaction: discord.Interaction, seconds: int):
    """Set the satisfaction analysis delay"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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

@bot.tree.command(name="list_high_priority_posts", description="Show paginated list of all high priority posts with navigation (Admin only).")
async def list_high_priority_posts(interaction: discord.Interaction):
    """List all posts currently marked as High Priority with pagination"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        if 'your-vercel-app' in DATA_API_URL:
            await interaction.followup.send("⚠️ API not configured. Cannot fetch high priority posts.", ephemeral=False)
            return
        
        forum_api_url = DATA_API_URL.replace('/api/data', '/api/forum-posts')
        
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
                
                # Sort by recency/activity (most recent first)
                # Use updatedAt if available, otherwise use createdAt
                def get_sort_key(post):
                    updated_at = post.get('updatedAt') or post.get('createdAt', '')
                    if updated_at:
                        try:
                            # Try ISO format first (most common)
                            if 'T' in updated_at:
                                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            else:
                                # Fallback to strptime
                                dt = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                            return dt.timestamp()
                        except:
                            try:
                                # Try common formats
                                for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S']:
                                    try:
                                        dt = datetime.strptime(updated_at, fmt)
                                        return dt.timestamp()
                                    except:
                                        continue
                            except:
                                pass
                    # If parsing fails, put at end (oldest)
                    return 0
                
                high_priority_posts.sort(key=get_sort_key, reverse=True)
                
                # Create paginated view
                view = HighPriorityPostsView(high_priority_posts, page_size=10)
                embed = view.create_embed(interaction.guild_id)
                
                await interaction.followup.send(embed=embed, view=view, ephemeral=False)
                print(f"✓ High priority posts list shown by {interaction.user} ({len(high_priority_posts)} posts)")
                
    except Exception as e:
        print(f"Error in list_high_priority_posts: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="ping_high_priority_now", description="Manually send high priority summary to notification channel (Admin only).")
async def ping_high_priority_now(interaction: discord.Interaction):
    """Manually trigger a high priority posts summary notification"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Send the summary (no ping for manual command - just viewing)
        await notify_support_channel_summary(ping_support=False)
        
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
                f"📊 **Current rate**: {sum(len(calls) for calls in gemini_api_calls_by_key.values())} calls across {len(GEMINI_API_KEYS)} key(s)",
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
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
        
        # Calculate total API calls across all keys
        total_calls = sum(len(calls) for calls in gemini_api_calls_by_key.values())
        usage_stats = gemini_key_manager.get_usage_stats()
        
        # Enhanced key statistics with health tracking
        key_stats_text = f"**{len(gemini_key_manager.api_keys)}** keys loaded\n"
        key_stats_text += f"**{total_calls}** calls (last min)\n\n"
        
        # Show detailed stats for each key
        for key_short, stats in list(usage_stats.items())[:4]:  # Show first 4 keys
            calls_for_key = len(gemini_api_calls_by_key.get(key_short, deque()))
            success_rate = stats.get('success_rate', 0)
            health = stats.get('health_score', 0)
            is_rate_limited = stats.get('rate_limited', False)
            total_calls = stats.get('total_calls', 0)
            errors = stats.get('errors', 0)
            success_calls = stats.get('successful_calls', 0)
            
            # Determine status indicator based on health score, errors, and rate limit status
            # Check for high error rate first (even if health score is high due to low total calls)
            error_rate = (errors / total_calls * 100) if total_calls > 0 else 0
            
            if is_rate_limited:
                status_icon = "🔴"  # Red for rate limited
            elif total_calls > 0 and error_rate > 50:
                status_icon = "🔴"  # Red for high error rate (>50% errors)
            elif total_calls > 0 and errors > success_calls:
                status_icon = "🔴"  # Red if more errors than successes
            elif health > 50 and error_rate < 20:
                status_icon = "🟢"  # Green for good health and low error rate
            elif health > 0 and error_rate < 40:
                status_icon = "🟡"  # Yellow for warning
            elif health > 0:
                status_icon = "🟡"  # Yellow for moderate health
            else:
                status_icon = "🔴"  # Red for poor health
            
            # Show error count if there are errors
            error_info = f", {errors} errors" if errors > 0 else ""
            key_stats_text += f"{status_icon} {key_short}:\n"
            key_stats_text += f"  {calls_for_key}/10 calls, {success_rate:.0f}% success{error_info}\n"
            key_stats_text += f"  Health: {health:.0f}\n"
        
        if len(usage_stats) > 4:
            key_stats_text += f"\n... {len(usage_stats) - 4} more key(s)"
        
        status_embed.add_field(
            name="🔥 Gemini API Keys",
            value=key_stats_text,
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
        
        # API keys info
        keys_info = f"**Total Keys:** {len(GEMINI_API_KEYS)}\n"
        usage_stats = gemini_key_manager.get_usage_stats()
        for i, key in enumerate(GEMINI_API_KEYS, 1):
            key_short = key[:10] + '...'
            usage = usage_stats.get(key_short, 0)
            current_indicator = " (current)" if i - 1 == gemini_key_manager.current_key_index else ""
            keys_info += f"**Key {i}:** {key_short} - {usage} calls{current_indicator}\n"
        
        api_embed.add_field(
            name="🔑 Gemini API Keys",
            value=keys_info,
            inline=False
        )
        
        api_embed.add_field(
            name="🤖 Bot Token",
            value=f"**DISCORD_BOT_TOKEN:** {'✅ Set' if DISCORD_BOT_TOKEN else '❌ Missing'}",
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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

@bot.tree.command(name="test_api_keys", description="Test all API keys to see which ones work (Admin only).")
async def test_api_keys(interaction: discord.Interaction):
    """Test all API keys and report which ones work"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    working_keys = []
    failed_keys = []
    
    embed = discord.Embed(
        title="🔍 Testing API Keys",
        description=f"Testing {len(GEMINI_API_KEYS)} key(s)...",
        color=discord.Color.blue()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    for i, test_key in enumerate(GEMINI_API_KEYS, 1):
        key_short = test_key[:15] + '...' if len(test_key) > 15 else test_key
        key_name = f"GEMINI_API_KEY" if i == 1 else f"GEMINI_API_KEY_{i}"
        
        # Try multiple models to find one that works
        models_to_try = [
            'gemini-2.5-flash',  # Current model (replaced 1.5-flash)
            'gemini-2.5-pro',   # Advanced model
            'gemini-2.5-flash-lite',  # Cost-effective variant
            'gemini-pro',  # Legacy fallback
            'gemini-flash-latest',  # Legacy fallback
            'gemini-pro-latest'  # Legacy fallback
        ]
        model_worked = False
        working_model = None
        
        for model_name in models_to_try:
            try:
                genai.configure(api_key=test_key)
                test_model = genai.GenerativeModel(model_name)
                test_response = test_model.generate_content("Say hello")
                
                if test_response and hasattr(test_response, 'text') and test_response.text:
                    working_keys.append((i, key_name, key_short, model_name))
                    model_worked = True
                    working_model = model_name
                    break
            except Exception as e:
                error_str = str(e).lower()
                error_msg = str(e)[:200]
                
                if 'not found' in error_str or '404' in error_str:
                    # Model not available, try next one
                    continue
                elif 'api key' in error_str or 'auth' in error_str or '403' in error_str or 'leaked' in error_str or 'permission denied' in error_str:
                    # Key is invalid, don't try other models
                    failed_keys.append((i, key_name, key_short, f"Invalid/Leaked: {error_msg}"))
                    break
                elif 'quota' in error_str or 'rate limit' in error_str or '429' in error_str:
                    # Rate limited but key works
                    working_keys.append((i, key_name, key_short, f"{model_name} (rate limited)"))
                    model_worked = True
                    break
                else:
                    # Other error, try next model
                    continue
        
        if not model_worked:
            failed_keys.append((i, key_name, key_short, "No models available"))
    
    # Build result embed
    result_embed = discord.Embed(
        title="✅ API Key Test Results",
        color=discord.Color.green() if working_keys else discord.Color.red()
    )
    
    if working_keys:
        working_text = "\n".join([f"✅ {idx}. {name} ({short})\n   Model: {model}" for idx, name, short, model in working_keys])
        result_embed.add_field(name=f"Working Keys ({len(working_keys)})", value=working_text[:1024], inline=False)
    
    if failed_keys:
        failed_text = "\n".join([f"❌ {idx}. {name} ({short})\n   {reason[:80]}" for idx, name, short, reason in failed_keys[:10]])
        if len(failed_keys) > 10:
            failed_text += f"\n... and {len(failed_keys) - 10} more"
        result_embed.add_field(name=f"Failed Keys ({len(failed_keys)})", value=failed_text[:1024], inline=False)
    
    result_embed.set_footer(text=f"Total: {len(working_keys)} working, {len(failed_keys)} failed out of {len(GEMINI_API_KEYS)} keys")
    
    await interaction.followup.send(embed=result_embed, ephemeral=True)

@bot.tree.command(name="check_api_keys", description="Show detailed API key usage and health statistics (Admin only).")
async def check_api_keys(interaction: discord.Interaction):
    """Show detailed API key statistics"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    
    try:
        usage_stats = gemini_key_manager.get_usage_stats()
        total_keys = len(gemini_key_manager.api_keys)
        current_key = gemini_key_manager.get_current_key()
        
        key_embed = discord.Embed(
            title="🔑 API Key Statistics",
            description=f"**{total_keys}** keys loaded | Current: `{current_key[:20]}...`",
            color=0x5865F2
        )
        
        # Show stats for each key
        for i, (key_short, stats) in enumerate(usage_stats.items(), 1):
            total_calls = stats.get('total_calls', 0)
            success_calls = stats.get('successful_calls', 0)
            errors = stats.get('errors', 0)
            success_rate = stats.get('success_rate', 0)
            health_score = stats.get('health_score', 0)
            is_rate_limited = stats.get('rate_limited', False)
            
            # Get recent calls from rate limit tracker
            recent_calls = len(gemini_api_calls_by_key.get(key_short, deque()))
            
            # Determine status based on health score and rate limit
            if is_rate_limited:
                status_text = "🔴 RATE LIMITED"
                status_icon = "🔴"
            elif health_score > 50:
                status_text = "🟢 Active (Healthy)"
                status_icon = "✅"
            elif health_score > 0:
                status_text = "🟡 Active (Warning)"
                status_icon = "⚠️"
            else:
                status_text = "🔴 Active (Poor Health)"
                status_icon = "❌"
            
            key_embed.add_field(
                name=f"{status_icon} Key {i}: {key_short}",
                value=(
                    f"**Status:** {status_text}\n"
                    f"**Total Calls:** {total_calls} ({recent_calls} in last min)\n"
                    f"**Success Rate:** {success_rate:.1f}% ({success_calls} success, {errors} errors)\n"
                    f"**Health Score:** {health_score:.0f}"
                ),
                inline=True
            )
        
        # Add warning if all keys are from same account
        if total_keys > 1:
            key_embed.add_field(
                name="⚠️ Important Note",
                value=(
                    "If all keys are from the **same Google account**, they share the same quota/rate limits.\n"
                    "For true load distribution, use keys from **different Google accounts**."
                ),
                inline=False
            )
        
        await interaction.followup.send(embed=key_embed, ephemeral=False)
        print(f"check_api_keys command used by {interaction.user}")
        
    except Exception as e:
        print(f"Error in check_api_keys: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=False)

@bot.tree.command(name="check_auto_entries", description="List all loaded auto-responses (Admin only).")
async def check_auto_entries(interaction: discord.Interaction):
    """Show all auto-responses"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message("❌ You need Administrator permission or Bot Permissions role to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    
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

def is_friend_server(interaction: discord.Interaction) -> bool:
    """Check if the command is being used in the friend's server (where only /ask is allowed)"""
    if not interaction.guild:
        return False
    return interaction.guild.id == FRIEND_SERVER_ID

@bot.tree.command(name="ask", description="Ask the bot a question using the RAG knowledge base.")
async def ask(interaction: discord.Interaction, question: str):
    """Query the RAG knowledge base - available to everyone on friends server, staff only on main server"""
    try:
        # On friend's server, allow everyone to use /ask but with 10 minute cooldown
        # On other servers, require staff role or admin (no cooldown)
        if is_friend_server(interaction):
            # Check cooldown for friends server BEFORE deferring
            user_id = interaction.user.id
            current_time = datetime.now().timestamp()
            if user_id in ask_cooldowns:
                time_since_last_use = current_time - ask_cooldowns[user_id]
                cooldown_seconds = 600  # 10 minute cooldown
                if time_since_last_use < cooldown_seconds:
                    remaining = int(cooldown_seconds - time_since_last_use)
                    remaining_minutes = remaining // 60
                    remaining_secs = remaining % 60
                    if remaining_minutes > 0:
                        await interaction.response.send_message(
                            f"⏳ Please wait {remaining_minutes} minute(s) and {remaining_secs} second(s) before using /ask again.",
                            ephemeral=True
                        )
                    else:
                        await interaction.response.send_message(
                            f"⏳ Please wait {remaining} second(s) before using /ask again.",
                            ephemeral=True
                        )
                    return
            # Update cooldown
            ask_cooldowns[user_id] = current_time
            # Defer after cooldown check passes
            await interaction.response.defer(ephemeral=False)
        else:
            # Main server: require staff role - check BEFORE deferring
            if not has_staff_role(interaction):
                await interaction.response.send_message("❌ You need the Staff role or Administrator permission to use this command.", ephemeral=True)
                return
            # Defer after permission check passes
            await interaction.response.defer(ephemeral=False)
    except discord.errors.InteractionResponded:
        # Already responded (cooldown or permission error)
        return
    except Exception as e:
        print(f"⚠ Error in /ask command setup: {e}")
        try:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)
        except:
            pass
        return
    
    try:
        # Step 1: Check auto-responses first
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
        
        # Step 2: No auto-response found - use RAG knowledgebase with Pinecone (same as forum posts)
        # Use the same find_relevant_rag_entries function that prioritizes Pinecone
        print(f"🔍 /ask: Searching RAG database for: '{question[:50]}...'")
        relevant_docs = find_relevant_rag_entries(question, RAG_DATABASE, top_k=5, similarity_threshold=0.2)
        
        # Log for debugging
        if relevant_docs:
            print(f"📊 /ask: Found {len(relevant_docs)} relevant RAG entries using {'Pinecone' if USE_PINECONE else 'keyword'} search")
            for i, doc in enumerate(relevant_docs[:3], 1):
                print(f"   {i}. '{doc.get('title', 'Unknown')}'")
        else:
            print(f"⚠ /ask: No RAG entries found for query: '{question[:50]}...'")
        
        # Step 3: Generate AI response using RAG knowledgebase if available
        # Use top 2 RAG entries if we have matches
        rag_context = relevant_docs[:2] if relevant_docs else []
        
        # Generate AI response (/ask command doesn't have access to images)
        try:
            ai_response = await generate_ai_response(question, rag_context, None)
            if not ai_response or len(ai_response.strip()) == 0:
                raise Exception("Empty response from AI")
        except Exception as ai_error:
            print(f"⚠️ /ask: AI generation failed: {ai_error}")
            # If we have RAG matches, show them directly as fallback
            if relevant_docs:
                top_doc = relevant_docs[0]
                doc_title = top_doc.get('title', 'Relevant Entry')
                doc_content = top_doc.get('content', '')
                content_preview = doc_content[:1500] + "..." if len(doc_content) > 1500 else doc_content
                ai_response = f"I found information in my knowledge base about **{doc_title}**:\n\n{content_preview}\n\n*Note: I'm having trouble connecting to my AI service right now, but here's the relevant information from my knowledge base.*"
            else:
                ai_response = "I couldn't find any relevant information in my knowledge base for your question, and I'm having trouble connecting to my AI service right now. A human support agent will help you shortly."
        
        # Truncate description if too long (Discord limit is 4096 characters)
        max_description_length = 4096
        truncated_response = ai_response[:max_description_length] if len(ai_response) > max_description_length else ai_response
        if len(ai_response) > max_description_length:
            truncated_response = truncated_response[:max_description_length-3] + "..."
        
        embed = discord.Embed(
            title="✅ AI Response",
            description=truncated_response,
            color=0x2ECC71
        )
        
        # Add knowledge base references if we have them
        if relevant_docs:
            doc_titles = [doc.get('title', 'Unknown') for doc in relevant_docs[:2]]
            embed.add_field(
                name="📚 Knowledge Base References",
                value="\n".join([f"• {title}" for title in doc_titles]),
                inline=False
            )
            embed.set_footer(text=f"Based on {len(relevant_docs)} knowledge base entries • {'Pinecone' if USE_PINECONE else 'Keyword'} search")
        else:
            embed.set_footer(text="AI-generated response (no RAG matches found)")
        
        await interaction.followup.send(embed=embed, ephemeral=False)
            
    except Exception as e:
        print(f"Error in /ask command: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=False)

@bot.tree.command(name="mark_as_solved", description="Mark thread as solved and lock it WITHOUT creating a RAG entry (Staff only).")
async def mark_as_solved(interaction: discord.Interaction):
    """Mark thread as solved and lock it without creating RAG entry"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
        print(f"🚫 Thread {thread_id} marked as solved (no review) - will not create RAG entry")
        
        # Cancel any pending satisfaction timer for this thread
        if thread_id in satisfaction_timers:
            satisfaction_timers[thread_id].cancel()
            del satisfaction_timers[thread_id]
            print(f"⏰ Cancelled satisfaction timer for solved thread {thread_id}")
        
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
            print(f"🔒 Thread {thread_id} locked and archived (manual /mark_as_solved)")
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
        
        # Increment leaderboard for staff member
        await increment_leaderboard(interaction.user)
        
        # Send success message
        await interaction.followup.send(
            f"✅ Thread marked as **Solved** and locked!\n\n"
            f"🔒 Thread is now closed.\n"
            f"📋 No RAG entry created (as requested).\n"
            f"🏆 +1 to your leaderboard score!",
            ephemeral=False
        )
        print(f"✓ Thread {thread_id} marked as solved (no RAG) by {interaction.user}")
        
    except Exception as e:
        print(f"Error in mark_as_solved: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="mark_as_solved_with_review", description="Mark thread as solved and send conversation to analyzer (Staff only).")
async def mark_as_solved_with_review(interaction: discord.Interaction):
    """Mark a thread as solved and analyze the conversation for RAG entry creation"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
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
                                'source': f'Staff ({interaction.user.name}) via /mark_as_solved_with_review',
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
            
                                    # Increment leaderboard for staff member
                                    await increment_leaderboard(interaction.user)
                                    
                                    # Send success message to user
                                    await interaction.followup.send(
                                        f"✅ Thread marked as solved and RAG entry submitted for review!\n\n"
                                        f"**Title:** {new_pending_entry['title']}\n"
                                        f"**ID:** {new_pending_entry['id']}\n\n"
                                        f"📋 The entry is now **pending review** in the **RAG Management** tab.\n"
                                        f"You can approve or reject it from the dashboard.\n"
                                        f"🏆 +1 to your leaderboard score!",
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
                print(f"🔒 Thread {thread.id} locked and archived (manual /mark_as_solved_with_review)")
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
        print(f"Error in mark_as_solved_with_review command: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="search", description="Search for solved support forum posts containing your search term (Staff only).")
@app_commands.describe(query="The search term to look for in solved forum posts")
async def search(interaction: discord.Interaction, query: str):
    """Search for solved forum posts containing a search term"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    
    # Check if user has staff role or admin
    if not has_staff_role(interaction):
        await interaction.response.send_message("❌ You need the Staff role or Administrator permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Get the support forum channel
        forum_channel = bot.get_channel(SUPPORT_FORUM_CHANNEL_ID)
        if not forum_channel:
            await interaction.followup.send("❌ Support forum channel not configured.", ephemeral=True)
            return
        
        # Search through archived threads (solved posts are typically archived)
        # Use fuzzy matching - split query into words and match any of them
        query_words = query.lower().split()
        # Remove very common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'be', 'how', 'what', 'why', 'when', 'where'}
        query_words = [w for w in query_words if w not in stopwords and len(w) > 2]  # Only words longer than 2 chars
        
        matching_threads = []
        thread_scores = {}  # Track relevance scores
        
        # Get the Resolved tag to identify solved posts
        resolved_tag = await get_resolved_tag(forum_channel)
        
        # Search through threads
        async for thread in forum_channel.archived_threads(limit=100):
            # Check if thread has resolved tag
            is_solved = resolved_tag and resolved_tag in thread.applied_tags
            
            if is_solved:
                score = 0
                thread_name_lower = thread.name.lower()
                
                # Score based on how many query words match
                for word in query_words:
                    if word in thread_name_lower:
                        score += 10  # Title matches are worth more
                
                # Also search through messages for better matching
                try:
                    message_matches = 0
                    async for message in thread.history(limit=50):
                        message_lower = message.content.lower()
                        for word in query_words:
                            if word in message_lower:
                                message_matches += 1
                                score += 1  # Message matches worth less
                    if message_matches > 0 and score == 0:
                        # If we found matches in messages but not title, still include it
                        score = message_matches
                except:
                    pass  # Skip if we can't access thread messages
                
                # Include thread if any words matched (score > 0)
                if score > 0:
                    matching_threads.append((thread, score))
            
            # Limit results
            if len(matching_threads) >= 20:  # Get more candidates for sorting
                break
        
        # Sort by score (highest first) and take top 10
        matching_threads.sort(key=lambda x: x[1], reverse=True)
        matching_threads = matching_threads[:10]
        
        if not matching_threads:
            await interaction.followup.send(
                f"🔍 No solved forum posts found containing: **{query}**\n\n"
                f"Try using different keywords or check if the posts are actually marked as solved.",
                ephemeral=False
            )
            return
        
        # Build response with results
        embed = discord.Embed(
            title=f"🔍 Search Results: \"{query}\"",
            description=f"Found {len(matching_threads)} solved post(s) matching your search:",
            color=discord.Color.green()
        )
        
        for thread, score in matching_threads:
            embed.add_field(
                name=f"📌 {thread.name}",
                value=f"[View Thread](https://discord.com/channels/{interaction.guild_id}/{thread.id})",
                inline=False
            )
        
        if len(matching_threads) >= 10:
            embed.set_footer(text="Showing top 10 results. Try more specific keywords for better matches.")
        
        await interaction.followup.send(embed=embed, ephemeral=False)
        print(f"🔍 Search completed for '{query}' by {interaction.user} - found {len(matching_threads)} results")
        
    except Exception as e:
        print(f"Error in search command: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ An error occurred while searching: {str(e)}", ephemeral=True)

@bot.tree.command(name="leaderboard", description="View the monthly support staff leaderboard (Staff only).")
async def leaderboard(interaction: discord.Interaction):
    """Display the monthly leaderboard of staff members who solved threads"""
    if is_friend_server(interaction):
        await interaction.response.send_message("❌ This command is not available on this server. Only /ask is available.", ephemeral=True)
        return
    
    # Check if user has staff role or admin
    if not has_staff_role(interaction):
        await interaction.response.send_message("❌ You need the Staff role or Administrator permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=False)
    
    try:
        from datetime import datetime
        
        current_month = datetime.now().strftime("%Y-%m")
        month_name = datetime.now().strftime("%B %Y")
        
        # Check if we need to reset for new month
        if LEADERBOARD_DATA['month'] != current_month:
            LEADERBOARD_DATA['month'] = current_month
            LEADERBOARD_DATA['scores'] = {}
            await save_leaderboard_to_api()
        
        scores = LEADERBOARD_DATA['scores']
        
        if not scores:
            await interaction.followup.send(
                f"📊 **Support Staff Leaderboard - {month_name}**\n\n"
                f"No solved threads yet this month! Be the first to help someone! 🚀",
                ephemeral=False
            )
            return
        
        # Sort by solved_count (descending)
        sorted_staff = sorted(scores.items(), key=lambda x: x[1]['solved_count'], reverse=True)
        
        # Create embed
        embed = discord.Embed(
            title=f"🏆 Support Staff Leaderboard",
            description=f"**{month_name}** - Top support heroes this month!",
            color=discord.Color.gold()
        )
        
        # Add top 10 staff members
        medals = ["🥇", "🥈", "🥉"]
        for i, (user_id, data) in enumerate(sorted_staff[:10], 1):
            medal = medals[i-1] if i <= 3 else f"**#{i}**"
            username = data.get('username', 'Unknown')
            solved_count = data.get('solved_count', 0)
            
            # Try to get the actual user for mention
            try:
                user = await bot.fetch_user(int(user_id))
                user_mention = user.mention
            except:
                user_mention = username
            
            embed.add_field(
                name=f"{medal} {username}",
                value=f"{user_mention} • **{solved_count}** solved thread{'s' if solved_count != 1 else ''}",
                inline=False
            )
        
        # Add footer with total stats
        total_solved = sum(data['solved_count'] for data in scores.values())
        total_staff = len(scores)
        
        embed.set_footer(text=f"Total: {total_solved} threads solved by {total_staff} staff member{'s' if total_staff != 1 else ''} • Resets monthly")
        
        # Add timestamp
        embed.timestamp = datetime.now()
        
        await interaction.followup.send(embed=embed, ephemeral=False)
        print(f"📊 Leaderboard displayed by {interaction.user}")
        
    except Exception as e:
        print(f"Error in leaderboard command: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

# --- RUN THE BOT WITH AUTO-RESTART ---
async def run_bot_with_restart():
    """Run the bot with automatic restart on crashes"""
    max_retries = 10
    retry_delay = 5  # Start with 5 seconds
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"🚀 Starting bot (attempt {retry_count + 1}/{max_retries})...")
            await bot.start(DISCORD_BOT_TOKEN)
        except KeyboardInterrupt:
            print("\n⚠️ Bot stopped by user (KeyboardInterrupt)")
            break
        except Exception as e:
            retry_count += 1
            error_type = type(e).__name__
            print(f"\n❌ Bot crashed: {error_type}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            if retry_count < max_retries:
                print(f"🔄 Attempting to restart in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                # Exponential backoff with max 60 seconds
                retry_delay = min(retry_delay * 2, 60)
            else:
                print(f"❌ Max retries ({max_retries}) reached. Bot stopped.")
                raise
        else:
            # If bot exits normally (shouldn't happen), restart
            print("⚠️ Bot exited unexpectedly. Restarting...")
            retry_count = 0
            retry_delay = 5

# Global exception handler for unhandled errors
def handle_exception(loop, context):
    """Handle unhandled exceptions in the event loop"""
    exception = context.get('exception')
    if exception:
        print(f"⚠️ Unhandled exception in event loop: {type(exception).__name__}: {str(exception)}")
        import traceback
        traceback.print_exc()
    else:
        print(f"⚠️ Unhandled error in event loop: {context.get('message', 'Unknown error')}")

if __name__ == "__main__":
    # Set up global exception handler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(handle_exception)
    
    try:
        # Run bot with auto-restart
        loop.run_until_complete(run_bot_with_restart())
    except KeyboardInterrupt:
        print("\n⚠️ Bot stopped by user")
    finally:
        loop.close()