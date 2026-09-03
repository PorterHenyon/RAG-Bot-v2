# Runs the ticket tracker bot in the background (for auto-start)
$ProjectRoot = $PSScriptRoot
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "bot.log"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Set-Location $ProjectRoot

if (-not (Test-Path .env)) {
    Add-Content $LogFile "$(Get-Date -Format o) ERROR: .env file missing"
    exit 1
}

if (-not (Test-Path venv)) {
    python -m venv venv
}

& "$ProjectRoot\venv\Scripts\python.exe" -m pip install -q -r requirements-tracker.txt 2>> $LogFile

$PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"
Add-Content $LogFile "$(Get-Date -Format o) Starting ticket tracker..."

Start-Process -FilePath $PythonExe `
    -ArgumentList "-u", "ticket_tracker.py" `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError $LogFile
