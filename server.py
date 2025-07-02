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

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 8765
JPEG_QUALITY = 75
HOME_DIR = str(Path.home())
UPLOAD_PATH = os.path.join(HOME_DIR, 'Desktop')
os.makedirs(UPLOAD_PATH, exist_ok=True)

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
        # Media Controls (silent)
        if command in ["play_pause", "next_track", "prev_track", "volume_up", "volume_down", "mute"]:
            pyautogui.press(command.replace('_', ''))
            return
        
        elif command == "toggle_mute":
            pyautogui.press("volumemute")
            return {"type": "command_response", "message": "Mute toggled"}

        # Mouse Click (silent)
        elif command == "mouse_click" and payload:
            screen_width, screen_height = pyautogui.size()
            click_x = int(screen_width * payload['x'])
            click_y = int(screen_height * payload['y'])
            pyautogui.click(click_x, click_y)
            return

        # Power Controls
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
        
        # Text Input
        elif command == "type_text" and payload:
            pyautogui.typewrite(payload, interval=0.01)
        # Open URL
        elif command == "open_url" and payload:
            webbrowser.open(payload)
            return {"type": "command_response", "message": "URL opened"}
        # Clipboard Control
        elif command == "set_clipboard" and payload:
            pyperclip.copy(payload)
            return {"type": "command_response", "message": "PC clipboard set"}
        elif command == "get_clipboard":
            return {"type": "clipboard_content", "content": pyperclip.paste()}
        # Quick Actions
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
        
        # ### NEW: Close Window Command ###
        elif command == "close_window" and payload:
            title = payload.get('title')
            if not title:
                return {"type": "command_response", "message": "Window title not provided", "status": "error"}
            try:
                # getWindowsWithTitle returns a list, we target the first match
                win = gw.getWindowsWithTitle(title)[0] 
                if win:
                    win.close()
                    # A small delay helps the OS update the window list before the next broadcast
                    await asyncio.sleep(0.5) 
                    return {"type": "command_response", "message": f"Closed window '{title}'"}
                else: # This case is unlikely if the first try didn't raise an error
                    return {"type": "command_response", "message": f"Window '{title}' not found", "status": "error"}
            except IndexError:
                 return {"type": "command_response", "message": f"Window '{title}' not found (already closed?)", "status": "error"}
            except Exception as e:
                # Some windows (e.g. system windows) might resist closing and throw an error
                return {"type": "command_response", "message": f"Could not close '{title}': {e}", "status": "error"}

        # Send Notification
        elif command == "send_notification" and payload:
            notification.notify(
                title=payload.get('title', 'PC-Pilot Pro'),
                message=payload.get('message', 'This is a notification from your phone.'),
                app_name='PC-Pilot Pro',
                timeout=10
            )
            return {"type": "command_response", "message": "Notification sent"}
        # File Explorer - List Directory
        elif command == "list_directory" and payload:
            path_str = payload.get('path', HOME_DIR)
            base_path = Path(HOME_DIR).resolve()
            req_path = Path(path_str).resolve()
            if base_path not in req_path.parents and req_path != base_path:
                 req_path = base_path
            items = []
            parent_dir = str(req_path.parent) if req_path != base_path else str(base_path)
            for item in os.scandir(req_path):
                try: items.append({"name": item.name, "type": "dir" if item.is_dir() else "file"})
                except OSError: continue
            items.sort(key=lambda x: (x['type'], x['name'].lower()))
            return {"type": "directory_listing", "path": str(req_path), "parent": parent_dir, "items": items}
        # File Explorer - Download File
        elif command == "download_file" and payload:
            file_path_str = payload.get('path')
            if not file_path_str: return
            file_path = Path(file_path_str).resolve()
            if not file_path.is_file() or Path(HOME_DIR).resolve() not in file_path.parents:
                return {"type": "command_response", "message": "Invalid file path", "status": "error"}
            with open(file_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
            return {"type": "file_download", "filename": file_path.name, "filedata": file_data}

        # System Information Command
        elif command == "get_system_info":
            boot_time_timestamp = psutil.boot_time()
            uptime_seconds = time.time() - boot_time_timestamp
            uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))
            info = {
                "os": f"{platform.system()} {platform.release()}",
                "hostname": socket.gethostname(),
                "user": psutil.users()[0].name if psutil.users() else "N/A",
                "uptime": uptime_str
            }
            return {"type": "system_info", "info": info}

        # Process Manager Commands
        elif command == "get_processes":
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            processes.sort(key=lambda x: x['name'].lower())
            return {"type": "process_list", "processes": processes}
        
        elif command == "kill_process" and payload:
            pid = payload.get('pid')
            if pid is None:
                return {"type": "command_response", "message": "PID not provided", "status": "error"}
            try:
                p = psutil.Process(pid)
                p.terminate() 
                await asyncio.sleep(0.5) # Give OS time to update process list
                # After killing, we can optionally resend the process list
                # get_processes_data = await execute_command('get_processes')
                # for client in connected_clients:
                #     await client.send(json.dumps(get_processes_data))
                return {"type": "command_response", "message": f"Process {pid} terminated."}
            except psutil.NoSuchProcess:
                return {"type": "command_response", "message": f"Process {pid} not found.", "status": "error"}
            except psutil.AccessDenied:
                return {"type": "command_response", "message": f"Access denied to terminate process {pid}.", "status": "error"}

        else:
            print(f"Unknown command or missing payload: {command}")

        # Default success response
        return {"type": "command_response", "message": f"Executed '{command}'"}

    except Exception as e:
        print(f"Error executing command '{command}': {e}")
        return {"type": "command_response", "message": f"Error on '{command}': {e}", "status": "error"}

