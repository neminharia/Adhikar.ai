# 📦 GitHub Commands Reference

Quick reference for pushing this project to GitHub.

## Initial Setup (First Time)

### 1. Initialize Git Repository (if not already done)

```bash
git init
```

### 2. Add All Files

```bash
git add .
```

### 3. Create Initial Commit

```bash
git commit -m "Initial commit: Adhikar.ai Legal AI Assistant"
```

### 4. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `SGP_FB` (or your preferred name)
3. Description: "⚖️ Adhikar.ai - Legal AI Assistant for Supreme Court Case Prediction"
4. Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we already have them)
6. Click "Create repository"

### 5. Add Remote and Push

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/SGP_FB.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Regular Workflow

### Check Status

```bash
git status
```

### Add Changes

```bash
# Add specific file
git add archive_new/app.py

# Add all changes
git add .

# Add with pattern
git add *.py
```

### Commit Changes

```bash
# Simple commit
git commit -m "Add new feature: export to PDF"

# Detailed commit
git commit -m "Add export to PDF feature

- Implement PDF export functionality
- Add download button in UI
- Include prediction details in export"
```

### Push to GitHub

```bash
# Push to main branch
git push origin main

# Push to specific branch
git push origin feature-branch-name
```

## Branch Management

### Create New Branch

```bash
git checkout -b feature/new-feature
```

### Switch Branch

```bash
git checkout main
git checkout feature/new-feature
```

### List Branches

```bash
git branch
```

### Merge Branch

```bash
git checkout main
git merge feature/new-feature
```

## Common Commands

### View Commit History

```bash
git log
git log --oneline
git log --graph --oneline --all
```

### Undo Changes

```bash
# Unstage file (keep changes)
git reset HEAD filename

# Discard changes in working directory
git checkout -- filename

# Undo last commit (keep changes)
git reset --soft HEAD~1
```

### Update from Remote

```bash
# Fetch changes
git fetch origin

# Pull changes
git pull origin main
```

## Before Pushing Checklist

✅ **Check .gitignore is working:**
```bash
git status
# Should NOT show:
# - venv/
# - .streamlit/secrets.toml
# - archive_new/legalbert_supreme/
# - *.pkl files
```

✅ **Verify secrets are not committed:**
```bash
git grep "mongodb+srv"  # Should return nothing
git grep "api_key" .streamlit/  # Should return nothing
```

✅ **Test the application:**
```bash
streamlit run archive_new/app.py
```

## Important Notes

### ⚠️ Never Commit:

- `.streamlit/secrets.toml` - Contains API keys
- `venv/` - Virtual environment
- Model files (`*.safetensors`, `*.bin`, `*.pkl`)
- `.env` files
- Personal data files

### ✅ Always Commit:

- Source code (`.py` files)
- Configuration templates (`*.example` files)
- Documentation (`.md` files)
- `requirements.txt`
- `.gitignore`

## Quick Push Script

Create a file `push.sh` (Linux/Mac) or `push.bat` (Windows):

**push.sh:**
```bash
#!/bin/bash
git add .
git commit -m "$1"
git push origin main
```

**push.bat:**
```batch
@echo off
git add .
git commit -m "%1"
git push origin main
```

Usage:
```bash
# Linux/Mac
chmod +x push.sh
./push.sh "Your commit message"

# Windows
push.bat "Your commit message"
```

## Troubleshooting

### "Remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/SGP_FB.git
```

### "Authentication failed"
- Use Personal Access Token instead of password
- Or use SSH: `git@github.com:YOUR_USERNAME/SGP_FB.git`

### "Large file warning"
```bash
# Remove large file from history (if accidentally committed)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/large/file" \
  --prune-empty --tag-name-filter cat -- --all
```

### "Merge conflicts"
```bash
# See conflicts
git status

# Edit conflicted files, then:
git add .
git commit -m "Resolve merge conflicts"
```

## GitHub Repository Settings

After pushing, configure:

1. **Repository Settings → Secrets**
   - Add GitHub Actions secrets if using CI/CD

2. **Repository Settings → Pages** (if deploying)
   - Configure for Streamlit Cloud deployment

3. **Add Topics/Tags:**
   - `legal-ai`
   - `streamlit`
   - `legalbert`
   - `supreme-court`
   - `india`

4. **Add Description:**
   - "⚖️ Legal AI Assistant for Supreme Court Case Outcome Prediction using LegalBERT and Gemini AI"

---

**Ready to push?** Follow the "Initial Setup" section above! 🚀

