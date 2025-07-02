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
import webbrowser
import pyperclip
from pathlib import Path
from plyer import notification
import datetime
import platform
import time

# NEW: Import aiohttp for serving the HTML file
from aiohttp import web

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 8765 # We will use this port for EVERYTHING now
JPEG_QUALITY = 75
HOME_DIR = str(Path.home())
UPLOAD_PATH = os.path.join(HOME_DIR, 'Desktop')
os.makedirs(UPLOAD_PATH, exist_ok=True)

connected_clients = set()

# (The get_local_ip and execute_command functions remain EXACTLY the same as before)
# ... paste your existing get_local_ip() and execute_command() functions here ...
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
        if command in ["play_pause", "next_track", "prev_track", "volume_up", "volume_down", "mute", "toggle_mute"]:
            key_to_press = command.replace('_', '')
            if command == 'toggle_mute':
                key_to_press = 'volumemute'
            pyautogui.press(key_to_press)
            if command == "toggle_mute": return {"type": "command_response", "message": "Mute toggled"}
            return
        elif command == "mouse_click" and payload:
            screen_width, screen_height = pyautogui.size()
            click_x = int(screen_width * payload['x'])
            click_y = int(screen_height * payload['y'])
            pyautogui.click(click_x, click_y)
            return
        elif command == "lock":
            if os.name == 'nt': os.system("rundll32.exe user32.dll,LockWorkStation")
        elif command == "restart":
            if os.name == 'nt': os.system('shutdown /r /t 1')
            else: os.system('reboot')
        elif command == "shutdown":
            if os.name == 'nt': os.system('shutdown /s /t 1')
            else: os.system('shutdown -h now')
        elif command == "sleep":
            if os.name == 'nt': os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            elif os.name == 'posix': os.system('systemctl suspend')
        elif command == "type_text" and payload:
            pyautogui.typewrite(payload, interval=0.01)
        elif command == "open_url" and payload:
            webbrowser.open(payload)
            return {"type": "command_response", "message": "URL opened"}
        elif command == "set_clipboard" and payload:
            pyperclip.copy(payload)
            return {"type": "command_response", "message": "PC clipboard set"}
        elif command == "get_clipboard":
            return {"type": "clipboard_content", "content": pyperclip.paste()}
        elif command == "take_screenshot":
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"Screenshot-{timestamp}.png"
            save_path = os.path.join(UPLOAD_PATH, filename)
            pyautogui.screenshot(save_path)
            return {"type": "command_response", "message": f"Screenshot saved to Desktop as {filename}"}
        elif command == "show_desktop":
            if os.name == 'nt': pyautogui.hotkey('win', 'd')
            else: pyautogui.hotkey('command', 'f3')
            return {"type": "command_response", "message": "Show Desktop command sent"}
        elif command == "close_window" and payload:
            title = payload.get('title')
            if not title: return {"type": "command_response", "message": "Window title not provided", "status": "error"}
            try:
                win = gw.getWindowsWithTitle(title)[0] 
                if win:
                    win.close()
                    await asyncio.sleep(0.5) 
                    return {"type": "command_response", "message": f"Closed window '{title}'"}
            except IndexError: return {"type": "command_response", "message": f"Window '{title}' not found", "status": "error"}
            except Exception as e: return {"type": "command_response", "message": f"Could not close '{title}': {e}", "status": "error"}
        elif command == "send_notification" and payload:
            notification.notify(title=payload.get('title', 'PC-Pilot Pro'), message=payload.get('message', '...'), app_name='PC-Pilot Pro', timeout=10)
            return {"type": "command_response", "message": "Notification sent"}
        elif command == "list_directory" and payload:
            path_str = payload.get('path', HOME_DIR)
            base_path = Path(HOME_DIR).resolve()
            req_path = Path(path_str).resolve()
            if base_path not in req_path.parents and req_path != base_path: req_path = base_path
            items = []
            parent_dir = str(req_path.parent) if req_path != base_path else str(base_path)
            for item in os.scandir(req_path):
                try: items.append({"name": item.name, "type": "dir" if item.is_dir() else "file"})
                except OSError: continue
            items.sort(key=lambda x: (x['type'], x['name'].lower()))
            return {"type": "directory_listing", "path": str(req_path), "parent": parent_dir, "items": items}
        elif command == "download_file" and payload:
            file_path_str = payload.get('path')
            if not file_path_str: return
            file_path = Path(file_path_str).resolve()
            if not file_path.is_file() or Path(HOME_DIR).resolve() not in file_path.parents:
                return {"type": "command_response", "message": "Invalid file path", "status": "error"}
            with open(file_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
            return {"type": "file_download", "filename": file_path.name, "filedata": file_data}
        elif command == "get_system_info":
            boot_time_timestamp = psutil.boot_time()
            uptime_seconds = time.time() - boot_time_timestamp
            uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))
            info = {"os": f"{platform.system()} {platform.release()}", "hostname": socket.gethostname(), "user": psutil.users()[0].name if psutil.users() else "N/A", "uptime": uptime_str}
            return {"type": "system_info", "info": info}
        elif command == "get_processes":
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try: processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): pass
            processes.sort(key=lambda x: x['name'].lower())
            return {"type": "process_list", "processes": processes}
        elif command == "kill_process" and payload:
            pid = payload.get('pid')
            if pid is None: return {"type": "command_response", "message": "PID not provided", "status": "error"}
            try:
                p = psutil.Process(pid)
                p.terminate()
                await asyncio.sleep(0.5)
                return {"type": "command_response", "message": f"Process {pid} terminated."}
            except psutil.NoSuchProcess: return {"type": "command_response", "message": f"Process {pid} not found.", "status": "error"}
            except psutil.AccessDenied: return {"type": "command_response", "message": f"Access denied to terminate process {pid}.", "status": "error"}
        else:
            print(f"Unknown command or missing payload: {command}")
        return {"type": "command_response", "message": f"Executed '{command}'"}
    except Exception as e:
        print(f"Error executing command '{command}': {e}")
        return {"type": "command_response", "message": f"Error on '{command}': {e}", "status": "error"}


