# Quick Start: Automated Builds

## 🚀 How to Trigger Automated Builds

Simply push your changes to the `master` branch:

```powershell
git add .
git commit -m "Your commit message"
git push origin master
```

That's it! The automation will:
1. ✅ Build the Windows server executable
2. ✅ Build the Android APK (debug and release)
3. ✅ Create a GitHub Release with all files
4. ✅ Upload all artifacts

## 📦 Where to Find Your Builds

### Option 1: GitHub Actions Artifacts (available immediately)
1. Go to your repository on GitHub
2. Click the **Actions** tab
3. Click on the latest workflow run
4. Scroll down to **Artifacts** section
5. Download:
   - `windows-server-exe` (RemoteMouseServer.exe)
   - `android-debug-apk` (app-debug.apk)
   - `android-release-apk` (app-release-unsigned.apk)

### Option 2: GitHub Releases (created automatically)
1. Go to your repository on GitHub
2. Click the **Releases** section (right sidebar)
3. Download the latest release
4. All executables are attached as release assets

## 💰 Is This Free?

**Yes!** For public repositories, GitHub Actions is completely free with unlimited build minutes.

For private repositories, you get 2,000 free minutes per month (Windows runners count as 2x).

## ⚙️ Files Created

This automation setup created:

1. **`.github/workflows/build-release.yml`** - Main CI/CD workflow
2. **`server/server.spec`** - PyInstaller configuration
3. **`.github/ACTIONS_README.md`** - Detailed documentation
4. **`.github/QUICKSTART.md`** - This file

## 🔧 What Happens on Each Push to Master?

```
Push to master
    ↓
GitHub Actions triggers
    ↓
┌─────────────────────┐         ┌──────────────────────┐
│ Windows Job         │         │ Android Job          │
│ - Install Python    │         │ - Setup Java/Gradle  │
│ - Install deps      │         │ - Build debug APK    │
│ - Run PyInstaller   │         │ - Build release APK  │
│ - Create .exe       │         │ - Upload artifacts   │
└─────────────────────┘         └──────────────────────┘
           ↓                              ↓
           └──────────┬───────────────────┘
                      ↓
           ┌─────────────────────┐
           │ Create Release      │
           │ - Tag with date     │
           │ - Attach all files  │
           │ - Publish release   │
           └─────────────────────┘
```

## 🐛 Troubleshooting

**Build failed?**
- Check the Actions tab for error logs
- Common issues:
  - Missing dependencies in requirements.txt
  - Gradle configuration errors
  - Syntax errors in code

**Can't find the executables?**
- Wait for the workflow to complete (usually 5-10 minutes)
- Check under Actions → Latest run → Artifacts
- Releases are only created for pushes to master (not pull requests)

**Want to test locally first?**
```powershell
# Test Windows server build
cd server
pip install -r requirements.txt
pip install pyinstaller
pyinstaller server.spec
# Output: server/dist/RemoteMouseServer.exe

# Test Android build (requires Android SDK)
./gradlew assembleDebug
# Output: app/build/outputs/apk/debug/app-debug.apk
```

## 📝 Next Steps

1. **Customize the release notes**: Edit `.github/workflows/build-release.yml` → `create-release` job
2. **Add code signing**: Configure keystore for Android, code signing cert for Windows
3. **Add more branches**: Include `develop` or `main` branches in the workflow triggers
4. **Set up notifications**: Configure GitHub to notify you when builds complete

## 📚 More Info

See `.github/ACTIONS_README.md` for detailed documentation.

