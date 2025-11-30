# Quick start script for Revolution Macro Bot
Write-Host "🚀 Starting Revolution Macro Bot..." -ForegroundColor Green
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "❌ ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "   Create a .env file with DISCORD_BOT_TOKEN, GEMINI_API_KEY, etc." -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path venv)) {
    Write-Host "⚠️  Virtual environment not found. Creating one..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Check if dependencies are installed
if (-not (Test-Path venv\Lib\site-packages\discord.py)) {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan
    pip install -r requirements.txt
}

# Start the bot
Write-Host ""
Write-Host "🤖 Starting bot..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
python bot.py

