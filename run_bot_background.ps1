# Runs the ticket tracker bot in the background (for auto-start)
$ProjectRoot = $PSScriptRoot
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "bot.log"
$PidFile = Join-Path $LogDir "bot.pid"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Set-Location $ProjectRoot

if (-not (Test-Path .env)) {
    Add-Content $LogFile "$(Get-Date -Format o) ERROR: .env file missing"
    exit 1
}

# Stop an existing bot instance if we started one earlier
if (Test-Path $PidFile) {
    $oldPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

if (-not (Test-Path venv)) {
    python -m venv venv
}

$PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"
& $PythonExe -m pip install -q -r requirements-tracker.txt 2>&1 | Out-File -FilePath $LogFile -Append

Add-Content $LogFile "$(Get-Date -Format o) Starting ticket tracker..."

# cmd merges stdout+stderr reliably (Start-Process cannot use same file for both)
$cmd = "`"$PythonExe`" -u ticket_tracker.py >> `"$LogFile`" 2>&1"
$proc = Start-Process cmd -ArgumentList "/c", $cmd -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru

if ($proc) {
    $proc.Id | Out-File -FilePath $PidFile -Encoding ascii
    Add-Content $LogFile "$(Get-Date -Format o) Bot process started (PID $($proc.Id))"
} else {
    Add-Content $LogFile "$(Get-Date -Format o) ERROR: Failed to start bot process"
    exit 1
}
