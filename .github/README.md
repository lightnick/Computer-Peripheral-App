# 📁 .github Directory

This directory contains all CI/CD automation and documentation for the Computer-Peripheral-App project.

## 📄 Files Overview

### Workflows
| File | Purpose |
|------|---------|
| **workflows/build-release.yml** | Main GitHub Actions workflow that builds Windows .exe and Android APK automatically on push to master |

### Documentation
| File | Purpose | When to Read |
|------|---------|--------------|
| **CHECKLIST.md** | Step-by-step testing checklist | 🟢 Start here! Verify setup |
| **QUICKSTART.md** | Quick reference guide | When you need a quick reminder |
| **ACTIONS_README.md** | Detailed technical documentation | When customizing the workflow |
| **AUTOMATION_SUMMARY.md** | Complete automation overview | For comprehensive understanding |
| **BADGES.md** | GitHub badges for README | When enhancing your README |

## 🚀 Quick Start

1. **Push to master branch:**
   ```powershell
   git add .
   git commit -m "Your changes"
   git push origin master
   ```

2. **Wait 10-15 minutes** for builds to complete

3. **Download executables:**
   - Actions tab → Artifacts (immediate)
   - Releases section (public downloads)

## 🎯 What Gets Built

Every push to `master` automatically creates:
- ✅ **RemoteMouseServer.exe** - Windows server executable (~15-25 MB)
- ✅ **app-debug.apk** - Android app debug build (~2-5 MB)
- ✅ **app-release-unsigned.apk** - Android app release build (~2-5 MB)

## 💰 Cost

- **Public repos:** FREE (unlimited builds)
- **Private repos:** 2,000 free minutes/month

## 📚 Documentation Flow

```
New to automation?
    ↓
CHECKLIST.md (Start here)
    ↓
QUICKSTART.md (Quick reference)
    ↓
Need to customize?
    ↓
ACTIONS_README.md (Technical details)
    ↓
Want the big picture?
    ↓
AUTOMATION_SUMMARY.md (Complete overview)
```

## 🔧 Workflow Structure

```yaml
build-release.yml
├── build-windows-server (Job 1)
│   ├── Setup Python 3.11
│   ├── Install dependencies
│   ├── Run PyInstaller
│   └── Upload .exe artifact
│
├── build-android-apk (Job 2)
│   ├── Setup JDK 17
│   ├── Setup Gradle
│   ├── Build debug & release APKs
│   └── Upload APK artifacts
│
└── create-release (Job 3)
    ├── Download all artifacts
    ├── Create GitHub Release
    └── Attach all files
```

## 🎯 Key Features

✅ Automatic builds on push to master
✅ Multi-platform support (Windows + Android)
✅ Both debug and release builds
✅ Automatic GitHub Releases
✅ 30-day artifact retention
✅ Detailed build logs
✅ Free for public repositories

## 🐛 Troubleshooting

**Build failed?**
→ Check Actions tab for logs

**Can't find executables?**
→ Wait for green checkmark, then check Releases

**Want to test locally?**
→ See QUICKSTART.md for local build commands

## 📞 Support

- Read: **CHECKLIST.md** for step-by-step guidance
- Review: **ACTIONS_README.md** for technical details
- Check: GitHub Actions tab for build logs

## 🎉 Success Criteria

Your automation works when:
- ✅ Workflow runs on push to master
- ✅ All jobs complete successfully
- ✅ Executables are available in Releases
- ✅ Files run without errors

---

**Ready to start?** Open **CHECKLIST.md** and follow the steps! 🚀

