# python
import socket
import threading
import time
import pyautogui
import base64
from io import BytesIO
from PIL import Image, ImageDraw
import pystray
from PIL import Image as PILImage

try:
    import win32gui
    import win32con
    import win32api
    import winreg
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    print("Warning: win32gui not available, textbox detection disabled")

pyautogui.FAILSAFE = False

HOST = "0.0.0.0"
PORT = 5000
stop_event = threading.Event()
threads = []

# --- Client connections for bidirectional communication ---
connected_clients = []
clients_lock = threading.Lock()

# --- Accumulator for smooth mouse movements ---
move_accumulator = [0, 0]
move_lock = threading.Lock()

# --- Accumulator for drag movements ---
drag_accumulator = [0, 0]
drag_accumulator_lock = threading.Lock()

# --- Scroll accumulator for smooth scrolling ---
scroll_accumulator = 0
scroll_accumulator_lock = threading.Lock()
last_scroll_process_time = 0
SCROLL_PROCESS_INTERVAL = 0.1  # 100ms - process accumulated scroll events

# --- Debounce for click events ---
last_click_times = {
    "left_click": 0,
    "right_click": 0,
    "middle_click": 0,
    "double_click": 0,
    "long_press": 0
}
CLICK_DEBOUNCE_INTERVAL = 0.1  # 100ms - prevents duplicate clicks
click_lock = threading.Lock()

# --- Drag state tracking ---
is_dragging = False
drag_lock = threading.Lock()

# --- Cursor view settings ---
CURSOR_VIEW_SIZE = 400  # Size of the area to capture around cursor (larger for full touchpad display)
CURSOR_VIEW_FPS = 10  # Updates per second
cursor_view_enabled = False
cursor_view_lock = threading.Lock()


def get_virtual_screen_bounds():
    """Get the virtual screen bounds that span all monitors.

    Returns:
        tuple: (left, top, width, height) of the virtual screen
    """
    if WINDOWS_AVAILABLE:
        try:
            # SM_XVIRTUALSCREEN (76) - left of virtual screen
            # SM_YVIRTUALSCREEN (77) - top of virtual screen
            # SM_CXVIRTUALSCREEN (78) - width of virtual screen
            # SM_CYVIRTUALSCREEN (79) - height of virtual screen
            virtual_left = win32api.GetSystemMetrics(76)
            virtual_top = win32api.GetSystemMetrics(77)
            virtual_width = win32api.GetSystemMetrics(78)
            virtual_height = win32api.GetSystemMetrics(79)
            return (virtual_left, virtual_top, virtual_width, virtual_height)
        except (AttributeError, OSError) as e:
            print(f"[DEBUG] Failed to get virtual screen bounds: {e}")

    # Fallback to primary monitor only
    screen_width, screen_height = pyautogui.size()
    return (0, 0, screen_width, screen_height)


def capture_cursor_area():
    """Capture area around cursor with cursor indicator and return as base64 JPEG."""
    try:
        # Get cursor position and virtual screen bounds (all monitors)
        x, y = pyautogui.position()
        virtual_left, virtual_top, virtual_width, virtual_height = get_virtual_screen_bounds()

        # Calculate the right and bottom edges of the virtual screen
        virtual_right = virtual_left + virtual_width
        virtual_bottom = virtual_top + virtual_height

        # Determine actual capture size (may be smaller than CURSOR_VIEW_SIZE if screen is tiny)
        capture_width = min(CURSOR_VIEW_SIZE, virtual_width)
        capture_height = min(CURSOR_VIEW_SIZE, virtual_height)

        # Calculate capture region
        half_width = capture_width // 2
        half_height = capture_height // 2
        left = x - half_width
        top = y - half_height

        # Ensure we don't go beyond virtual screen bounds
        if left < virtual_left:
            left = virtual_left
        if top < virtual_top:
            top = virtual_top
        if left + capture_width > virtual_right:
            left = virtual_right - capture_width
        if top + capture_height > virtual_bottom:
            top = virtual_bottom - capture_height

        # Make sure left and top are still valid after adjustment
        left = max(virtual_left, left)
        top = max(virtual_top, top)

        # Capture screenshot
        screenshot = pyautogui.screenshot(region=(left, top, capture_width, capture_height))

        # Calculate where the cursor actually is in the captured image
        # (not necessarily the center due to edge clamping)
        cursor_x = x - left
        cursor_y = y - top

        # Draw cursor indicator at the actual cursor position
        draw = ImageDraw.Draw(screenshot)

        # Draw a proper Windows-style arrow cursor
        # Main arrow shape (pointing up-left)
        arrow_points = [
            (cursor_x, cursor_y),           # Tip
            (cursor_x, cursor_y + 16),      # Left shaft bottom
            (cursor_x + 5, cursor_y + 13),  # Left inner corner
            (cursor_x + 8, cursor_y + 20),  # Bottom left of tail
            (cursor_x + 10, cursor_y + 18), # Bottom right of tail
            (cursor_x + 7, cursor_y + 11),  # Right inner corner
            (cursor_x + 11, cursor_y + 11), # Right shaft
            (cursor_x, cursor_y)            # Back to tip
        ]

        # Draw black outline (2px border)
        outline_offset = 1
        outline_points = [(px - outline_offset, py - outline_offset) for px, py in arrow_points]
        draw.polygon(outline_points, fill='black')
        outline_points = [(px + outline_offset, py + outline_offset) for px, py in arrow_points]
        draw.polygon(outline_points, fill='black')

        # Draw white cursor
        draw.polygon(arrow_points, fill='white', outline='black')

        # Convert to JPEG and encode to base64
        buffer = BytesIO()
        screenshot.save(buffer, format='JPEG', quality=50, optimize=True)
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        return img_base64
    except Exception as e:
        print(f"[ERROR] Failed to capture cursor area: {e}")
        return None

