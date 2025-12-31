# GitHub Actions CI/CD Setup

This project uses GitHub Actions to automatically build executables when code is pushed to the master branch.

## What Gets Built

When you push or merge to the `master` branch, the workflow automatically builds:

1. **Windows Server Executable** (`RemoteMouseServer.exe`)
   - Built from `server/server.py`
   - Uses PyInstaller to create a standalone .exe
   - Includes all dependencies (pyautogui, pystray, PIL, win32 libraries)

2. **Android APK** (`app-debug.apk` and `app-release-unsigned.apk`)
   - Built from the Android app source
   - Both debug and release versions are created

## How It Works

The workflow (`.github/workflows/build-release.yml`) runs three jobs:

1. **build-windows-server**: Builds the Windows executable on a Windows runner
2. **build-android-apk**: Builds the Android APK on an Ubuntu runner
3. **create-release**: Creates a GitHub Release with all artifacts attached

## Viewing Build Results

After pushing to master:

1. Go to the **Actions** tab in your GitHub repository
2. Click on the latest workflow run
3. View the build logs for each job
4. Download artifacts from the workflow summary page
5. Automatic releases are created under the **Releases** section

## GitHub Actions Usage (Free Tier)

- **Public repositories**: Unlimited minutes ✅
- **Private repositories**: 2,000 minutes/month free
  - Windows runners consume 2x minutes (1 real minute = 2 billed minutes)
  - Linux runners consume 1x minutes

## Local Testing

### Build Windows Server Locally

```powershell
cd server
pip install -r requirements.txt
pip install pyinstaller
pyinstaller server.spec
# Output: dist/RemoteMouseServer.exe
```

### Build Android APK Locally

```powershell
# If you have Android SDK and Gradle installed:
./gradlew assembleDebug
# Output: app/build/outputs/apk/debug/app-debug.apk
```

## Setting Up Gradle Wrapper (Optional)

If the `gradlew` and `gradlew.bat` files are missing, the workflow will still work using the gradle-build-action. However, to add the wrapper locally:

1. Install Gradle on your system
2. Run: `gradle wrapper --gradle-version=7.5`
3. Commit the generated `gradlew`, `gradlew.bat`, and `gradle/wrapper/` files

## Customization

### Change Release Naming

Edit `.github/workflows/build-release.yml` and modify the `tag_name` and `name` fields in the `create-release` job.

### Build on Different Branches

Change the `branches` section in the workflow:

```yaml
on:
  push:
    branches:
      - master
      - main
      - develop
```

### Sign Android APK

To create a signed release APK:

1. Generate a keystore file
2. Add keystore as a GitHub secret
3. Update the workflow to sign the APK during build

## Troubleshooting

### Windows Executable Issues
- If the .exe doesn't run, check Windows Defender SmartScreen
- Missing DLLs: ensure all dependencies are in `requirements.txt`
- Icon missing: add `icon.ico` to the `server/` folder

### Android Build Issues
- Gradle version compatibility: check `gradle/wrapper/gradle-wrapper.properties`
- SDK version: ensure `compileSdk` matches your environment
- Missing permissions: check `AndroidManifest.xml`

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [Android Gradle Plugin](https://developer.android.com/studio/releases/gradle-plugin)

