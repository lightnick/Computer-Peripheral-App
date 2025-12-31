# Computer Peripheral App - Technical Documentation

## Project Overview

A remote mouse controller application that allows an Android device to control a PC's mouse and keyboard over a local network. The project consists of two main components:

1. **Android App** (Kotlin) - Touch interface that sends mouse/keyboard commands
2. **Python Server** - Receives commands and controls the PC's mouse/keyboard

## Architecture

### Communication Flow
```
Android App (UI) → Socket Connection → Python Server → PyAutoGUI → PC Input
                  ← Cursor View Feed ←
```

- **Protocol**: TCP socket communication on port 5000
- **Format**: Newline-delimited text commands
- **Bidirectional**: Server can send messages back to app (cursor view, textbox detection)

## Key Components

### Android App (`app/`)

#### Main Activity (`MainActivity.kt`)
- **Connection Management**: Establishes socket connection to server
- **Touch Handling**: Processes touchpad gestures and button presses
- **Cursor View**: Displays magnified view of cursor area from server
- **Keyboard Input**: Shows keyboard for text input when clicking in textboxes

#### Gesture Detection
- **Single Tap**: Quick left click (no keyboard detection)
- **Double Tap**: Double click
- **Three-finger Tap**: Middle click
- **Left Button Hold + Touchpad Move**: Drag operation
- **Scroll Wheel**: Vertical scrolling

#### UI Layout (`activity_main.xml`)
- **Mouse Buttons**: Left and right click buttons (no text labels)
- **Scroll Wheel**: Center area for scrolling
- **Touchpad**: Large area for cursor movement
- **Cursor View Overlay**: ImageView showing magnified cursor area
- **Connection UI**: Collapsible section for IP input (hidden when connected)

### Python Server (`server/`)

#### Server (`server.py`)

**Core Functionality**:
- Socket server listening on 0.0.0.0:5000
- Multi-threaded client handling
- System tray integration with notifications
- Real-time cursor position streaming

**Command Processing**:
- `move X,Y` - Move cursor relative to current position
- `click` - Single left click (from touchpad tap)
- `drag_start` - Start dragging (mouse down)
- `drag_move X,Y` - Move while dragging
- `drag_end` - End dragging (mouse up), checks for textbox focus
- `right_click` - Right click
- `middle_click` - Middle click
- `double_click` - Double click
- `scroll AMOUNT` - Scroll vertically
- `type CHAR` - Type a character
- `key NAME` - Press special key (backspace, enter)
- `cursor_view on/off` - Enable/disable cursor view streaming

**Movement Processing**:
- **Accumulator Pattern**: Batches rapid movement events for smooth control
- **Update Intervals**:
  - Mouse movement: 10ms (100Hz)
  - Drag movement: 10ms (100Hz)
  - Scroll: 100ms batching
- **Thread-safe**: Uses locks for shared state

**Cursor View**:
- Captures 400x400px area around cursor at 10 FPS
- Draws cursor indicator at actual cursor position
- Encodes as JPEG (50% quality) and base64
- Accounts for screen edge clamping

**Textbox Detection** (Windows):
- Checks window class names for text input fields
- Detects browsers, IDEs, text editors
- Sends `TEXTBOX_FOCUSED` message to trigger mobile keyboard

**System Tray**:
- Blue icon with white circle
- Menu options: "Show IP Address", "Exit"
- Shows Windows notifications with server IP
- Startup notification displays local IP address

## File Structure

```
Computer-Peripheral-App/
├── app/                           # Android application
│   ├── src/main/
│   │   ├── java/com/example/androidmouse/
│   │   │   └── MainActivity.kt    # Main app logic
│   │   └── res/
│   │       ├── layout/
│   │       │   └── activity_main.xml  # UI layout
│   │       └── drawable/
│   │           ├── mouse_button.xml   # Button styling
│   │           ├── scroll_wheel.xml   # Scroll wheel styling
│   │           └── touchpad_border.xml # Touchpad styling
│   ├── build.gradle
│   └── settings.gradle
├── server/                        # Python server
│   ├── server.py                  # Main server code
│   ├── requirements.txt           # Python dependencies
│   └── venv/                      # Virtual environment
├── README.md                      # User documentation
└── CLAUDE.MD                      # This file
```

## Setup & Installation