def cursor_view_worker():
    """Continuously capture and send cursor area to clients."""
    global cursor_view_enabled
    interval = 1.0 / CURSOR_VIEW_FPS

    while not stop_event.is_set():
        with cursor_view_lock:
            enabled = cursor_view_enabled

        if enabled:
            img_data = capture_cursor_area()
            if img_data:
                notify_clients(f"CURSOR_VIEW {img_data}")

        time.sleep(interval)

def is_text_input_focused():
    """Check if the currently focused window is a text input field."""
    if not WINDOWS_AVAILABLE:
        return False

    try:
        # Get the currently focused window
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return False

        # Get window class name and title
        class_name = win32gui.GetClassName(hwnd)
        window_title = win32gui.GetWindowText(hwnd)

        print(f"[DEBUG] Focused window: Class='{class_name}', Title='{window_title}'")

        # Common text input class names (expanded list)
        text_input_classes = [
            'Edit',  # Standard text box
            'RichEdit',  # Rich text editor
            'RichEdit20',
            'RICHEDIT50W',
            'RichEdit60W',
            'TextBox',
            'ConsoleWindowClass',  # Command prompt/PowerShell
            'CabinetWClass',  # Windows Explorer (for rename)
            'Notepad',
            'WordPadClass',
            'OpusApp',  # Microsoft Word
            'XLMAIN',  # Microsoft Excel
            'ThunderRT6FormDC',  # VB apps
            'SunAwtFrame',  # Java apps
            'Chrome_WidgetWin',  # Chrome input fields
            'MozillaWindowClass',  # Firefox
        ]

        # Check if it's a known text input class
        for text_class in text_input_classes:
            if text_class.lower() in class_name.lower():
                print(f"[DEBUG] ✓ Matched text input class: {text_class}")
                return True

        # Browser detection - be more aggressive
        browsers = ['Chrome', 'Firefox', 'Edge', 'Safari', 'Opera', 'Brave', 'Vivaldi']
        for browser in browsers:
            if browser.lower() in window_title.lower() or browser.lower() in class_name.lower():
                print(f"[DEBUG] ✓ Browser detected: {browser}")
                # For browsers, assume text input is possible
                return True

        # IDE and code editor detection
        editors = ['Visual Studio', 'VS Code', 'Sublime', 'Atom', 'Notepad++', 'IntelliJ',
                   'PyCharm', 'WebStorm', 'Eclipse']
        for editor in editors:
            if editor.lower() in window_title.lower():
                print(f"[DEBUG] ✓ Editor detected: {editor}")
                return True

        print(f"[DEBUG] ✗ No text input detected")
        return False
    except Exception as e:
        print(f"[ERROR] Error checking focused window: {e}")
        return False

def notify_clients(message):
    """Send a message to all connected clients."""
    with clients_lock:
        for client in connected_clients[:]:  # Copy list to avoid modification during iteration
            try:
                client.send((message + "\n").encode('utf-8'))
            except Exception as e:
                print(f"Error sending to client: {e}")
                # Remove disconnected client
                if client in connected_clients:
                    connected_clients.remove(client)

