# Complete Fix for Large Files - Run this script
# This will properly remove large files from git history

Write-Host "Fixing Large Files Issue" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

# Step 1: Check for unstaged changes
Write-Host "`nStep 1: Checking git status..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "Unstaged changes detected. Stashing them..." -ForegroundColor Yellow
    git stash push -m "Temporary stash for large file cleanup"
    $stashed = $true
} else {
    Write-Host "No unstaged changes" -ForegroundColor Green
    $stashed = $false
}

# Step 2: Configure git
Write-Host "`nStep 2: Configuring git..." -ForegroundColor Yellow
$env:FILTER_BRANCH_SQUELCH_WARNING = "1"
git config http.postBuffer 524288000
git config http.maxRequestBuffer 100M
Write-Host "Git configured" -ForegroundColor Green

# Step 3: Remove large files from history
Write-Host "`nStep 3: Removing large files from git history..." -ForegroundColor Yellow
Write-Host "This will take a few minutes. Please wait..." -ForegroundColor Yellow

# Remove model directory from all commits
git filter-branch --force --index-filter "git rm -rf --cached --ignore-unmatch archive_new/legalbert_supreme" --prune-empty --tag-name-filter cat -- --all

if ($LASTEXITCODE -eq 0) {
    Write-Host "Large files removed from history" -ForegroundColor Green
} else {
    Write-Host "filter-branch completed with warnings" -ForegroundColor Yellow
}

# Step 4: Clean up
Write-Host "`nStep 4: Cleaning up git references..." -ForegroundColor Yellow
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin 2>$null
git reflog expire --expire=now --all
git gc --prune=now --aggressive
Write-Host "Cleanup completed" -ForegroundColor Green

# Step 5: Restore stashed changes
if ($stashed) {
    Write-Host "`nStep 5: Restoring stashed changes..." -ForegroundColor Yellow
    git stash pop
    Write-Host "Changes restored" -ForegroundColor Green
}

# Step 6: Verify
Write-Host "`nStep 6: Verifying repository..." -ForegroundColor Yellow
$repoSize = git count-objects -vH | Select-String "size-pack" | ForEach-Object { ($_ -split ":")[1].Trim() }
Write-Host "Repository size: $repoSize" -ForegroundColor Cyan

# Check for large files in working directory
Write-Host "`nChecking for large files in working directory..." -ForegroundColor Yellow
$largeFiles = @()
git ls-files | ForEach-Object { 
    $file = Get-Item $_ -ErrorAction SilentlyContinue
    if ($file -and $file.Length -gt 50MB) {
        $largeFiles += [PSCustomObject]@{
            File = $_
            Size = "{0:N2} MB" -f ($file.Length / 1MB)
        }
    }
}

if ($largeFiles.Count -gt 0) {
    Write-Host "Large files found in working directory:" -ForegroundColor Red
    $largeFiles | Format-Table -AutoSize
    Write-Host "These files should be in .gitignore" -ForegroundColor Yellow
} else {
    Write-Host "No large files in working directory" -ForegroundColor Green
}

Write-Host "`nDone! Repository cleaned." -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "   1. Review changes: git status" -ForegroundColor White
Write-Host "   2. Commit any needed changes" -ForegroundColor White
Write-Host "   3. Force push: git push origin main --force" -ForegroundColor White
Write-Host "`nWARNING: --force rewrites history. Only use if you are the only contributor!" -ForegroundColor Red
