import pystray
from pystray import MenuItem as item
from PIL import Image
import subprocess
import sys
import os

# Reference to Inferna process
AI_PROCESS = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AI_FILE = os.path.join(BASE_DIR, "FinalAI.py")

def start_ai():
    global AI_PROCESS
    if AI_PROCESS is None:
        AI_PROCESS = subprocess.Popen(
            [sys.executable, AI_FILE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

def stop_ai():
    global AI_PROCESS
    if AI_PROCESS:
        AI_PROCESS.terminate()
        AI_PROCESS = None

def exit_app(icon, item): 
    stop_ai()
    icon.stop()

def on_tray_ready(icon):
    icon.visible = True
    start_ai()   # AUTO START INFERNA

# Simple black icon (no image file needed)
icon_image = Image.new("RGB", (64, 64), "black")

icon = pystray.Icon(
    "Inferna",
    icon_image,
    "Inferna Assistant",
    menu=pystray.Menu(
        item("Start Inferna", lambda: start_ai()),
        item("Stop Inferna", lambda: stop_ai()),
        item("Exit", exit_app)
    )
)

icon.run(on_tray_ready)