def move_worker():
    """Applies accumulated mouse movements and scroll events at a regular interval."""
    global last_scroll_process_time, scroll_accumulator
    while not stop_event.is_set():
        time.sleep(0.01)  # 10ms update interval (100Hz)
        current_time = time.time()

        # Process normal movements
        with move_lock:
            dx, dy = move_accumulator
            move_accumulator[0] = 0
            move_accumulator[1] = 0

        # Process drag movements
        with drag_accumulator_lock:
            drag_dx, drag_dy = drag_accumulator
            drag_accumulator[0] = 0
            drag_accumulator[1] = 0

        # Process scroll events (less frequently)
        scroll_amount = 0
        if current_time - last_scroll_process_time > SCROLL_PROCESS_INTERVAL:
            with scroll_accumulator_lock:
                scroll_amount = scroll_accumulator
                scroll_accumulator = 0
            if scroll_amount != 0:
                last_scroll_process_time = current_time

        # Execute movements
        if dx != 0 or dy != 0:
            pyautogui.moveRel(dx, dy)
            print(f"Cursor at: {pyautogui.position()}")

        if drag_dx != 0 or drag_dy != 0:
            pyautogui.moveRel(drag_dx, drag_dy)
            print(f"Dragging: moved ({drag_dx}, {drag_dy})")

        if scroll_amount != 0:
            pyautogui.scroll(scroll_amount)
            print(f"Scrolled by: {scroll_amount}")

def handle_command(cmd: str):
    global is_dragging, scroll_accumulator
    cmd = cmd.strip()
    if not cmd:
        return

    parts = cmd.split(None, 1)
    command = parts[0]
    args = parts[1] if len(parts) > 1 else None

    try:
        # Handle click events with debouncing
        if command in last_click_times:
            current_time = time.time()
            with click_lock:
                if current_time - last_click_times[command] > CLICK_DEBOUNCE_INTERVAL:
                    last_click_times[command] = current_time

                    if command == "left_click":
                        pyautogui.click()
                        print("Left click")
                    elif command == "right_click":
                        pyautogui.click(button="right")
                        print("Right click")
                    elif command == "middle_click":
                        pyautogui.click(button="middle")
                        print("Middle click")
                    elif command == "double_click":
                        pyautogui.doubleClick()
                        print("Double click")
                    elif command == "long_press":
                        pyautogui.click(button="right")
                        print("Long press (right click)")
                else:
                    # Silently ignore duplicate clicks within debounce interval
                    pass
        elif command == "click":
            # Simple click from touchpad tap (no keyboard detection)
            pyautogui.click()
            print("Click (touchpad tap)")
        elif command == "drag_start":
            with drag_lock:
                # Only start drag if not already dragging
                if not is_dragging:
                    pyautogui.mouseDown()
                    is_dragging = True
                    print("Mouse down")

        elif command == "drag_move":
            if is_dragging and args:
                try:
                    dx_str, dy_str = args.split(",", 1)
                    dx, dy = int(dx_str), int(dy_str)
                    with drag_accumulator_lock:
                        drag_accumulator[0] += dx
                        drag_accumulator[1] += dy
                except ValueError:
                    print(f"Invalid drag_move coordinates: {args}")

        elif command == "drag_end":
            with drag_lock:
                # Only end drag if currently dragging
                if is_dragging:
                    pyautogui.mouseUp()
                    is_dragging = False
                    print("Mouse up")

            # Check if a text input is now focused (after click)
            # Run in separate thread to not block command processing
            def check_text_input():
                time.sleep(0.15)  # Increased delay to let focus change
                print("[DEBUG] Checking for text input after click...")
                if is_text_input_focused():
                    notify_clients("TEXTBOX_FOCUSED")
                    print("[INFO] ✓ Text input focused - keyboard notification sent")
                else:
                    print("[DEBUG] No text input detected after click")

            threading.Thread(target=check_text_input, daemon=True).start()
        elif command == "scroll":
            if args:
                try:
                    # PyAutoGUI's scroll is inverted on some systems, so we multiply by -1
                    # A positive amount from the app will scroll down.
                    amount = int(args) * -1
                    with scroll_accumulator_lock:
                        scroll_accumulator += amount
                except ValueError:
                    print(f"Invalid scroll amount: {args}")
        elif command == "move" or command == "move_rel":
            if args:
                dx_str, dy_str = args.split(",", 1)
                dx, dy = int(dx_str), int(dy_str)
                with move_lock:
                    move_accumulator[0] += dx
                    move_accumulator[1] += dy
        elif command == "type":
            # Type a character
            if args:
                try:
                    pyautogui.write(args, interval=0.0)
                    print(f"Typed: {args}")
                except Exception as e:
                    print(f"Error typing character: {e}")

        elif command == "key":
            # Press a special key (backspace, enter, etc.)
            if args:
                try:
                    key_name = args.strip().lower()
                    pyautogui.press(key_name)
                    print(f"Pressed key: {key_name}")
                except Exception as e:
                    print(f"Error pressing key: {e}")

        elif command == "cursor_view":
            # Enable/disable cursor view
            global cursor_view_enabled
            if args:
                with cursor_view_lock:
                    cursor_view_enabled = args.strip().lower() == "on"
                    status = "enabled" if cursor_view_enabled else "disabled"
                    print(f"Cursor view {status}")

        elif command == "shutdown":
            stop_event.set()
            print("Shutdown command received")
        else:
            print(f"Unknown command: {cmd}")
    except Exception as e:
        print("Error handling command:", cmd, "-", e)

