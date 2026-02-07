import keyboard
from PIL import ImageGrab, Image, ImageTk
import requests
import json
import time
import os
import io
import threading
import random
import tkinter as tk
import queue
import pyautogui
from datetime import datetime


# Configuration
SAVE_PATH = r'C:\DATA\SD\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\input\screenshot.jpg'
PROMPT_URL = 'http://127.0.0.1:8188/prompt'
HISTORY_URL = 'http://127.0.0.1:8188/history?max_items=64'
VIEW_URL_BASE = 'http://127.0.0.1:8188/view'

CROP_TOP = 50       #REMOVE PX FROM TOP
CROP_BOTTOM = 10    #REMOVE PX FROM BOTTOM
CROP_LEFT = 10      #REMOVE PX FROM LEFT
CROP_RIGHT = 10     #REMOVE PX FROM RIGHT

start_time = time.time()

HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh-TW;q=0.6,zh;q=0.5',
    'Cache-Control': 'max-age=0',
    'Comfy-User': '',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KJSON, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not/A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
}

class ImageViewer:
    def __init__(self):
        self.root = None
        self.image_label = None
        self.queue = queue.Queue()
        self.last_geometry = None
        self.original_image = None
        self.resize_job = None
        self.init_ui()

    def init_ui(self):
        self.root = tk.Tk()
        self.root.title("screen2edit Image Viewer")
        self.root.protocol("WM_DELETE_WINDOW", self.withdraw_window)
        self.root.withdraw()

        # Create canvas for image display
        self.canvas = tk.Canvas(self.root, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind resize events with debounce
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Start queue processing
        self.root.after(100, self.process_queue)

    def on_canvas_resize(self, event=None):
        # Cancel any pending resize jobs
        if self.resize_job:
            self.root.after_cancel(self.resize_job)
        # Schedule image update after resize pause
        self.resize_job = self.root.after(200, self.update_image)
        
    def process_queue(self):
        try:
            while True:
                img = self.queue.get_nowait()
                self.show_image(img)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def show_image(self, img):
        self.original_image = img
        if self.root.state() == 'withdrawn':
            if self.last_geometry:
                self.root.geometry(self.last_geometry)
            self.root.deiconify()
        # Force image update regardless of size
        self.current_size = None  # Add this line! <---
        self.root.after(100, self.update_image)
        
    def update_image(self):
        if not self.original_image:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Prevent empty canvas sizes
        if canvas_width <= 1 or canvas_height <= 1:
            return

        # Calculate aspect ratio
        img_width, img_height = self.original_image.size
        ratio = min(canvas_width/img_width, canvas_height/img_height)
        new_size = (int(img_width * ratio), int(img_height * ratio))

        # Only resize if the new size is different
        if hasattr(self, 'current_size') and self.current_size == new_size:
            return
            
        # Resize and display with high-quality downsampling
        resized_img = self.original_image.resize(new_size, Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_img)
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width/2,
            canvas_height/2,
            anchor=tk.CENTER,
            image=self.tk_image
        )
        self.current_size = new_size

    def withdraw_window(self):
        self.last_geometry = self.root.geometry()
        self.root.withdraw()

# Global image viewer instance
image_viewer = ImageViewer()

def ensure_directory():
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

def capture_and_save_active_window():
    """
    Capture the current active window and save it to a file
    """
    try:
        # Get the active window
        window = pyautogui.getActiveWindow()
        
        if window is None:
            print("No active window found!")
            return None
        
        # Get window position and size
        left, top, width, height = window.left, window.top, window.width, window.height
        
        print(f"Capturing active window:")
        print(f"  Title: {window.title}")
        print(f"  Position: ({left}, {top})")
        print(f"  Size: {width}x{height}")
        
        # Capture the window region
        # use globals at the top of the script to crop
        screenshot = pyautogui.screenshot(region=(left+CROP_LEFT, top+CROP_TOP, width-CROP_LEFT-CROP_RIGHT, height-CROP_TOP-CROP_BOTTOM))
        
        # Create save directory if it doesn't exist
        save_dir = "screenshots"
        os.makedirs(save_dir, exist_ok=True)
        
        # Generate filename with timestamp
        #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        #filename = f"active_window_{timestamp}.png"
        #save_path = os.path.join(save_dir, filename)
        
        # Save the screenshot
        screenshot.save(SAVE_PATH)
        print(f"Screenshot saved to: {SAVE_PATH}")
        
        return SAVE_PATH
        
    except Exception as e:
        print(f"Error capturing active window: {e}")
        return None    

