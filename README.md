# 🚗 SmartTrack - Intelligent Parking and Vehicle Monitoring System
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Project-Active-brightgreen)

Welcome to **SmartTrack** — an intelligent, automated parking management system built using **Django**, **YOLOv8**, **EasyOCR**, and **OpenCV**.

SmartTrack uses **real-time license plate detection** to automatically log vehicle entries and exits.  
It also provides **beautiful analytics** and a customized **admin panel** for full parking control and billing.

---

## ✨ Features

- 📸 Real-time **License Plate Recognition** (YOLOv8 + EasyOCR)
- 🧠 **Automatic Entry and Exit logging**
- 🗂️ Full Admin Dashboard with:
  - Vehicle History Tracking
  - Vehicle Snapshots as Proof of Entry and Exit
  - Visit Logs & Parking Durations
  - Average Time Parked
  - Number of Days Visited
- 🎨 Enhanced, Modernized Django Admin Theme
- 📷 Mobile Camera (iPhone via iVCam) or Webcam Live Stream Integration

---

## 🚀 Tech Stack

- **Backend**: Django
- **Computer Vision**: YOLO (YOLOv8), EasyOCR
- **UI**: Tkinter (for camera application), Django Templates, TailwindCSS (for styling)   
- **Database**: SQLite (default, can be configured for other databases)
- **Image Processing**: OpenCV

---

## Installation

### Prerequisites

- Python 3.8+
- Pip package manager
- Webcam (for live detection)
- CUDA-compatible GPU (recommended for better performance)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/smarttrack.git
   cd smarttrack
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser for admin access:
   ```bash
   python manage.py createsuperuser
   ```

6. Make sure the YOLO model is available at `runs/detect/train3/weights/best.pt`
   - The system will run in manual entry mode if the model is not found

7. Create the `entries` directory if it doesn't exist:
   ```bash
   mkdir entries
   ```

## Usage

### Running the Django Server

```bash
python manage.py runserver
```

Access the admin interface at http://127.0.0.1:8000/admin/

### Starting the Camera Interface

You can start the camera interface through:

1. Django admin interface - Use the "Start Camera" button on the Vehicle admin page
2. Directly running the stream script:
   ```bash
   python stream.py
   ```

### Processing Static Images

To process an existing image file for license plate detection:

```bash
python plateLogger.py --image path/to/image.jpg --mode entry
```

Alternatively, use the web upload form at http://127.0.0.1:8000/parking/upload/

### 🧩 Project Structure
```
smarttrack/
├── parking/                 # Main Django App
│   ├── admin.py              # Admin customization
│   ├── models.py             # Models (Vehicle, EntryExitLog)
│   ├── views.py              # Views (entry, exit, analytics, history)
│   ├── templates/            # Custom templates (analytics.html, vehicle_detail.html)
│   ├── static/               # Tailwind CSS files (optional)
├── plateLogger.py            # Single image plate detection and logging
├── stream.py                 # Live camera feed detection
├── db.sqlite3                # Default SQLite database
├── manage.py
```
## System Components

### Models

- **Vehicle**: Stores vehicle information with unique license plates
- **EntryExitLog**: Records vehicle entry and exit timestamps along with images
- **ParkingLog**: Tracks parking duration and can calculate charges

### Scripts

- **stream.py**: Provides real-time camera interface for license plate detection
- **plateLogger.py**: Processes static images for license plate detection and logging

### Views

- **log_plate**: API endpoint for recording entry/exit events
- **analytics_view**: Provides parking usage statistics
- **vehicle_detail**: Shows detailed history for a specific vehicle
- **upload_image**: Web interface for uploading and processing images

## API Endpoints

- `GET /parking/log/?plate={license_plate}` - Log a vehicle entry or exit
- `GET /parking/analytics/` - View parking analytics dashboard
- `GET /parking/vehicle/{license_plate}/` - View details for a specific vehicle
- `GET /parking/upload/` - Upload and process images

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


### 🎯 Future Enhancements
- 🔔 Real-time Notifications on Entry/Exit (Email/SMS)
- 🛡️ Vehicle Type Classification (Car, Bike, Truck)
- 📈 Revenue Reports and Graphs
- 📅 Monthly Pass System
- ☁️ Deploy on Heroku / AWS / DigitalOcean
- 📱 Mobile App Extension (React Native / Flutter)

Feel free to use, modify, and contribute!

---

###  Credits
## 🤝 Credits

- [Django Framework](https://www.djangoproject.com/)
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [django-admin-interface](https://github.com/fabiocaccamo/django-admin-interface)
- [OpenCV](https://opencv.org/)

---
