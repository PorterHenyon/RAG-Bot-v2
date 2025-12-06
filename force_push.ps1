# Force commit and push all changes
Write-Host "=== Force Pushing All Changes ===" -ForegroundColor Green

# Check current branch
Write-Host "`n1. Checking current branch..." -ForegroundColor Yellow
$branch = git rev-parse --abbrev-ref HEAD
Write-Host "   Current branch: $branch" -ForegroundColor Cyan

# Check for uncommitted changes
Write-Host "`n2. Checking for uncommitted changes..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "   Found uncommitted changes:" -ForegroundColor Yellow
    Write-Host $status
    Write-Host "`n3. Staging all changes..." -ForegroundColor Yellow
    git add -A
    Write-Host "   ✓ All changes staged" -ForegroundColor Green
} else {
    Write-Host "   ✓ No uncommitted changes" -ForegroundColor Green
}

# Check if there are commits to push
Write-Host "`n4. Checking commits to push..." -ForegroundColor Yellow
$commitsAhead = git rev-list --count HEAD ^origin/$branch 2>$null
if ($commitsAhead -gt 0) {
    Write-Host "   Found $commitsAhead commits to push" -ForegroundColor Yellow
} else {
    Write-Host "   No commits ahead of remote" -ForegroundColor Yellow
    Write-Host "   Creating commit with all current changes..." -ForegroundColor Yellow
    git add -A
    git commit -m "Complete fix: RAG saving, auto-response logic, translate removal, ask cooldown, issue classification, leaderboard, search improvements, API rotation"
    Write-Host "   ✓ Commit created" -ForegroundColor Green
}

# Push to origin
Write-Host "`n5. Pushing to origin/$branch..." -ForegroundColor Yellow
git push origin $branch
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Successfully pushed to GitHub!" -ForegroundColor Green
} else {
    Write-Host "   ✗ Push failed! Error code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host "`n   This might be an authentication issue." -ForegroundColor Yellow
    Write-Host "   Try: git push origin $branch" -ForegroundColor Yellow
}

# Show final status
Write-Host "`n6. Final status:" -ForegroundColor Yellow
git status --short

Write-Host "`n=== Done ===" -ForegroundColor Green
