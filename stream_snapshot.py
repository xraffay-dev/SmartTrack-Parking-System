import cv2
import matplotlib.pyplot as plt
import easyocr
from ultralytics import YOLO
import os
import django
import time
import re
from pathlib import Path

# 🛠 Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarttrack.settings")
django.setup()

from parking.models import Vehicle, EntryExitLog
from django.utils import timezone

# 📦 Load YOLOv8 model
model = YOLO("runs/detect/train3/weights/best.pt")

# 🎥 Open camera
cap = None
for i in range(5):
    temp_cap = cv2.VideoCapture(i)
    ret, frame = temp_cap.read()
    if ret and frame is not None:
        print(f"✅ Found working camera at index {i}")
        cap = temp_cap
        break
    temp_cap.release()

if cap is None:
    raise RuntimeError("❌ No available camera found.")

# 🧠 OCR engine
reader = easyocr.Reader(["en"])

# 📏 Confidence threshold
YOLO_CONFIDENCE_THRESHOLD = 0.5

# 📂 Create 'entries' folder if it doesn't exist
entries_folder = Path("entries")
entries_folder.mkdir(exist_ok=True)

# 📊 Matplotlib live view
plt.ion()
fig, ax = plt.subplots()


def clean_plate_text(text):
    """Clean OCR text to plate format."""
    text = re.sub(r"[^A-Z0-9]", "", text.upper())
    return text if 5 <= len(text) <= 12 else None


print("[📡] Streaming started... Waiting for car...")

captured = False

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("❌ Frame capture failed.")
        time.sleep(1)
        continue

    # 📺 Live frame
    ax.clear()
    ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    ax.set_title("🚗 Waiting for vehicle...")
    ax.axis("off")
    plt.pause(0.001)

    # 🧠 YOLO Detection
    results = model(frame)[0]

    for box in results.boxes:
        if box.conf < YOLO_CONFIDENCE_THRESHOLD:
            continue

        # 🚀 Found something
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cropped = frame[y1:y2, x1:x2]

        # 🧪 OCR on cropped
        ocr_result = reader.readtext(cropped)
        plate = clean_plate_text(ocr_result[0][1]) if ocr_result else None

        if plate:
            print(f"[✅] Plate Detected: {plate}")
            captured = True

            # 📝 Save to Django
            vehicle, _ = Vehicle.objects.get_or_create(license_plate=plate)
            EntryExitLog.objects.create(vehicle=vehicle, entry_time=timezone.now())

            # 🖼 Save captured frame
            save_path = entries_folder / f"{plate}_{int(time.time())}.jpg"
            cv2.imwrite(str(save_path), frame)
            print(f"📸 Image saved to: {save_path}")

            # 🖍 Annotate
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                plate,
                (x1, max(y1 - 10, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 0, 0),
                2,
            )

            # 🎯 Show captured
            ax.clear()
            ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ax.set_title(f"✅ Captured: {plate}")
            ax.axis("off")
            plt.pause(1)

            break  

    if captured:
        print("👋 Exiting after capture...")
        break

# 🛠️ Clean Exit
cap.release()
cv2.destroyAllWindows()
