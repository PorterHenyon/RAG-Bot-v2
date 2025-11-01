# Repository Push Instructions

## Issue: Repository Rule Violations

If you're getting repository rule violations when pushing, here are common solutions:

## Solution 1: Use a Feature Branch (Recommended)

Many repositories protect the `main` branch and require pull requests:

```bash
# Create a new branch
git checkout -b feature/dashboard-sync

# Push to the new branch
git push -u origin feature/dashboard-sync

# Then create a Pull Request on GitHub
```

## Solution 2: Check for Protected Branch Rules

Your repository might have branch protection rules. Check:
- Go to GitHub → Settings → Branches
- See if `main` branch requires pull requests
- If yes, use Solution 1 above

## Solution 3: Verify No Sensitive Data

We've already removed hardcoded credentials. Verify:

```bash
# Check for any API keys or tokens in code
git grep -i "token\|api_key\|secret" -- '*.py' '*.ts' '*.tsx' '*.js'

# Should only show:
# - env.example (which is fine - it's a template)
# - os.getenv() calls (which is fine - reading from env vars)
```

## Solution 4: Check Commit Message Requirements

Some repos require specific commit message formats:

- ✅ Good: "Add dashboard-to-bot sync functionality"
- ✅ Good: "Remove hardcoded credentials - use environment variables only"
- ❌ Bad: "fix", "update", "changes"

## Solution 5: Check File Size Limits

Large files might be rejected:

```bash
# Check for large files
git ls-files | xargs ls -lh | sort -k5 -hr | head -10

# Files over 100MB might need Git LFS
```

## Solution 6: Force Push (⚠️ Use with Caution)

If you've already removed sensitive data but the remote still has the old commit:

```bash
# ⚠️ WARNING: Only do this if you're the only one working on this repo
# This will overwrite remote history

git push --force-with-lease origin main
```

**Only use this if:**
- You're working alone
- You've verified all sensitive data is removed
- You understand this rewrites history

## What We've Fixed

✅ Removed all hardcoded credentials from `bot.py`
✅ Created `env.example` as a template
✅ Updated `.gitignore` to exclude `.env` files
✅ All credentials now use environment variables only

## Next Steps

1. **Try pushing to a feature branch first:**
   ```bash
   git checkout -b feature/dashboard-sync
   git push -u origin feature/dashboard-sync
   ```

2. **If that works, create a Pull Request on GitHub**

3. **After PR is merged, you can push to main**

## Still Having Issues?

If you're still getting errors, check the exact error message:
- Is it about branch protection?
- Is it about file size?
- Is it about commit messages?
- Is it about required reviewers?

Share the exact error message and we can troubleshoot further!

