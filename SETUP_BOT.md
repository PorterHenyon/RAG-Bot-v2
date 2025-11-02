# Setting Up the Discord Bot Locally

## Quick Start with Virtual Environment

### Step 1: Create Virtual Environment

```bash
python -m venv venv
```

### Step 2: Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**On Mac/Linux:**
```bash
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create .env File

Create a `.env` file in the root directory:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
SUPPORT_FORUM_CHANNEL_ID=your_channel_id_here
DATA_API_URL=https://your-vercel-url.vercel.app/api/data
```

### Step 5: Run the Bot

```bash
python bot.py
```

## Deactivate Virtual Environment

When you're done working:

```bash
deactivate
```

## Why Use a Virtual Environment?

✅ **Isolates dependencies** - Prevents conflicts with other Python projects
✅ **No root/sudo needed** - Avoids permission warnings
✅ **Clean installation** - Only installs what your bot needs
✅ **Easier cleanup** - Just delete the `venv` folder to remove everything

## Troubleshooting

### PowerShell Execution Policy Error

If you get: `cannot be loaded because running scripts is disabled on this system`

Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Can't Find Python

Make sure Python is installed and in your PATH:
```bash
python --version
```

If that doesn't work, try:
```bash
py --version
```

### Virtual Environment Already Exists

If `venv` folder already exists, you can:
- **Reuse it**: Just activate it and install dependencies
- **Start fresh**: Delete the `venv` folder and create a new one

