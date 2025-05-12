import os
import sys
import cv2
import re
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from ultralytics import YOLO
from pathlib import Path
from django.utils import timezone
import easyocr
import requests
import time
import datetime

# Django setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarttrack.settings")
import django

django.setup()

from parking.models import Vehicle, EntryExitLog

# Try to load the YOLO model if it exists, otherwise use manual entry mode
model_path = "./runs/detect/train3/weights/best.pt"
model_exists = os.path.exists(model_path)

if model_exists:
    model = YOLO(model_path)
    print(f"YOLO model loaded from {model_path}")
else:
    print(f"YOLO model not found at {model_path}. Running in manual entry mode.")

# Always load the OCR reader since we'll use it if available
reader = easyocr.Reader(["en"])

# Use a relative path instead of hardcoded path
entries_dir = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'entries'))
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
    return re.sub(r"[^A-Z0-9]", "", text.upper())

def detect_plate_live(frame):
    # If model doesn't exist, return None and show manual entry mode
    if not model_exists:
        detected_plate.set("📛 Manual Entry Mode (No YOLO model)")
        return None
    
    # If model exists, use it for detection
    try:
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
    except Exception as e:
        print(f"Error in detection: {e}")
        detected_plate.set("📛 Detection Error")
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
    
    if model_exists:
        # Try to detect plate using YOLO model
        plate = detect_plate_live(frame)
        if not plate:
            # No plate detected, ask if user wants to enter manually
            manual_entry = messagebox.askyesno("No Plate", "No license plate detected. Would you like to enter it manually?")
            if not manual_entry:
                return
            # Use empty string as placeholder for manual entry
            plate = ""
    else:
        # In manual mode, always use empty string as placeholder
        plate = ""
    
    # Show confirmation window with the captured frame and detected/empty plate
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

    # Display appropriate label based on whether plate was detected or manual entry
    if plate:
        plate_label = tk.Label(
            confirm_window, text=f"Detected Plate: {plate}", font=("Arial", 18)
        )
    else:
        plate_label = tk.Label(
            confirm_window, text="Manual Entry Mode", font=("Arial", 18)
        )
    plate_label.pack(pady=10)

    # Create entry field for plate number
    plate_entry = tk.Entry(confirm_window, font=("Arial", 16))
    if plate:  # Only pre-fill if plate was detected
        plate_entry.insert(0, plate)
    plate_entry.pack(pady=10)
    
    # Focus on entry field for immediate typing in manual mode
    plate_entry.focus()

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

        # Format timestamp in the same way as plateLogger.py
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        # Use the license plate as part of the filename, just like plateLogger.py
        filename = entries_dir / f"{cleaned_plate_text}_{timestamp}.jpg"
        cv2.imwrite(str(filename), frame)
        print(f"✅ Image saved as: {filename}")

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
