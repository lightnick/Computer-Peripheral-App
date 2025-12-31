# Computer-Peripheral-App

## 🚀 Quick Download (Pre-built Executables)

**Don't want to build from source?** Download ready-to-use executables:

1. Go to [Releases](../../releases) (right sidebar on GitHub)
2. Download the latest release:
   - `RemoteMouseServer.exe` - Windows server (no installation needed!)
   - `app-debug.apk` - Android app

Executables are automatically built and released when code is pushed to master.

---

## How the Project Works
1. The Android app captures touch gestures and sends them as commands to the Python server.
2. The server receives these commands and simulates mouse actions on the connected Windows PC.
3. A wireless connection using sockets is established between the Android device and the server.

## Starting the Server

### First Time Setup
1. Navigate to the `server` directory in your terminal.
2. Ensure Python 3 is installed on your machine.
3. Create a virtual environment (recommended):
   ```bash
   # Windows
   py -m venv venv

   # macOS/Linux
   python3 -m venv venv
   ```
4. Activate the virtual environment:
   ```bash
   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Server
1. Make sure you're in the `server` directory and the virtual environment is activated.
2. Run the server:
   ```bash
   python server.py
   ```

The server will start listening for commands on port 5000 from the Android app for controlling your mouse.

### Supported Gestures
- **Move**: Move cursor relative to current position
- **Left Click**: Single tap
- **Right Click**: Two-finger tap or long press
- **Middle Click**: Three-finger tap
- **Double Click**: Double tap
- **Scroll**: Two-finger swipe up/down
- **Drag**: Touch and hold, then move (for dragging windows/files)

## 🤖 Automated Builds

This project uses GitHub Actions for CI/CD. Every push to the `master` branch automatically:
- ✅ Builds the Windows server executable
- ✅ Builds the Android APK (debug & release)
- ✅ Creates a GitHub Release with all artifacts

**For developers:** See [`.github/QUICKSTART.md`](.github/QUICKSTART.md) for details on the automation setup.

**Build Status:** Check the [Actions tab](../../actions) to see the latest build results.