def get_history_uuids():
    try:
        response = requests.get(HISTORY_URL, headers=HEADERS)
        return set(response.json().keys())
    except Exception as e:
        print(f"Error getting history: {e}")
        return set()
        
def update_noise_seed(data, new_seed):
    """Рекурсивно ищет все ключи 'noise_seed' и обновляет их."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "noise_seed":
                data[key] = new_seed
            else:
                update_noise_seed(value, new_seed)
    elif isinstance(data, list):
        for item in data:
            update_noise_seed(item, new_seed)        

def send_prompt() -> bool:
    try:
        global start_time 
        start_time = time.time() # Начинаем отсчет перед запросом
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path to workflow.json
        json_file_path = os.path.join(script_dir, 'workflows/workflow.json')
        
        print(f"Reading workflow from: {json_file_path}")
        
        # Read and parse the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as file:
            workflow_data = json.load(file)
        
        new_seed = random.randint(0, 10**5) 
        update_noise_seed(workflow_data, new_seed)
        print(f"Updated noise_seed to: {new_seed}")
        
        # Wrap the workflow data in a prompt attribute
        payload = {
            "prompt": workflow_data
        }
        
        print(f"Sending POST request to: {PROMPT_URL}")
        print(f"Payload structure: {{prompt: <workflow_data>}}")
        
        # Send the POST request
        response = requests.post(
            PROMPT_URL, 
            headers=HEADERS, 
            json=payload,
            timeout=30
        )
        
        # Print response details
        print(f"Response Status Code: {response.status_code}")        
        try:
            response_json = response.json()
            print(f"Response Body:\n{json.dumps(response_json, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response Body (raw): {response.text}")
        
        return response.status_code == 200
        
    except FileNotFoundError:
        print(f"Error: workflow.json not found in {script_dir}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in workflow.json: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {PROMPT_URL}")
        print("Please ensure the server is running at the specified URL.")
        return False
    except requests.exceptions.Timeout:
        print("Error: Request timed out. The server took too long to respond.")
        return False
    except Exception as e:
        print(f"Error sending prompt: {e}")
        return False

def poll_history(pre_uuids):
    while True:
        time.sleep(1)
        try:
            current_uuids = get_history_uuids()
            new_uuids = current_uuids - pre_uuids
            for uuid in new_uuids:
                response = requests.get(HISTORY_URL, headers=HEADERS)
                history = response.json().get(uuid, {})
                outputs = history.get('outputs', {})
                
                for node_id in outputs:
                    images = outputs[node_id].get('images', [])
                    for image in images:
                        filename = image.get('filename')
                        if filename:
                            fetch_and_display_image(filename)
                            return
            pre_uuids.update(current_uuids)
        except Exception as e:
            print(f"Polling error: {e}")
            return

def fetch_and_display_image(filename):
    rand = random.random()
    view_url = f"{VIEW_URL_BASE}?filename={filename}&subfolder=&type=output&rand={rand}"
    try:
        response = requests.get(view_url)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            # Put the image in the queue instead of showing it directly
            image_viewer.queue.put(img)
            elapsed = time.time() - start_time
            print(f"Done in {elapsed:.2f} s.") # Формат x.00 s.
    except Exception as e:
        print(f"Error displaying image: {e}")

def on_hotkey():    
    ensure_directory()
    capture_and_save_active_window()    
    pre_uuids = get_history_uuids()
    
    if not send_prompt():
        return
    
    print("Took a screenshot. Waiting resp from comfy...")
    threading.Thread(target=poll_history, args=(pre_uuids,)).start()

if __name__ == "__main__":
    ensure_directory()
    keyboard.add_hotkey('alt+x', on_hotkey)
    print("Press Alt+X to take screenshot... Press Ctrl+C to exit.")
    # Set up Tkinter main loop in main thread
    image_viewer.root.mainloop()
