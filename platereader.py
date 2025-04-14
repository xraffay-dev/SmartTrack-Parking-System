from ultralytics import YOLO
import cv2
import easyocr
import matplotlib.pyplot as plt

# 📦 Load YOLO model
model = YOLO("runs/detect/train3/weights/best.pt")

# 📷 Load image
# image_path = "./plate_dataset/test/images/car469.jpg"
image_path = "car2.jpg"

image = cv2.imread(image_path)

# 🧠 Init OCR Reader (English only to avoid noise)
reader = easyocr.Reader(['en'])

# 🔍 Detect plate
results = model(image_path)

for box in results[0].boxes.xyxy:
    x1, y1, x2, y2 = map(int, box)
    cropped = image[y1:y2, x1:x2]

    # 🧪 Run EasyOCR
    result = reader.readtext(cropped)

    # 📄 Extract text
    plate_text = ''
    if result:
        plate_text = result[0][1]  # First detected string

    print("✅ Final Detected Plate:", plate_text)

    # 🖍 Draw on image
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(image, plate_text, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Show cropped plate
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Detected")
    plt.axis("off")
    plt.show()