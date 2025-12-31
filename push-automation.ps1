# Push Automation to GitHub
# Run this script to commit and push all automation files

Write-Host "=== Pushing CI/CD Automation to GitHub ===" -ForegroundColor Green
Write-Host ""

# Navigate to project directory
Set-Location "C:\Users\Nitro-5\Cool Projects\Computer-Peripheral-App"

# Show what will be committed
Write-Host "Files to be committed:" -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "Staging all changes..." -ForegroundColor Cyan
git add .

Write-Host "Creating commit..." -ForegroundColor Cyan
git commit -m "Add CI/CD automation for Windows and Android builds

- Added GitHub Actions workflow for automated builds
- Windows server executable (RemoteMouseServer.exe)
- Android APK (debug and release versions)
- Automatic GitHub Releases creation
- PyInstaller configuration for optimal Windows builds
- Complete documentation suite
- Updated README with automation info

Builds trigger automatically on push to master branch."

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
git push origin master

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Go to: https://github.com/YOUR_USERNAME/Computer-Peripheral-App/actions"
Write-Host "2. Watch your first automated build run!"
Write-Host "3. Download executables from Releases section in ~10-15 minutes"
Write-Host ""
Write-Host "See .github/CHECKLIST.md for detailed testing steps." -ForegroundColor Cyan

