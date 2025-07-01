import asyncio
import websockets
import json
from io import BytesIO
from PIL import Image
import mss
import pygetwindow as gw
import pyautogui
import os
import socket
import psutil
import base64
import webbrowser  # ### NEW: For opening URLs
import pyperclip   # ### NEW: For clipboard control

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 8765
JPEG_QUALITY = 75
UPLOAD_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')

connected_clients = set()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

async def execute_command(command, payload=None):
    """Handles system commands, now with expanded functionality."""
    print(f"Executing command: {command} with payload: {payload}")
    try:
        # Media Controls
        if command in ["play_pause", "next_track", "prev_track", "volume_up", "volume_down", "mute"]:
            pyautogui.press(command.replace('_', ''))
        # Power Controls
        elif command == "lock":
            if os.name == 'nt': os.system("rundll32.exe user32.dll,LockWorkStation")
        elif command == "restart":
            if os.name == 'nt': os.system('shutdown /r /t 1')
            else: os.system('shutdown -r now')
        elif command == "shutdown":
            if os.name == 'nt': os.system('shutdown /s /t 1')
            else: os.system('shutdown -h now')
        # Text Input
        elif command == "type_text" and payload:
            pyautogui.typewrite(payload, interval=0.01)

        # ### NEW: Mouse Click from Screenshot ###
        elif command == "mouse_click" and payload:
            screen_width, screen_height = pyautogui.size()
            click_x = int(screen_width * payload['x'])
            click_y = int(screen_height * payload['y'])
            pyautogui.click(click_x, click_y)
            return {"type": "command_response", "message": f"Clicked at ({click_x}, {click_y})"}

        # ### NEW: Open URL ###
        elif command == "open_url" and payload:
            webbrowser.open(payload)
            return {"type": "command_response", "message": "URL opened"}

        # ### NEW: Clipboard Control ###
        elif command == "set_clipboard" and payload:
            pyperclip.copy(payload)
            return {"type": "command_response", "message": "PC clipboard set"}
        elif command == "get_clipboard":
            clipboard_content = pyperclip.paste()
            # This command needs a special response with the data
            return {"type": "clipboard_content", "content": clipboard_content}

        else:
            print(f"Unknown command or missing payload: {command}")
        
        # Default success response for commands that don't have a custom one
        return {"type": "command_response", "message": f"Executed '{command}'"}

    except Exception as e:
        print(f"Error executing command '{command}': {e}")
        return {"type": "command_response", "message": f"Error on '{command}'", "status": "error"}

async def handle_client(websocket):
    """Handles a single client connection."""
    connected_clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}. Total clients: {len(connected_clients)}")
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'command':
                # Execute command and get a response message to send back
                response_message = await execute_command(data.get('command'), data.get('payload'))
                if response_message:
                    await websocket.send(json.dumps(response_message))

            elif msg_type == 'file_upload':
                # ... (file upload logic remains the same)
                try:
                    filename = data.get('filename', 'uploaded_file')
                    safe_filename = os.path.basename(filename)
                    save_path = os.path.join(UPLOAD_PATH, safe_filename)
                    file_bytes = base64.b64decode(data.get('filedata'))
                    with open(save_path, 'wb') as f:
                        f.write(file_bytes)
                    print(f"File '{safe_filename}' uploaded successfully to Desktop.")
                    response = {"type": "command_response", "message": f"Uploaded '{safe_filename}' successfully!"}
                    await websocket.send(json.dumps(response))
                except Exception as e:
                    print(f"File upload failed: {e}")
                    response = {"type": "command_response", "message": "File upload failed."}
                    await websocket.send(json.dumps(response))

    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        connected_clients.remove(websocket)
        print(f"Total clients remaining: {len(connected_clients)}")

async def broadcast_data():
    """Periodically captures and broadcasts all system data."""
    with mss.mss() as sct:
        while True:
            await asyncio.sleep(1) # Broadcast data once per second
            if not connected_clients:
                continue

            # 1. Capture Screenshot
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=JPEG_QUALITY)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            screenshot_data = {"type": "screenshot", "image": img_base64}

            # 2. Get Window List
            try:
                all_windows = gw.getAllTitles()
                visible_windows = [title for title in all_windows if title]
                windows_data = {"type": "windows", "windows": visible_windows}
            except Exception:
                windows_data = {"type": "windows", "windows": []}

            # 3. Get System Stats (CPU, RAM, and ### NEW: Disk/Battery ###)
            stats_data = {
                "type": "stats",
                "cpu": psutil.cpu_percent(),
                "ram": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage('/').percent,
                "battery": None # Default to None
            }
            battery = psutil.sensors_battery()
            if battery:
                stats_data["battery"] = {
                    "percent": battery.percent,
                    "charging": battery.power_plugged
                }
            
            # 4. Broadcast all data types to clients
            all_data = [screenshot_data, windows_data, stats_data]
            tasks = [
                asyncio.create_task(client.send(json.dumps(d)))
                for client in connected_clients
                for d in all_data
            ]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    server = await websockets.serve(handle_client, HOST, PORT, max_size=20_000_000) # Increased max size
    print(f"🚀 PC-Pilot Pro Server is running on ws://{get_local_ip()}:{PORT}")
    broadcaster_task = asyncio.create_task(broadcast_data())
    await server.wait_closed()
    await broadcaster_task

if __name__ == "__main__":
    try:
        print("To start, run this command in a NEW terminal in this folder:")
        print("python -m http.server")
        print(f"Then open http://{get_local_ip()}:8000 on your phone.")
        print("--------------------------------------------------")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down.")
