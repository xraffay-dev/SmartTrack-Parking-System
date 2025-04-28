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
- 🧠 **Automatic Entry and Exit** logging
- 🗂️ Full Admin Dashboard with:
  - Vehicle History Tracking
  - Visit Logs & Parking Durations
  - Average Time Parked
  - Number of Days Visited
- 💵 **Billing system** — charge **50 Rs per hour** based on parking duration
- 🎨 Enhanced, Modernized Django Admin Theme
- 📷 Mobile Camera (iPhone via iVCam) or Webcam Live Stream Integration
- 📊 Batch Processing Support for Testing Multiple Vehicles at Once

---

## 🚀 Tech Stack

- **Backend:** Django (Python)
- **Detection:** YOLOv8 (Ultralytics)
- **OCR:** EasyOCR
- **Frontend:** TailwindCSS (Custom templates)
- **Database:** SQLite
- **Streaming:** OpenCV
- **Admin Styling:** django-admin-interface

---

## 🛠 Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/smarttrack.git
cd smarttrack
```
### 2. Create and Activate Virtual Environment
```bash
python -m venv env
env\Scripts\activate   # Windows
source env/bin/activate # Mac/Linux
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
_(If needed manually install: ultralytics, easyocr, django-admin-interface, etc.)_
### 4. Apply Migrations
```bash
python manage.py migrate
```
### 5. Create Superuser
```bash
python manage.py createsuperuser
```
### 6. Run the Server
```bash
python manage.py runserver
```
Go to: http://127.0.0.1:8000/admin
### Live Stream Setup (Optional)
You can connect your iPhone (via iVCam) or webcam to OpenCV.
```bash
python stream.py
```
Detected plates will automatically be logged!
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
├── batch_plateLogger.py      # Batch testing script
├── stream.py                 # Live camera feed detection
├── db.sqlite3                # Default SQLite database
├── manage.py
```
### 🎯 Future Enhancements
- 🔔 Real-time Notifications on Entry/Exit (Email/SMS)
- 🛡️ Vehicle Type Classification (Car, Bike, Truck)
- 📈 Revenue Reports and Graphs
- 📅 Monthly Pass System
- ☁️ Deploy on Heroku / AWS / DigitalOcean
- 📱 Mobile App Extension (React Native / Flutter)

###  📜 License
This project is licensed under the MIT License.
Feel free to use, modify, and contribute!

###  Credits
## 🤝 Credits

- [Django Framework](https://www.djangoproject.com/)
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [django-admin-interface](https://github.com/fabiocaccamo/django-admin-interface)
- [OpenCV](https://opencv.org/)
