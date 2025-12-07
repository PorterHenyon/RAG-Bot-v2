#!/usr/bin/env python3
"""Test all Gemini API keys to see which ones work"""

import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Also try to load from Railway environment (if running there)
# Railway sets environment variables directly, so they should already be available

# Load all API keys
GEMINI_API_KEYS = []

# Load GEMINI_API_KEY (primary key)
env_key = os.getenv('GEMINI_API_KEY')
if env_key:
    GEMINI_API_KEYS.append(env_key)

# Load additional keys (GEMINI_API_KEY_2 through GEMINI_API_KEY_20)
for i in range(2, 21):
    additional_key = os.getenv(f'GEMINI_API_KEY_{i}')
    if additional_key and additional_key not in GEMINI_API_KEYS:
        GEMINI_API_KEYS.append(additional_key)

print(f"\n{'='*60}")
print(f"Testing {len(GEMINI_API_KEYS)} API Key(s)")
print(f"{'='*60}\n")

if len(GEMINI_API_KEYS) == 0:
    print("❌ No API keys found in environment variables!")
    print("   Make sure GEMINI_API_KEY is set in your .env file or Railway environment variables")
    print("\n   If you're running this locally but keys are in Railway:")
    print("   1. Copy your keys from Railway to a .env file, OR")
    print("   2. Run this script on Railway using: railway run python test_keys.py")
    exit(1)

working_keys = []
failed_keys = []

for i, test_key in enumerate(GEMINI_API_KEYS, 1):
    key_short = test_key[:15] + '...' if len(test_key) > 15 else test_key
    key_name = f"GEMINI_API_KEY" if i == 1 else f"GEMINI_API_KEY_{i}"
    
    print(f"Testing Key {i} ({key_name}): {key_short}")
    
    try:
        # Configure genai with this key
        genai.configure(api_key=test_key)
        
        # Try to create a model
        test_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Try to generate a simple response
        test_response = test_model.generate_content("Say hello in one word")
        
        if test_response and hasattr(test_response, 'text') and test_response.text:
            print(f"   ✅ WORKING! Response: {test_response.text.strip()[:50]}")
            working_keys.append((i, key_name, key_short))
        else:
            print(f"   ❌ FAILED: No response text")
            failed_keys.append((i, key_name, key_short, "No response text"))
            
    except Exception as e:
        error_str = str(e).lower()
        error_msg = str(e)[:200]
        
        if 'api key' in error_str or 'auth' in error_str or '403' in error_str or 'leaked' in error_str or 'permission denied' in error_str:
            print(f"   ❌ INVALID/LEAKED: {error_msg}")
            failed_keys.append((i, key_name, key_short, f"Invalid/Leaked: {error_msg}"))
        elif 'quota' in error_str or 'rate limit' in error_str or '429' in error_str:
            print(f"   ⚠️ RATE LIMITED (but key is valid): {error_msg}")
            working_keys.append((i, key_name, key_short))  # Rate limited but key works
        elif 'not found' in error_str or 'invalid' in error_str:
            print(f"   ⚠️ MODEL NOT FOUND (key might work with different model): {error_msg}")
            failed_keys.append((i, key_name, key_short, f"Model issue: {error_msg}"))
        else:
            print(f"   ❌ FAILED: {error_msg}")
            failed_keys.append((i, key_name, key_short, error_msg))

print(f"\n{'='*60}")
print(f"RESULTS SUMMARY")
print(f"{'='*60}\n")

print(f"✅ WORKING KEYS ({len(working_keys)}):")
if working_keys:
    for idx, key_name, key_short in working_keys:
        print(f"   {idx}. {key_name} ({key_short})")
else:
    print("   None")

print(f"\n❌ FAILED KEYS ({len(failed_keys)}):")
if failed_keys:
    for idx, key_name, key_short, reason in failed_keys:
        print(f"   {idx}. {key_name} ({key_short})")
        print(f"      Reason: {reason[:100]}")
else:
    print("   None")

print(f"\n{'='*60}")
if len(working_keys) > 0:
    print(f"✓ {len(working_keys)} key(s) are working. The bot should be able to connect.")
else:
    print(f"❌ NO WORKING KEYS FOUND!")
    print(f"   All keys failed. Check your API keys at: https://aistudio.google.com/app/apikey")
    print(f"   Make sure keys are valid and not leaked.")
print(f"{'='*60}\n")
