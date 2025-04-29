from pathlib import Path

# Create directory for GUI if it doesn't exist
gui_dir = Path.cwd() / "ui_snapshot_app"
gui_dir.mkdir(exist_ok=True)

# Content of the updated GUI script with capture + recapture functionality
gui_script = """
import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import time
import easyocr
import os
import django
from ultralytics import YOLO
from parking.models import Vehicle, EntryExitLog
from django.utils import timezone
import re
from pathlib import Path

# 🛠 Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarttrack.settings")
django.setup()

# 🧠 Load models
model = YOLO("runs/detect/train3/weights/best.pt")
reader = easyocr.Reader(["en"])

# 📂 Snapshot folder
entries_dir = Path("entries")
entries_dir.mkdir(exist_ok=True)

# 📷 Open camera
cap = cv2.VideoCapture(1)

def clean_plate_text(text):
    text = re.sub(r'[^A-Z0-9]', '', text.upper())
    return text if 5 <= len(text) <= 12 else None

def capture_snapshot():
    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("Capture Error", "Could not read from camera.")
        return None, None
    filename = entries_dir / f"snapshot_{int(time.time())}.jpg"
    cv2.imwrite(str(filename), frame)
    return frame, filename

def process_image(frame):
    results = model(frame)[0]
    for box in results.boxes:
        if box.conf < 0.5:
            continue
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cropped = frame[y1:y2, x1:x2]
        ocr_result = reader.readtext(cropped)
        plate = clean_plate_text(ocr_result[0][1]) if ocr_result else None

        if plate:
            vehicle, _ = Vehicle.objects.get_or_create(license_plate=plate)
            EntryExitLog.objects.create(vehicle=vehicle, entry_time=timezone.now())
            return plate
    return None

def handle_capture():
    global last_frame
    frame, filename = capture_snapshot()
    if frame is not None:
        last_frame = frame
        plate = process_image(frame)
        if plate:
            messagebox.showinfo("Success", f"✅ Plate logged: {plate}")
        else:
            messagebox.showwarning("No Plate", "No license plate detected. Click Recapture to try again.")
    else:
        messagebox.showerror("Error", "Snapshot failed.")

def show_stream():
    ret, frame = cap.read()
    if not ret:
        return
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    video_panel.imgtk = imgtk
    video_panel.config(image=imgtk)
    video_panel.after(10, show_stream)

# 🧱 GUI Setup
root = tk.Tk()
root.title("SmartTrack Snapshot")
root.geometry("800x600")

video_panel = tk.Label(root)
video_panel.pack()

btn_frame = tk.Frame(root)
btn_frame.pack(pady=15)

tk.Button(btn_frame, text="📸 Capture", width=20, command=handle_capture).pack(side=tk.LEFT, padx=10)
tk.Button(btn_frame, text="🔁 Recapture", width=20, command=show_stream).pack(side=tk.LEFT, padx=10)
tk.Button(btn_frame, text="❌ Exit", width=20, command=lambda: (cap.release(), root.destroy())).pack(side=tk.LEFT, padx=10)

last_frame = None
show_stream()
root.mainloop()
"""

# Save the script to a file
script_path = gui_dir / "stream_snapshot_gui.py"
with open(script_path, "w", encoding="utf-8") as f:
    f.write(gui_script)

script_path.name  # Return only the filename
