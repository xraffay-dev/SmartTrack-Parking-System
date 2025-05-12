from ultralytics import YOLO
import matplotlib.pyplot as plt
import easyocr
import requests
import argparse
import cv2
import re
import datetime


def clean_plate_text(plate_text):
    return re.sub(r"[^A-Z0-9]", "", plate_text.upper())


# 📦 Load YOLO model
model = YOLO("runs/detect/train3/weights/best.pt")

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--mode", default="entry", choices=["entry", "exit"])
parser.add_argument("--image", help="Path to the image file to process")
args = parser.parse_args()

# 📷 Load image
if args.image:
    image_path = args.image
else:
    image_path = f"./plate_dataset/test/images/car2.jpg"  # Default image

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

    # Save the full car image with the license plate number in the filename
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    image_filename = f"{cleaned_plate_text}_{timestamp}.jpg"
    image_path_save = f"entries/{image_filename}"
    cv2.imwrite(image_path_save, image)  # Save the full image instead of cropped
    print(f"✅ Full car image saved as: {image_path_save}")

    # Use GET request to avoid CSRF issues
    url = f"http://127.0.0.1:8000/parking/log/?plate={cleaned_plate_text}&mode={args.mode}"

    # Send detected plate to your Django backend (as an entry)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ Logged to backend:", response.json())
        else:
            print("❌ Failed to log:", response.text)
            
        # Save image separately - we'll just save it locally since GET can't send files
        print(f"✅ Image saved locally as: {image_path_save}")
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
