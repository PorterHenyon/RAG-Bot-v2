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
    
    # Try multiple models to find one that works
    models_to_try = ['gemini-1.5-flash', 'gemini-2.5-flash', 'gemini-flash-latest', 'gemini-pro-latest', 'gemini-1.5-pro']
    model_worked = False
    working_model = None
    
    for model_name in models_to_try:
        try:
            # Configure genai with this key
            genai.configure(api_key=test_key)
            
            # Try to create a model
            test_model = genai.GenerativeModel(model_name)
            
            # Try to generate a simple response
            test_response = test_model.generate_content("Say hello in one word")
            
            if test_response and hasattr(test_response, 'text') and test_response.text:
                print(f"   ✅ WORKING with {model_name}! Response: {test_response.text.strip()[:50]}")
                working_keys.append((i, key_name, key_short, model_name))
                model_worked = True
                working_model = model_name
                break
        except Exception as model_error:
            error_str = str(model_error).lower()
            error_msg = str(model_error)[:200]
            
            if 'not found' in error_str or '404' in error_str:
                # Model not available, try next one
                continue
            elif 'api key' in error_str or 'auth' in error_str or '403' in error_str or 'leaked' in error_str or 'permission denied' in error_str:
                # Key is invalid, don't try other models
                failed_keys.append((i, key_name, key_short, f"Invalid/Leaked: {error_msg}"))
                break
            elif 'quota' in error_str or 'rate limit' in error_str or '429' in error_str:
                # Rate limited but key works
                print(f"   ⚠️ RATE LIMITED with {model_name} (but key is valid)")
                working_keys.append((i, key_name, key_short, f"{model_name} (rate limited)"))
                model_worked = True
                break
            else:
                # Other error, try next model
                continue
    
    if not model_worked:
        # None of the models worked
        print(f"   ❌ FAILED: No models available for this key")
        failed_keys.append((i, key_name, key_short, "No models available"))

print(f"\n{'='*60}")
print(f"RESULTS SUMMARY")
print(f"{'='*60}\n")

print(f"✅ WORKING KEYS ({len(working_keys)}):")
if working_keys:
    for idx, key_name, key_short, model in working_keys:
        print(f"   {idx}. {key_name} ({key_short}) - Works with {model}")
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
