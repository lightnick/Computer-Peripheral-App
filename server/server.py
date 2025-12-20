import socket
import pyautogui

def handle_command(command):
    if command == 'left_click':
        pyautogui.click()
    elif command == 'right_click':
        pyautogui.click(button='right')
    else:
        try:
            x, y = map(int, command.split(","))
            pyautogui.moveTo(x, y)
        except ValueError:
            print("Unknown command:", command)

def main():
    host = '0.0.0.0'
    port = 5000

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((host, port))
        server.listen(1)
        print(f"Server listening on {host}:{port}")

        conn, addr = server.accept()
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                handle_command(data.decode('utf-8'))

if __name__ == "__main__":
    main()