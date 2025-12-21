# python
import socket
import threading
import time
import pyautogui

pyautogui.FAILSAFE = False

HOST = "0.0.0.0"
PORT = 5000
stop_event = threading.Event()
threads = []

# --- Accumulator for smooth mouse movements ---
move_accumulator = [0, 0]
move_lock = threading.Lock()

# --- Debounce for scroll events ---
last_scroll_time = 0
SCROLL_DEBOUNCE_INTERVAL = 0.05  # 50ms

def move_worker():
    """Applies accumulated mouse movements at a regular interval."""
    while not stop_event.is_set():
        time.sleep(0.01)  # 10ms update interval (100Hz)
        with move_lock:
            dx, dy = move_accumulator
            move_accumulator[0] = 0
            move_accumulator[1] = 0

        if dx != 0 or dy != 0:
            pyautogui.moveRel(dx, dy)
            print(f"Cursor at: {pyautogui.position()}")

def handle_command(cmd: str):
    global last_scroll_time
    cmd = cmd.strip()
    if not cmd:
        return

    parts = cmd.split(None, 1)
    command = parts[0]
    args = parts[1] if len(parts) > 1 else None

    try:
        if command == "left_click":
            pyautogui.click()
        elif command == "right_click":
            pyautogui.click(button="right")
        elif command == "double_click":
            pyautogui.doubleClick()
        elif command == "scroll":
            current_time = time.time()
            if args and (current_time - last_scroll_time > SCROLL_DEBOUNCE_INTERVAL):
                last_scroll_time = current_time
                try:
                    # PyAutoGUI's scroll is inverted on some systems, so we multiply by -1
                    # A positive amount from the app will scroll down.
                    amount = int(args) * -1
                    pyautogui.scroll(amount)
                    print(f"Scrolled by: {amount}")
                except ValueError:
                    print(f"Invalid scroll amount: {args}")
        elif command == "move" or command == "move_rel":
            if args:
                dx_str, dy_str = args.split(",", 1)
                dx, dy = int(dx_str), int(dy_str)
                with move_lock:
                    move_accumulator[0] += dx
                    move_accumulator[1] += dy
        elif command == "shutdown":
            stop_event.set()
            print("Shutdown command received")
        else:
            print(f"Unknown command: {cmd}")
    except Exception as e:
        print("Error handling command:", cmd, "-", e)

def client_thread(conn, addr):
    print("Connected by", addr)
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
        print("Disconnected", addr)

def main():
    global threads
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

        print(f"Server listening on {HOST}:{PORT}")
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
