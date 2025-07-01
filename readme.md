# PC-Pilot

 <!-- Optional: Create a banner image and upload to a host like imgur.com -->

**PC-Pilot** is a powerful, browser-based remote control for your computer. It turns any smartphone or tablet into a versatile command center for your PC, allowing you to manage it from anywhere on your local network.

Built with Python, WebSockets, and modern web technologies, PC-Pilot provides a real-time, responsive, and feature-rich interface right in your web browser, with no app installation required on your phone.

---

## Features

PC-Pilot is packed with features designed for both convenience and power:

#### Real-Time Monitoring
*   **Live Screen Stream:** Watch your PC's desktop in real-time with an efficient, low-latency JPEG stream.
*   **Interactive Mouse Control:** Click, right-click, or double-click anywhere on the screen stream to control your PC's mouse precisely.
*   **System Status Dashboard:** Monitor your PC's CPU, RAM, and Disk usage with live-updating progress bars. Battery status is also displayed for laptops.
*   **Open Windows List:** See a list of all currently open application windows on your PC.

#### Remote Control & Interaction
*   **File Explorer:** Browse your PC's user directory, navigate through folders, and download any file directly to your phone.
*   **Phone-to-PC File Transfer:** Upload multiple files, photos, or videos from your phone directly to your PC's desktop.
    *   **Direct Camera/Video Capture:** Use your phone's camera to take a picture or record a video and send it instantly to your PC.
*   **Process Manager:** View a list of all running processes, see their resource usage, and terminate any process with a single click.
*   **Shell Command Execution:** Run command-line commands (`cmd` or `bash`) on your PC and see the output directly in the web interface.
*   **Media Controls:** Play/pause, skip tracks, and control your PC's master volume.

#### System & Utility
*   **Power Controls:** Securely Lock, Restart, or Shut Down your PC.
*   **Clipboard Sync:** Send text from your phone to your PC's clipboard or fetch the PC's clipboard content back to your phone.
*   **Desktop Notifications:** Send a message from your phone that appears as a native desktop notification on your PC.
*   **Save HD Screenshot:** Instantly save a full-resolution PNG screenshot of your PC's current display to the desktop.

---

## Getting Started

Setting up PC-Pilot is simple and takes just a few minutes.

### Prerequisites

You need Python 3 installed on the PC you want to control. You can get it from [python.org](https://www.python.org/downloads/).

### Installation

1.  **Clone or Download:** Get the project files.
    ```bash
    git clone https://github.com/your-username/pc-pilot.git
    cd pc-pilot
    ```
    Or, download the ZIP and extract it.

2.  **Install Dependencies:** Open a terminal or command prompt in the project folder and run the following command to install the required Python libraries:
    ```bash
    pip install -r requirements.txt
    ```

### Create `requirements.txt`

In your project folder, create a file named `requirements.txt` and paste the following content into it. This file lists all the Python libraries needed for the project.

```
websockets
Pillow
mss
pygetwindow
PyAutoGUI
psutil
pyperclip
plyer
playsound
```

### Running the Application

PC-Pilot requires two components to run: the Python server and a simple web server to host the HTML page.

**Step 1: Start the PC-Pilot Server**
In your terminal, run the main Python script. This is the core of the application.

```bash
python server.py
```
The server will start and display its local IP address, which you will need.

**Step 2: Start the Web Server**
Open a **new, separate terminal** in the same project folder and run the following command. This serves the `index.html` file to your devices.

```bash
python -m http.server
```

### Accessing the Interface

1.  Ensure your smartphone or tablet is connected to the **same Wi-Fi network** as your PC.
2.  Open a web browser (like Chrome, Safari, or Firefox) on your phone.
3.  In the address bar, type the IP address of your PC followed by `:8000`. For example:
    `http://192.168.1.10:8000`
4.  The PC-Pilot interface will load, and you can start controlling your computer!

---

## Screenshots

<!-- Optional: Add screenshots of your app in action -->
<p align="center">
  <img src="https://i.imgur.com/your-screenshot-1.png" width="300" alt="Main Interface">
  <img src="https://i.imgur.com/your-screenshot-2.png" width="300" alt="Process Manager">
</p>

---

## Contributing

Contributions are welcome! If you have ideas for new features or improvements, feel free to fork the repository and submit a pull request.

## License

This project is open-source and available under the [MIT License](LICENSE).