async def handle_client(websocket):
    connected_clients.add(websocket)
    print(f"Client connected. Total clients: {len(connected_clients)}")
    try:
        initial_dir_data = await execute_command('list_directory', {'path': HOME_DIR})
        await websocket.send(json.dumps(initial_dir_data))
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get('type')
            if msg_type == 'command':
                response_message = await execute_command(data.get('command'), data.get('payload'))
                if response_message: await websocket.send(json.dumps(response_message))
            elif msg_type == 'file_upload':
                try:
                    filename = os.path.basename(data.get('filename', 'uploaded_file'))
                    save_path = os.path.join(UPLOAD_PATH, filename)
                    file_bytes = base64.b64decode(data.get('filedata'))
                    with open(save_path, 'wb') as f: f.write(file_bytes)
                    await websocket.send(json.dumps({"type": "command_response", "message": f"Uploaded '{filename}'!"}))
                except Exception as e:
                    await websocket.send(json.dumps({"type": "command_response", "message": "File upload failed."}))
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnected. Total clients: {len(connected_clients)}")

# DANS server.py, REMPLACEZ CETTE FONCTION

async def broadcast_data():
    with mss.mss() as sct:
        while True:
            await asyncio.sleep(1)
            if not connected_clients:
                continue

            try:
                # Préparer le paquet de données une seule fois
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=JPEG_QUALITY)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                visible_windows = [title for title in gw.getAllTitles() if title]
                battery = psutil.sensors_battery()
                
                full_data = {
                    "type": "combined_update",
                    "screenshot": img_base64,
                    "windows": visible_windows,
                    "stats": {
                        "cpu": psutil.cpu_percent(),
                        "ram": psutil.virtual_memory().percent,
                        "disk": psutil.disk_usage('/').percent,
                        "battery": {"percent": battery.percent, "charging": battery.power_plugged} if battery else None
                    }
                }
                
                # Convertir en JSON une seule fois
                message_to_send = json.dumps(full_data)
                
                # Envoyer aux clients et gérer les déconnexions
                dead_clients = set()
                # On utilise list() pour créer une copie, car on ne peut pas modifier un set pendant qu'on l'itère
                for client in list(connected_clients):
                    try:
                        # ✅ LA CORRECTION : Utiliser send_str() pour aiohttp
                        await client.send_str(message_to_send)
                    except (ConnectionResetError, RuntimeError):
                        print(f"Client disconnected abruptly. Removing from broadcast list.")
                        dead_clients.add(client)

                # Nettoyer les clients déconnectés
                if dead_clients:
                    for client in dead_clients:
                        if client in connected_clients:
                            connected_clients.remove(client)

            except Exception as e:
                print(f"Error in broadcast loop: {e}")

# NEW: aiohttp handlers
async def http_handler(request):
    """Serves the index.html file."""
    return web.FileResponse('./index.html')

async def websocket_handler(request):
    """Handles the WebSocket connection."""
    ws = web.WebSocketResponse(max_msg_size=20_000_000)
    await ws.prepare(request)
    
    # This replaces the old handle_client logic but integrates with aiohttp
    connected_clients.add(ws)
    print(f"Client connected via aiohttp. Total clients: {len(connected_clients)}")
    try:
        # Send initial data
        initial_dir_data = await execute_command('list_directory', {'path': HOME_DIR})
        await ws.send_json(initial_dir_data)
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                msg_type = data.get('type')
                
                if msg_type == 'command':
                    response = await execute_command(data.get('command'), data.get('payload'))
                    if response: await ws.send_json(response)
                elif msg_type == 'file_upload':
                    # Handle file upload...
                    try:
                        filename = os.path.basename(data.get('filename', 'uploaded_file'))
                        save_path = os.path.join(UPLOAD_PATH, filename)
                        file_bytes = base64.b64decode(data.get('filedata'))
                        with open(save_path, 'wb') as f: f.write(file_bytes)
                        await ws.send_json({"type": "command_response", "message": f"Uploaded '{filename}'!"})
                    except Exception as e:
                        print(f"Upload failed: {e}")
                        await ws.send_json({"type": "command_response", "message": "File upload failed.", "status":"error"})

            elif msg.type == web.WSMsgType.ERROR:
                print(f"ws connection closed with exception {ws.exception()}")

    finally:
        connected_clients.remove(ws)
        print(f"Client disconnected. Total clients: {len(connected_clients)}")

    return ws

async def main():
    # Create the aiohttp application
    app = web.Application()
    
    # Add the route for the main page ('/') to serve index.html
    app.router.add_get('/', http_handler)
    
    # Add the route for the websocket connection
    app.router.add_get('/ws', websocket_handler)

    # Start the broadcast task in the background
    asyncio.create_task(broadcast_data())

    # Setup and run the web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    
    local_ip = get_local_ip()
    print("--------------------------------------------------")
    print("🚀 PC-Pilot Pro All-in-One Server is RUNNING!")
    print(f"   - To connect on your local network, go to: http://{local_ip}:{PORT}")
    print("\n   To connect from ANYWHERE, see the ngrok instructions.")
    print("--------------------------------------------------")

    await site.start()
    
    # Wait forever
    await asyncio.Event().wait()


if __name__ == "__main__":
    # Also need to modify the client JS to handle 'combined_update'
    print("Reminder: The client-side Javascript needs a small change to handle 'combined_update' messages.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down.")
