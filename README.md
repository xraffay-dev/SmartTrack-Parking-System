# SmartTrack Parking System

A comprehensive parking management system with automatic license plate recognition capabilities for tracking vehicle entry and exit.

![SmartTrack](https://img.shields.io/badge/SmartTrack-Parking%20System-blue)

## Overview

SmartTrack is an intelligent parking management solution that uses computer vision to automate vehicle tracking in parking facilities. The system captures license plates through camera feeds, logs entry and exit times, and provides detailed analytics about parking usage patterns.

## Key Features

- **Automated License Plate Recognition**: Uses YOLO object detection and EasyOCR to detect and read license plates from images or live camera feed
- **Entry/Exit Tracking**: Automatically logs when vehicles enter and exit the parking facility
- **Real-time Camera Interface**: Interactive UI for capturing and processing license plates in real-time
- **Manual Entry Option**: Supports manual license plate entry when automatic detection fails
- **Comprehensive Analytics**: Track parking durations, frequent visitors, and current capacity
- **Admin Dashboard**: Django admin interface with custom controls for system management
- **Image Storage**: Saves timestamped images of vehicles with their license plates
- **REST API**: Simple API endpoints for logging plate data and retrieving information

## Technology Stack

- **Backend**: Django
- **Computer Vision**: YOLO (YOLOv8), EasyOCR
- **UI**: Tkinter (for camera application), Django Templates, TailwindCSS (for styling)   
- **Database**: SQLite (default, can be configured for other databases)
- **Image Processing**: OpenCV

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

---

Developed with ❤️ by [Your Name/Organization]