### Server Setup (Windows PC)
```bash
cd server
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

### Android App Setup
1. Open project in Android Studio
2. Build and install APK on Android device
3. Connect Android device to same network as PC
4. Enter server IP address shown in notification/console

## Technical Details

### Threading Model (Server)

1. **Main Thread**: Socket accept loop
2. **Client Threads**: One per connected client, handles commands
3. **Move Worker Thread**: Processes accumulated movements at 100Hz
4. **Cursor View Thread**: Captures and streams cursor area at 10 FPS
5. **System Tray Thread**: Runs tray icon event loop

### State Management

**Server Global State**:
- `connected_clients` - List of active socket connections
- `move_accumulator` - Buffered X,Y deltas for mouse movement
- `drag_accumulator` - Buffered X,Y deltas for drag movement
- `scroll_accumulator` - Buffered scroll amount
- `is_dragging` - Boolean drag state
- `cursor_view_enabled` - Boolean for cursor streaming
- `last_click_times` - Debounce timestamps for clicks

**Android State**:
- `socket` - TCP socket connection
- `outputStream` - Output stream for sending commands
- `isLeftButtonPressed` - Drag state controlled by left button
- `isUpdatingKeyboardText` - Flag to prevent TextWatcher loops

### Network Protocol

**Command Format**: `COMMAND [ARGS]\n`

**Examples**:
```
move 10,20\n
drag_start\n
drag_move 5,3\n
drag_end\n
click\n
right_click\n
scroll -50\n
type a\n
key backspace\n
cursor_view on\n
```

**Server → Client Messages**:
```
TEXTBOX_FOCUSED\n
CURSOR_VIEW <base64_jpeg_data>\n
```

### UI Design Philosophy

**Android App**:
- Minimal interface resembling a real mouse
- No text labels on mouse buttons (clean look)
- Rounded corners and elevation for depth
- Connection UI hidden when connected
- Gear icon (⚙) for accessing settings

**Color Scheme**:
- Background: #FAFAFA (light gray)
- Mouse buttons: #EEEEEE (lighter gray)
- Scroll wheel: #9E9E9E (medium gray)
- Touchpad: #E8E8E8 (very light gray)
- Borders: #BDBDBD, #CCCCCC (gray variants)

## Dependencies

### Python Server
- `pyautogui` - Mouse/keyboard control
- `pillow` - Image processing
- `pystray` - System tray integration
- `pywin32` - Windows API access (textbox detection)

### Android App
- Kotlin standard library
- Android SDK (minimum API level varies)
- Material Design components

## Known Behaviors

1. **Edge Clamping**: Cursor view correctly handles screen edges by calculating actual cursor position in captured image
2. **Keyboard Auto-show**: Mobile keyboard appears when clicking in detected textboxes (Windows only)
3. **Debouncing**: Click events debounced at 100ms to prevent duplicates
4. **Smooth Movement**: Accumulator pattern ensures smooth cursor movement even with rapid touchpad events
5. **Connection State**: Connection UI auto-hides on successful connection

## Future Enhancement Ideas

- Multi-monitor support indication
- Custom cursor themes
- Gesture customization
- Connection history/favorites
- Screen mirroring option
- Audio feedback for clicks
- Haptic feedback on Android

## Development Notes

### Modifying Commands
1. Add command handler in `handle_command()` function
2. Update Android app to send new command format
3. Test with single client first
4. Consider thread safety if accessing shared state

### Adding UI Elements
1. Update `activity_main.xml` for layout changes
2. Create drawable resources for custom styling
3. Initialize views in `onCreate()`
4. Set up event listeners
5. Update `MainActivity.kt` with new logic

### Debugging Tips
- Server prints all received commands to console
- Use `[DEBUG]` prefix for debug logs
- Check Windows notifications for server status
- Monitor Android logcat for connection issues
- Verify port 5000 is not blocked by firewall

## Security Considerations

- Server binds to 0.0.0.0 (all interfaces) - only use on trusted networks
- No authentication mechanism - anyone on network can connect
- Commands executed with server process privileges
- Recommend: Use on private home network only

## Performance Optimization

1. **JPEG Quality**: Set to 50% for cursor view to reduce bandwidth
2. **Update Rate**: 10 FPS for cursor view balances smoothness and performance
3. **Batch Processing**: Movement accumulator prevents command flood
4. **Thread Pooling**: One thread per client, reused connections
5. **Image Size**: 400x400px cursor view optimized for touchpad display

---

**Last Updated**: 2026-01-01
**Version**: 1.0
**Maintained by**: User + Claude