def client_thread(conn, addr):
    print("Connected by", addr)

    # Add client to connected clients list for bidirectional communication
    with clients_lock:
        connected_clients.append(conn)

    try:
        with conn:
            buffer = b""
            while not stop_event.is_set():
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    try:
                        handle_command(line.decode("utf-8", errors="replace"))
                    except Exception as e:
                        print("Command processing error:", e)
    except Exception as e:
        print("Connection error with", addr, "-", e)
    finally:
        # Remove client from connected clients list
        with clients_lock:
            if conn in connected_clients:
                connected_clients.remove(conn)
        print("Disconnected", addr)

def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to a public DNS server (doesn't actually send data)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # Fallback to hostname resolution
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def create_tray_icon():
    """Create a system tray icon for the server."""
    # Create a simple icon (white circle on colored background)
    icon_size = 64
    icon_image = PILImage.new('RGB', (icon_size, icon_size), color='#2196F3')
    draw = ImageDraw.Draw(icon_image)

    # Draw a mouse cursor shape
    draw.ellipse([16, 16, 48, 48], fill='white')

    def show_ip(icon, item):
        """Show IP address in a system notification."""
        ip = get_local_ip()
        message = f"Server IP: {ip}\nConnect from your Android app using this IP address"
        icon.notify(message, "Remote Mouse Server")
        # Also print to console
        print(f"\n{'='*50}")
        print(f"Server IP Address: {ip}:{PORT}")
        print(f"Connect from your Android app using this IP")
        print(f"{'='*50}\n")

    def exit_server(icon, item):
        """Exit the server."""
        print("\nShutting down from system tray...")
        stop_event.set()
        icon.stop()

    # Create menu
    menu = pystray.Menu(
        pystray.MenuItem("Show IP Address", show_ip),
        pystray.MenuItem("Exit", exit_server)
    )

    # Create icon
    icon = pystray.Icon(
        "mouse_server",
        icon_image,
        "Mouse Server",
        menu
    )

    return icon

def main():
    global threads

    # Get and display local IP
    local_ip = get_local_ip()
    print(f"\n{'='*60}")
    print(f"  Remote Mouse Server")
    print(f"{'='*60}")
    print(f"  Server IP Address: {local_ip}:{PORT}")
    print(f"  Use this IP address in your Android app to connect")
    print(f"{'='*60}\n")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        server.settimeout(1.0)  # check stop_event periodically

        # Start the background thread for processing mouse movements
        move_processing_thread = threading.Thread(target=move_worker, daemon=True)
        move_processing_thread.start()
        threads.append(move_processing_thread)

        # Start the cursor view thread
        cursor_view_thread = threading.Thread(target=cursor_view_worker, daemon=True)
        cursor_view_thread.start()
        threads.append(cursor_view_thread)

        # Start system tray icon
        tray_icon = create_tray_icon()
        tray_thread = threading.Thread(target=tray_icon.run, daemon=False)
        tray_thread.start()
        threads.append(tray_thread)

        print(f"Server listening on {HOST}:{PORT}")
        print("Cursor view available (send 'cursor_view on' to enable)")
        print("System tray icon active - right-click to see options")

        # Show startup notification with IP address
        time.sleep(0.5)  # Give tray icon time to initialize
        tray_icon.notify(
            f"Server IP: {local_ip}\nReady to accept connections",
            "Remote Mouse Server Started"
        )
        try:
            while not stop_event.is_set():
                try:
                    conn, addr = server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                t = threading.Thread(target=client_thread, args=(conn, addr), daemon=True)
                t.start()
                threads.append(t)
        except KeyboardInterrupt:
            print("KeyboardInterrupt received, shutting down")
            stop_event.set()
    finally:
        try:
            server.close()
        except Exception:
            pass
        # give client threads a moment to finish
        for t in threads:
            t.join(timeout=0.5)
        print("Server stopped")

if __name__ == "__main__":
    main()
