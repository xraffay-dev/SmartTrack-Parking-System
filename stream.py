# import cv2
# import easyocr
# import time
# import os
# import django
# import matplotlib.pyplot as plt
# from django.utils import timezone

# # 🛠️ Django setup
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarttrack.settings')
# django.setup()

# from parking.models import Vehicle, EntryExitLog

# # 🎥 Use iVCam or default webcam
# cap = cv2.VideoCapture(1)

# # 🧠 Load OCR engine
# reader = easyocr.Reader(['en'])

# # ✅ Avoid duplicate logging
# seen_plates = set()
# last_seen_time = {}
# cooldown = 60  # seconds

# # 📊 Enable interactive plotting
# plt.ion()
# fig, ax = plt.subplots()

# print("[📷] Streaming started. Press Ctrl+C to stop.")

# while True:
#     ret, frame = cap.read()
#     if not ret or frame is None:
#         print("❌ Failed to grab frame.")
#         time.sleep(1)
#         continue

#     # 🔍 Run OCR
#     results = reader.readtext(frame)
#     current_time = time.time()

#     for _, text, _ in results:
#         plate = text.strip().upper()
#         if 5 <= len(plate) <= 12 and plate.replace("-", "").isalnum():
#             if plate not in last_seen_time or (current_time - last_seen_time[plate]) > cooldown:
#                 print(f"[✅] New Plate: {plate}")
#                 last_seen_time[plate] = current_time

#                 # Log in DB
#                 vehicle, _ = Vehicle.objects.get_or_create(license_plate=plate)
#                 EntryExitLog.objects.create(vehicle=vehicle, entry_time=timezone.now())

#     # 🖼️ Show frame using matplotlib
#     ax.clear()
#     ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
#     ax.set_title("iPhone Camera Live")
#     ax.axis("off")
#     plt.pause(0.001)


import cv2
import matplotlib.pyplot as plt
import easyocr
from ultralytics import YOLO
import os
import django
import time

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarttrack.settings")
django.setup()

from parking.models import Vehicle, EntryExitLog
from django.utils import timezone

# 🔍 Load YOLOv8 model
model = YOLO("runs/detect/train3/weights/best.pt")

# 🎥 Set up iVCam (try 1 if 0 shows laptop cam)
cap = cv2.VideoCapture(1)

# 🧠 Initialize EasyOCR
reader = easyocr.Reader(["en"])

# 🚫 Prevent spam logging
cooldown = 60  # seconds
last_logged = {}

# 📊 Matplotlib setup
plt.ion()
fig, ax = plt.subplots()

print("[📡] Real-time YOLO stream started. Press Ctrl+C to stop.")

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("❌ Frame capture failed.")
        time.sleep(1)
        continue

    # 🧠 YOLOv8 Detection
    results = model(frame)[0]

    for box in results.boxes.xyxy:
        x1, y1, x2, y2 = map(int, box)
        cropped = frame[y1:y2, x1:x2]

        # 🔠 Run OCR only on the cropped plate
        ocr_result = reader.readtext(cropped)
        plate = ocr_result[0][1].strip().upper() if ocr_result else None

        if plate and 5 <= len(plate) <= 12 and plate.replace("-", "").isalnum():
            now = time.time()

            if plate not in last_logged or (now - last_logged[plate]) > cooldown:
                print(f"[✅] Detected: {plate}")
                last_logged[plate] = now

                # 📝 Log to DB
                vehicle, _ = Vehicle.objects.get_or_create(license_plate=plate)
                EntryExitLog.objects.create(vehicle=vehicle, entry_time=timezone.now())

            # 🖍 Annotate on frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                plate,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 0, 0),
                2,
            )

    # 📺 Display frame with matplotlib
    ax.clear()
    ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    ax.set_title("📷 Live YOLO + OCR Feed")
    ax.axis("off")
    plt.pause(0.001)
