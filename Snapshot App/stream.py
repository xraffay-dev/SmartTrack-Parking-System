import os
import sys

# Django setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarttrack.settings")
import django

django.setup()

# Django models
from parking.models import Vehicle, EntryExitLog
from django.utils import timezone

# Other imports
import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import time
import easyocr
import re
from pathlib import Path
from ultralytics import YOLO

# Load models
model_path = "../runs/detect/train3/weights/best.pt"
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found: {model_path}")
model = YOLO(model_path)
reader = easyocr.Reader(["en"])

# Snapshot folder
entries_dir = Path("C:/Users/xraff/OneDrive/Desktop/smarttrack/entries")
entries_dir.mkdir(exist_ok=True)

# Initialize camera
cap = cv2.VideoCapture(0)

# GUI Setup
root = tk.Tk()
root.title("SmartTrack Snapshot")
root.geometry("800x650")

detected_plate = tk.StringVar(value="Detecting...")

video_panel = tk.Label(root)
video_panel.pack()

plate_display = tk.Label(root, textvariable=detected_plate, font=("Arial", 16))
plate_display.pack(pady=5)


def clean_plate_text(text):
    text = re.sub(r"[^A-Z0-9]", "", text.upper())
    return text if 5 <= len(text) <= 12 else None


def detect_plate_live(frame):
    results = model(frame)[0]
    for box in results.boxes:
        if box.conf < 0.5:
            continue
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cropped = frame[y1:y2, x1:x2]
        ocr_result = reader.readtext(cropped)
        plate = clean_plate_text(ocr_result[0][1]) if ocr_result else None
        if plate:
            detected_plate.set(f"📛 Plate Detected: {plate}")
            return plate
    detected_plate.set("📛 Plate Detected: ---")
    return None


def show_stream():
    ret, frame = cap.read()
    if not ret:
        return
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    imgtk = ImageTk.PhotoImage(image=img)

    video_panel.configure(image=imgtk)
    video_panel.image = imgtk  # Prevent GC
    detect_plate_live(frame)

    root.after(500, show_stream)  # Update every 0.5s for performance


def capture_snapshot():
    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("Capture Error", "Could not read from camera.")
        return
    plate = detect_plate_live(frame)
    if not plate:
        messagebox.showwarning("No Plate", "No license plate detected.")
        return
    show_confirmation_window(frame, plate)


def show_confirmation_window(frame, plate):
    confirm_window = tk.Toplevel(root)
    confirm_window.title("Confirm Plate")
    confirm_window.geometry("800x600")

    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    img_label = tk.Label(confirm_window, image=imgtk)
    img_label.image = imgtk
    img_label.pack()

    plate_label = tk.Label(
        confirm_window, text=f"Detected Plate: {plate}", font=("Arial", 18)
    )
    plate_label.pack(pady=10)

    def save_and_log():
        timestamp = int(time.time())
        filename = entries_dir / f"snapshot_{timestamp}.jpg"
        cv2.imwrite(str(filename), frame)
        vehicle, _ = Vehicle.objects.get_or_create(license_plate=plate)
        EntryExitLog.objects.create(vehicle=vehicle, entry_time=timezone.now())
        confirm_window.destroy()
        messagebox.showinfo("Success", f"✅ Plate logged: {plate}")

    def recapture():
        confirm_window.destroy()

    btn_frame = tk.Frame(confirm_window)
    btn_frame.pack(pady=20)
    tk.Button(btn_frame, text="✅ Continue", command=save_and_log, width=15).pack(
        side=tk.LEFT, padx=10
    )
    tk.Button(btn_frame, text="🔁 Recapture", command=recapture, width=15).pack(
        side=tk.LEFT, padx=10
    )


btn_frame = tk.Frame(root)
btn_frame.pack(pady=15)

tk.Button(btn_frame, text="📸 Capture", width=20, command=capture_snapshot).pack(
    side=tk.LEFT, padx=10
)
tk.Button(
    btn_frame, text="❌ Exit", width=20, command=lambda: (cap.release(), root.destroy())
).pack(side=tk.LEFT, padx=10)

# Start stream
show_stream()
root.mainloop()
