# python
import socket
import threading
import pyautogui

pyautogui.FAILSAFE = False

HOST = "0.0.0.0"
PORT = 5000
stop_event = threading.Event()
threads = []

def handle_command(cmd: str):
    cmd = cmd.strip()
    if not cmd:
        return
    try:
        if cmd == "left_click":
            pyautogui.click()
        elif cmd == "right_click":
            pyautogui.click(button="right")
        elif cmd == "double_click":
            pyautogui.doubleClick()
        elif cmd.startswith("move "):
            x_str, y_str = cmd[len("move "):].split(",", 1)
            x, y = int(x_str), int(y_str)
            pyautogui.moveTo(x, y)
        elif cmd.startswith("move_rel "):
            dx_str, dy_str = cmd[len("move_rel "):].split(",", 1)
            dx, dy = int(dx_str), int(dy_str)
            pyautogui.moveRel(dx, dy)
        elif cmd == "shutdown":
            stop_event.set()
            print("Shutdown command received")
        else:
            print("Unknown command:", cmd)
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
