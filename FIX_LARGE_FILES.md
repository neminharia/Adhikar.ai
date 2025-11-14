# 🔧 Fix Large Files Issue - Step by Step Guide

Your repository has large files in git history that need to be removed. Follow these steps:

## ⚠️ Problem
- Large model file (417MB) in git history
- GitHub rejects files over 100MB
- Need to remove from history, not just current files

## ✅ Solution Steps

### Step 1: Increase Git Buffer Size

```powershell
# Increase buffer to handle large operations
git config http.postBuffer 524288000
git config http.maxRequestBuffer 100M
```

### Step 2: Remove Large Files from Git History

**Option A: Using git filter-branch (Recommended for this case)**

```powershell
# Remove model.safetensors from entire history
git filter-branch --force --index-filter `
  "git rm --cached --ignore-unmatch archive_new/legalbert_supreme/model.safetensors" `
  --prune-empty --tag-name-filter cat -- --all

# Remove entire model directory from history
git filter-branch --force --index-filter `
  "git rm -rf --cached --ignore-unmatch archive_new/legalbert_supreme" `
  --prune-empty --tag-name-filter cat -- --all
```

**Option B: Using git filter-repo (Faster, but needs installation)**

```powershell
# Install git-filter-repo first
pip install git-filter-repo

# Remove model directory from history
git filter-repo --path archive_new/legalbert_supreme --invert-paths
```

### Step 3: Force Garbage Collection

```powershell
# Remove all unreferenced objects
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Step 4: Verify Large Files Are Gone

```powershell
# Check repository size
git count-objects -vH

# List large files (if any remain)
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {print substr($0,6)}' | sort --numeric-sort --key=2 | tail -10
```

### Step 5: Force Push to GitHub

```powershell
# WARNING: This rewrites history. Make sure you're the only one working on this repo!
git push origin --force --all
git push origin --force --tags
```

## 🚀 Quick Fix Script (Copy & Paste All at Once)

```powershell
# Step 1: Configure git
git config http.postBuffer 524288000
git config http.maxRequestBuffer 100M

# Step 2: Remove large files from history
git filter-branch --force --index-filter "git rm -rf --cached --ignore-unmatch archive_new/legalbert_supreme" --prune-empty --tag-name-filter cat -- --all

# Step 3: Clean up
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Step 4: Force push (CAREFUL - rewrites history!)
git push origin --force --all
```

## 🔄 Alternative: Start Fresh (Easier but loses history)

If you don't need the git history:

```powershell
# 1. Delete .git folder
Remove-Item -Recurse -Force .git

# 2. Reinitialize
git init
git add .
git commit -m "Initial commit: Adhikar.ai Legal AI Assistant"

# 3. Add remote
git remote add origin https://github.com/neminharia/Adhikar.ai.git

# 4. Push
git push -u origin main --force
```

## ✅ Verify .gitignore is Correct

Make sure `.gitignore` has:
```
archive_new/legalbert_supreme/
*.safetensors
*.pkl
*.bin
venv/
```

But **NOT**:
```
archive_new/  # This would ignore app.py too!
```

## 📝 After Fixing

1. Verify no large files:
   ```powershell
   git ls-files | ForEach-Object { Get-Item $_ } | Where-Object { $_.Length -gt 50MB }
   ```

2. Check repository size:
   ```powershell
   git count-objects -vH
   ```

3. Test push:
   ```powershell
   git push origin main
   ```

## ⚠️ Important Notes

- **Force push rewrites history** - Only do this if you're the only contributor
- **Backup first** - Make sure you have a backup of your code
- **Model files** - Keep them locally, just don't commit them
- **Git LFS** - If you need to track large files, use Git LFS (but not recommended for models)

## 🎯 Recommended Approach

For this project, **don't commit model files**. Instead:

1. Remove from git history (use steps above)
2. Keep models locally
3. Add to `.gitignore` (already done)
4. Document in README where to get models
5. Use GitHub Releases for model distribution (if needed)

---

**After running these commands, your push should work!** 🚀

