# PowerShell Script to Fix Large Files Issue
# Run this script in PowerShell from your project root

Write-Host "🔧 Fixing Large Files Issue..." -ForegroundColor Cyan

# Step 1: Configure git for large files
Write-Host "`n📝 Step 1: Configuring git buffer sizes..." -ForegroundColor Yellow
git config http.postBuffer 524288000
git config http.maxRequestBuffer 100M
Write-Host "✅ Git buffer configured" -ForegroundColor Green

# Step 2: Remove large files from history
Write-Host "`n🗑️ Step 2: Removing large files from git history..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Yellow

git filter-branch --force --index-filter "git rm -rf --cached --ignore-unmatch archive_new/legalbert_supreme" --prune-empty --tag-name-filter cat -- --all

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Large files removed from history" -ForegroundColor Green
} else {
    Write-Host "⚠️ Warning: filter-branch may have issues. Continuing..." -ForegroundColor Yellow
}

# Step 3: Clean up references
Write-Host "`n🧹 Step 3: Cleaning up git references..." -ForegroundColor Yellow
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive
Write-Host "✅ Git cleanup completed" -ForegroundColor Green

# Step 4: Verify
Write-Host "`n📊 Step 4: Checking repository size..." -ForegroundColor Yellow
git count-objects -vH

# Step 5: Check for remaining large files
Write-Host "`n🔍 Step 5: Checking for large files..." -ForegroundColor Yellow
$largeFiles = git ls-files | ForEach-Object { 
    $file = Get-Item $_ -ErrorAction SilentlyContinue
    if ($file -and $file.Length -gt 50MB) {
        [PSCustomObject]@{
            File = $_
            Size = "{0:N2} MB" -f ($file.Length / 1MB)
        }
    }
}

if ($largeFiles) {
    Write-Host "⚠️ Large files still found:" -ForegroundColor Red
    $largeFiles | Format-Table
    Write-Host "Please remove these files manually" -ForegroundColor Yellow
} else {
    Write-Host "✅ No large files found" -ForegroundColor Green
}

Write-Host "`n✨ Done! Now you can push to GitHub:" -ForegroundColor Cyan
Write-Host "   git push origin main --force" -ForegroundColor White
Write-Host "`n⚠️  WARNING: --force rewrites history. Only use if you're the only contributor!" -ForegroundColor Yellow

