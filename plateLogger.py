from ultralytics import YOLO
import matplotlib.pyplot as plt
import easyocr
import requests
import argparse
import cv2
import re


def clean_plate_text(plate_text):
    # Replace any character that is not an alphabet, number, or hyphen with a hyphen
    cleaned_text = re.sub(r"[^a-zA-Z0-9-]", "-", plate_text)
    return cleaned_text


# 📦 Load YOLO model
# model = YOLO("runs/detect/train3/weights/best.pt")
model = YOLO("runs/detect/train3/weights/best.pt")

# Parse command line argument
parser = argparse.ArgumentParser()
parser.add_argument("--mode", default="entry", choices=["entry", "exit"])
args = parser.parse_args()

# 📷 Load image
image_path = f"./plate_dataset/test/images/car1.jpg"

image = cv2.imread(image_path)

# 🧠 Init OCR Reader (English only to avoid noise)
reader = easyocr.Reader(["en"])

# 🔍 Detect plate
results = model(image_path)

for box in results[0].boxes.xyxy:
    x1, y1, x2, y2 = map(int, box)
    cropped = image[y1:y2, x1:x2]

    # 🧪 Run EasyOCR
    result = reader.readtext(cropped)

    # 📄 Extract text
    plate_text = ""
    if result:
        plate_text = result[0][1]  # First detected string

    cleaned_plate_text = clean_plate_text(plate_text)

    print("✅ Final Detected Plate:", cleaned_plate_text)

    url = f"http://127.0.0.1:8000/parking/log/?plate={plate_text}"

    # Send detected plate to your Django backend (as an entry)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ Logged to backend:", response.json())
        else:
            print("❌ Failed to log:", response.text)
    except Exception as e:
        print("❗ Error logging to backend:", e)

    # 🖍 Draw on image
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(
        image, plate_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
    )

    # Show cropped plate
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Detected")
    plt.axis("off")
    plt.show()
