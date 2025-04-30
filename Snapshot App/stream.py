import os
import sys
import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import time
import easyocr
import re
from pathlib import Path
from ultralytics import YOLO
import requests
from django.utils import timezone

# Django setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarttrack.settings")
import django

django.setup()

from parking.models import Vehicle, EntryExitLog

model_path = "../runs/detect/train3/weights/best.pt"
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found: {model_path}")
model = YOLO(model_path)
reader = easyocr.Reader(["en"])

entries_dir = Path("C:/Users/xraff/OneDrive/Desktop/smarttrack/entries")
entries_dir.mkdir(exist_ok=True)

cap = cv2.VideoCapture(0)

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
    video_panel.image = imgtk
    detect_plate_live(frame)

    root.after(500, show_stream)


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
    confirm_window.geometry("")  # Let window auto-fit content

    confirm_window.lift()
    confirm_window.attributes("-topmost", True)
    confirm_window.after_idle(confirm_window.attributes, "-topmost", False)

    # Resize and display image
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    img = img.resize((600, 400), Image.Resampling.LANCZOS)
    imgtk = ImageTk.PhotoImage(image=img)
    img_label = tk.Label(confirm_window, image=imgtk)
    img_label.image = imgtk
    img_label.pack()

    plate_label = tk.Label(
        confirm_window, text=f"Detected Plate: {plate}", font=("Arial", 18)
    )
    plate_label.pack(pady=10)

    plate_entry = tk.Entry(confirm_window, font=("Arial", 16))
    plate_entry.insert(0, plate)
    plate_entry.pack(pady=10)

    def save_and_log():
        new_plate = plate_entry.get().strip()
        if not new_plate:
            messagebox.showwarning("Invalid Plate", "Plate number cannot be empty.")
            return

        cleaned_plate_text = clean_plate_text(new_plate)
        url = f"http://127.0.0.1:8000/parking/log/?plate={cleaned_plate_text}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"✅ Logged to backend: {response.json()}")
            else:
                print(f"❌ Failed to log: {response.text}")
        except Exception as e:
            print(f"❗ Error logging to backend: {e}")

        timestamp = int(time.time())
        filename = entries_dir / f"snapshot_{timestamp}.jpg"
        cv2.imwrite(str(filename), frame)

        vehicle, _ = Vehicle.objects.get_or_create(license_plate=new_plate)
        EntryExitLog.objects.create(vehicle=vehicle, entry_time=timezone.now())

        confirm_window.destroy()
        messagebox.showinfo("Success", f"✅ Plate logged: {new_plate}")

    def recapture():
        confirm_window.destroy()
        capture_snapshot()

    print("Creating confirmation buttons...")  # Debugging aid
    btn_frame = tk.Frame(confirm_window)
    btn_frame.pack(pady=20)

    tk.Button(btn_frame, text="✅ Continue", command=save_and_log, width=15).pack(
        side=tk.LEFT, padx=10
    )
    tk.Button(btn_frame, text="🔁 Recapture", command=recapture, width=15).pack(
        side=tk.LEFT, padx=10
    )
    print("Buttons packed.")  # Debugging aid


btn_frame = tk.Frame(root)
btn_frame.pack(pady=15)

tk.Button(btn_frame, text="📸 Capture", width=20, command=capture_snapshot).pack(
    side=tk.LEFT, padx=10
)
tk.Button(
    btn_frame, text="❌ Exit", width=20, command=lambda: (cap.release(), root.destroy())
).pack(side=tk.LEFT, padx=10)

show_stream()
root.mainloop()
