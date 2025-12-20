# Android-Mouse

## How the Project Works
1. The Android app captures touch gestures and sends them as commands to the Python server.
2. The server receives these commands and simulates mouse actions on the connected Windows PC.
3. A wireless connection using sockets is established between the Android device and the server.

## Starting the Server
1. Navigate to the `server` directory in your terminal.
2. Ensure Python 3 is installed on your machine.
3. Install dependencies: `pip install pyautogui`.
4. Run the server with: `python server.py`.

This process starts the server listening for commands on port 5000 from the Android app for controlling your mouse.