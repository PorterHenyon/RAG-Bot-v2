# Register the ticket tracker bot to start automatically when you log in to Windows.
# Run once:  powershell -ExecutionPolicy Bypass -File install_autostart.ps1

$ProjectRoot = $PSScriptRoot
$TaskName = "RevolutionTicketTracker"
$ScriptPath = Join-Path $ProjectRoot "run_bot_background.ps1"

Write-Host "Installing auto-start for Support Ticket Tracker..." -ForegroundColor Cyan
Write-Host "  Project: $ProjectRoot"
Write-Host "  Task:    $TaskName"
Write-Host ""

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" `
    -WorkingDirectory $ProjectRoot

$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Keeps the Discord ticket tracker online for /daily_summary and /scan commands" `
    -Force | Out-Null

Write-Host "✓ Scheduled task registered — bot starts when you log in to Windows" -ForegroundColor Green
Write-Host ""
Write-Host "Starting bot now..." -ForegroundColor Cyan
& $ScriptPath
Write-Host "✓ Bot started in background (logs: logs\bot.log)" -ForegroundColor Green
Write-Host ""
Write-Host "Daily summaries are sent automatically by GitHub Actions at 9 AM Mountain Time." -ForegroundColor Yellow
Write-Host "Add GitHub repo secrets (one-time) — see SETUP_AUTORUN.md" -ForegroundColor Yellow
