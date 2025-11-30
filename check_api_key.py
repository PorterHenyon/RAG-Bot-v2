#!/usr/bin/env python3
"""
Quick script to check if your Gemini API key is valid
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file")
    print("\n📝 Steps to fix:")
    print("   1. Open your .env file")
    print("   2. Add: GEMINI_API_KEY=your_key_here")
    print("   3. Get a key from: https://aistudio.google.com/app/apikey")
    exit(1)

print(f"✓ Found API key: {api_key[:15]}...")
print("Testing connection...")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Say hello")
    print(f"✅ SUCCESS! API key is valid.")
    print(f"   Response: {response.text}")
    print("\n✓ Your bot should work now!")
except Exception as e:
    error_msg = str(e)
    if 'leaked' in error_msg.lower():
        print("❌ ERROR: Your API key was reported as LEAKED")
        print("\n📝 You MUST get a NEW API key:")
        print("   1. Go to: https://aistudio.google.com/app/apikey")
        print("   2. Delete the old key (if you can see it)")
        print("   3. Click 'Create API Key' to make a NEW one")
        print("   4. Copy the new key")
        print("   5. Update GEMINI_API_KEY in your .env file")
        print("   6. Run this script again to verify")
    elif '403' in error_msg or 'permission' in error_msg.lower():
        print("❌ ERROR: API key is invalid or has no permissions")
        print("\n📝 Get a new key from: https://aistudio.google.com/app/apikey")
    else:
        print(f"❌ ERROR: {error_msg}")
    exit(1)

