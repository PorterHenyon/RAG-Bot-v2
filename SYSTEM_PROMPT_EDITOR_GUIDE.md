# 🤖 System Instruction Editor - Guide

## ✨ What It Does

The **System Instruction Editor** in the Settings tab lets you customize how the Revolution Macro AI bot responds to users - **without touching any code**!

---

## 📝 How to Use

### **Step 1: Open Settings**
1. Go to your dashboard
2. Click **Settings** tab
3. You'll see the **🤖 AI System Instruction** section at the top

### **Step 2: Edit the Instruction**
1. Click in the text area
2. Edit the system prompt however you want
3. The prompt is in **plain text format** - write naturally

### **Step 3: Save**
1. Click **"Save Instruction"** button
2. You'll see: **✓ Saved & synced to API!**
3. The prompt is now saved to Redis/Vercel KV

### **Step 4: Update the Bot**
**Option A: Immediate (Recommended)**
```
In Discord, run: /reload
```
Bot will fetch the new prompt instantly.

**Option B: Wait for Auto-Sync**
```
Bot syncs every hour automatically
```

---

## 🎯 What You Can Customize

### **Bot Personality:**
```
Your tone should be friendly and patient.
```
→ Change to whatever you want!

### **Response Style:**
```
Keep answers concise (2-4 paragraphs max)
```
→ Make it longer, shorter, more detailed, etc.

### **Features to Mention:**
```
KEY FEATURES OF REVOLUTION MACRO:
- Automated gathering and resource collection
- Smart pathing and navigation systems
```
→ Add/remove features as needed

### **Common Issues:**
```
COMMON ISSUES USERS FACE:
- Character resetting during tasks
- Initialization errors
```
→ Update based on what users actually ask about

### **Response Guidelines:**
```
RESPONSE GUIDELINES:
- Use numbered steps for troubleshooting
- Reference specific settings/tabs
```
→ Add your own guidelines

---

## 💡 Example Customizations

### Make Responses More Casual:
```
You are the Revolution Macro support bot! 🚀

Hey there! I'm here to help you with Revolution Macro.
Feel free to ask me anything - no question is too simple!

I'll do my best to help. If I'm not sure about something,
I'll be honest and connect you with the team. Let's fix
this together!
```

### Make Responses More Technical:
```
You are a technical support specialist for Revolution Macro.

Provide detailed, technical solutions with:
1. Exact file paths and settings locations
2. Configuration file syntax examples
3. Command-line parameters when relevant
4. Debug logging instructions
5. Advanced troubleshooting steps

Assume users have intermediate technical knowledge.
```

### Focus on Specific Game:
```
You are the Revolution Macro support bot specializing in 
Bee Swarm Simulator automation.

Common BSS features:
- Honey conversion automation
- Field rotation and prioritization
- Hive management and auto-convert
- Quest automation
- Mondo Chick farming
- etc.

Focus answers on BSS-specific scenarios.
```

---

## 🔄 How It Works

```
Dashboard (Settings Tab)
    ↓
Edit system instruction
    ↓
Click "Save Instruction"
    ↓
Saved to Redis/Vercel KV (API)
    ↓
Bot fetches on next sync (hourly)
    OR
Bot fetches when you run /reload
    ↓
Bot uses new instruction for ALL responses
```

---

## 🎯 Advanced Tips

### **1. Test Before Deploying**
- Make changes in dev environment first
- Test with `/ask` command to see how bot responds
- Once happy, deploy to production

### **2. Version Control**
- Keep a backup of your system prompt
- Copy/paste to a text file before major changes
- Easy to revert if needed

### **3. Iterative Improvement**
- Start with default prompt
- Monitor bot responses over a week
- Adjust based on what users actually ask
- Refine tone/style based on feedback

### **4. Use Variables (Conceptually)**
You can reference parts of the instruction:
```
TONE: Friendly and professional
STYLE: Step-by-step guides
LENGTH: 2-4 paragraphs

Use the TONE from above...
Follow the STYLE guidelines...
Keep responses to LENGTH specified...
```

---

## ⚠️ Important Notes

### **What the Prompt Controls:**
✅ How the bot responds to questions  
✅ Bot's personality and tone  
✅ What knowledge the bot references  
✅ Response format and structure  

### **What it Does NOT Control:**
❌ Auto-response triggers (those are separate)  
❌ RAG entry matching logic  
❌ When to escalate to humans (AI decides)  
❌ Slash commands (those are code-based)  

### **Best Practices:**
1. **Be specific** - Tell the AI exactly how to behave
2. **Include context** - Mention Revolution Macro features
3. **Set expectations** - Define response length, format, style
4. **Acknowledge limitations** - Tell AI when to admit uncertainty
5. **Stay on-brand** - Match your company's voice

---

## 📊 Testing Your Changes

After updating the system prompt:

### **Test 1: Quick Check**
```
1. Save new prompt
2. Run /reload in Discord
3. Use /ask command with a test question
4. Check if response matches your new instruction
```

### **Test 2: Live Test**
```
1. Create a test forum post
2. See how bot responds
3. Verify tone, style, content match your prompt
```

### **Test 3: Edge Cases**
```
1. Ask an off-topic question
2. Ask something the bot doesn't know
3. Verify it handles uncertainty as instructed
```

---

## 🎨 Prompt Template

Here's a good structure to follow:

```
You are [who/what the bot is].

[App Name] FEATURES:
- Feature 1
- Feature 2
- Feature 3

COMMON USER ISSUES:
- Issue 1 (usual cause)
- Issue 2 (usual cause)
- Issue 3 (usual cause)

YOUR ROLE:
1. Responsibility 1
2. Responsibility 2
3. Responsibility 3

RESPONSE GUIDELINES:
- Guideline 1
- Guideline 2
- Guideline 3

TONE: [Describe desired tone]

When uncertain, [how to handle uncertainty].
```

---

## ✅ Quick Reference

| Action | How To Do It |
|--------|--------------|
| **Edit prompt** | Settings tab → Edit text area |
| **Save changes** | Click "Save Instruction" |
| **Apply to bot** | Run `/reload` in Discord |
| **Test changes** | Use `/ask` command |
| **Revert changes** | Paste previous version, save again |
| **See last update** | Check timestamp below text area |

---

Your Revolution Macro bot's AI is now **fully customizable** through the dashboard! 🎉

