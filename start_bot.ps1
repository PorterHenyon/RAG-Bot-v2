# Quick start — runs bot in foreground so you can see errors immediately
Write-Host "Starting Support Ticket Tracker..." -ForegroundColor Green

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path .env)) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Installing dependencies..." -ForegroundColor Cyan
& .\venv\Scripts\python.exe -m pip install -q -r requirements-tracker.txt

Write-Host ""
Write-Host "Starting bot (Ctrl+C to stop)..." -ForegroundColor Green
Write-Host ""
& .\venv\Scripts\python.exe -u ticket_tracker.py
