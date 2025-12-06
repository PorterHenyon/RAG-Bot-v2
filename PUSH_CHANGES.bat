@echo off
echo ========================================
echo FORCE PUSHING ALL CHANGES TO GITHUB
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Checking git status...
git status
echo.

echo Step 2: Staging all changes...
git add -A
echo.

echo Step 3: Committing all changes...
git commit -m "COMPLETE FIX: All 9 fixes - RAG saving, auto-response logic, translate removal, ask cooldown, issue classification, leaderboard saving, search improvements, API rotation, sync interval"
echo.

echo Step 4: Pushing to GitHub...
git push origin main
echo.

echo Step 5: Final status...
git status
echo.

echo ========================================
echo DONE! Check GitHub to verify the push.
echo ========================================
pause