# The rest of the server code is unchanged and does not need to be modified.
async def handle_client(websocket):
    connected_clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}. Total clients: {len(connected_clients)}")
    try:
        initial_dir_data = await execute_command('list_directory', {'path': HOME_DIR})
        if initial_dir_data: await websocket.send(json.dumps(initial_dir_data))
        sys_info_data = await execute_command('get_system_info')
        if sys_info_data: await websocket.send(json.dumps(sys_info_data))

        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get('type')
            if msg_type == 'command':
                response_message = await execute_command(data.get('command'), data.get('payload'))
                if response_message:
                    await websocket.send(json.dumps(response_message))
            elif msg_type == 'file_upload':
                try:
                    filename = data.get('filename', 'uploaded_file')
                    safe_filename = os.path.basename(filename)
                    save_path = os.path.join(UPLOAD_PATH, safe_filename)
                    file_bytes = base64.b64decode(data.get('filedata'))
                    with open(save_path, 'wb') as f: f.write(file_bytes)
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
    with mss.mss() as sct:
        while True:
            await asyncio.sleep(1) 
            if not connected_clients: continue
            
            # Prepare all data packages
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=JPEG_QUALITY)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            screenshot_data = {"type": "screenshot", "image": img_base64}
            
            try:
                all_windows = gw.getAllTitles()
                visible_windows = [title for title in all_windows if title]
                windows_data = {"type": "windows", "windows": visible_windows}
            except Exception as e:
                print(f"Error getting window list: {e}")
                windows_data = {"type": "windows", "windows": []}

            stats_data = {"type": "stats", "cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent, "disk": psutil.disk_usage('/').percent, "battery": None}
            battery = psutil.sensors_battery()
            if battery:
                stats_data["battery"] = {"percent": battery.percent, "charging": battery.power_plugged}
            
            # Combine all periodic data into one list to send
            all_data = [screenshot_data, windows_data, stats_data]
            
            # Prepare and send data to all clients
            data_to_send = [json.dumps(d) for d in all_data]
            tasks = [asyncio.create_task(client.send(msg)) for client in connected_clients for msg in data_to_send]
            if tasks: await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    server = await websockets.serve(handle_client, HOST, PORT, max_size=20_000_000)
    local_ip = get_local_ip()
    print("--------------------------------------------------")
    print("🚀 PC-Pilot Pro Server is RUNNING!")
    print(f"   - WebSocket listening on: ws://{local_ip}:{PORT}")
    print("\n   To connect from your phone:")
    print("   1. Make sure your phone is on the same Wi-Fi network.")
    print(f"   2. In a NEW terminal in this folder, run: python -m http.server")
    print(f"   3. Open a web browser on your phone and go to: http://{local_ip}:8000")
    print("--------------------------------------------------")

    broadcaster_task = asyncio.create_task(broadcast_data())
    await server.wait_closed()
    await broadcaster_task

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutting down.")
