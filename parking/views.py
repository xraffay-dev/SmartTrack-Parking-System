import re
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from django.http import JsonResponse
from .models import Vehicle, EntryExitLog, ParkingLog
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg, DurationField, ExpressionWrapper, F
from django.db import transaction, IntegrityError


def normalize_plate(plate):
    return re.sub(r"[^A-Z0-9]", "", plate.upper())


def format_duration(duration):
    if not duration:
        return "N/A"
    total_seconds = int(duration.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s"


def log_plate(request):
    plate = request.GET.get("plate") if request.method == "GET" else request.POST.get("plate")
    if not plate:
        return JsonResponse({"error": "Plate not provided"}, status=400)

    plate = re.sub(r"[^A-Z0-9]", "", plate.upper().strip())
    image_file = request.FILES.get("image") if request.method == "POST" else None

    try:
        with transaction.atomic():
            vehicle, created = Vehicle.objects.select_for_update().get_or_create(license_plate=plate)

            open_log = EntryExitLog.objects.filter(vehicle=vehicle, is_open=True).order_by('-entry_time').first()
            if open_log:
                open_log.is_open = False
                open_log.exit_time = now()
                open_log.save()
                duration = open_log.exit_time - open_log.entry_time
                return JsonResponse({
                    "action": "exit",
                    "plate": plate,
                    "entry_time": open_log.entry_time,
                    "exit_time": open_log.exit_time,
                    "duration": str(duration),
                    "message": "Exit logged"
                })

            entry_log = EntryExitLog.objects.create(vehicle=vehicle, entry_time=now(), is_open=True)
            if image_file:
                entry_log.image.save(image_file.name, image_file)
                entry_log.save()
            ParkingLog.objects.create(plate=plate, entry_time=entry_log.entry_time)
            return JsonResponse({
                "action": "entry",
                "plate": plate,
                "entry_time": entry_log.entry_time,
                "message": "Entry logged"
            })
    except IntegrityError as e:
        return JsonResponse({
            "error": "Could not create entry due to a race condition. Please try again."
        }, status=500)
    except Exception as e:
        return JsonResponse({
            "error": f"Unexpected error: {e}"
        }, status=500)


def analytics_view(request):
    total_logs = EntryExitLog.objects.count()
    currently_parked = EntryExitLog.objects.filter(exit_time__isnull=True).count()

    durations = EntryExitLog.objects.exclude(exit_time__isnull=True).annotate(
        duration=ExpressionWrapper(
            F("exit_time") - F("entry_time"), output_field=DurationField()
        )
    )
    avg_duration = durations.aggregate(avg=Avg("duration"))["avg"]
    avg_duration_readable = format_duration(avg_duration)

    top_vehicles = (
        EntryExitLog.objects.values("vehicle__license_plate")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    context = {
        "total_logs": total_logs,
        "currently_parked": currently_parked,
        "avg_duration": avg_duration_readable,
        "top_vehicles": top_vehicles,
    }

    return render(request, "parking/analytics.html", context)


def vehicle_detail(request, plate):
    vehicle = get_object_or_404(Vehicle, license_plate=plate.upper())
    logs = EntryExitLog.objects.filter(vehicle=vehicle).order_by("entry_time")

    total_visits = logs.count()
    total_time = timedelta()
    currently_parked = False
    days_visited = set()
    log_data = []

    completed_visits = 0

    for log in logs:
        duration = None
        if log.exit_time:
            duration = log.exit_time - log.entry_time
            total_time += duration
            completed_visits += 1
        else:
            currently_parked = True

        days_visited.add(log.entry_time.date())

        log_data.append(
            {
                "entry_time": log.entry_time,
                "exit_time": log.exit_time,
                "duration": format_duration(duration),
            }
        )

    avg_duration = total_time / completed_visits if completed_visits else None

    context = {
        "vehicle": vehicle,
        "logs": log_data,
        "total_visits": total_visits,
        "total_time": format_duration(total_time),
        "avg_duration": format_duration(avg_duration),
        "days_visited": len(days_visited),
        "currently_parked": currently_parked,
    }

    return render(request, "parking/vehicle_detail.html", context)


def launch_stream(request):
    import subprocess
    import os
    import sys
    from django.shortcuts import redirect
    
    try:
        python_exe = sys.executable
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        stream_script_path = os.path.join(project_dir, 'stream.py')
        
        entries_dir = os.path.join(project_dir, 'entries')
        if not os.path.exists(entries_dir):
            os.makedirs(entries_dir)
        
        subprocess.Popen(
            [python_exe, stream_script_path],
            cwd=project_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        print(f"Camera launched with: {python_exe} {stream_script_path}")
    except Exception as e:
        print(f"Error launching camera: {e}")
    
    referer = request.META.get('HTTP_REFERER', '/admin/parking/vehicle/')
    return redirect(referer)


def upload_image(request):
    import subprocess
    import os
    import tempfile
    import shutil
    from django.shortcuts import render, redirect
    from .models import Vehicle, EntryExitLog
    
    if request.method == 'POST' and request.FILES.get('image'):
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        entries_dir = os.path.join(project_dir, 'entries')
        if not os.path.exists(entries_dir):
            os.makedirs(entries_dir)
            
        uploaded_image = request.FILES['image']
        
        temp_path = os.path.join(entries_dir, f'temp_{uploaded_image.name}')
        with open(temp_path, 'wb+') as destination:
            for chunk in uploaded_image.chunks():
                destination.write(chunk)
        
        try:
            import sys
            sys.path.append(project_dir)
            from ultralytics import YOLO
            import easyocr
            import re
            import cv2
            import datetime
            
            model = YOLO(os.path.join(project_dir, "runs/detect/train3/weights/best.pt"))
            reader = easyocr.Reader(["en"])
            image = cv2.imread(temp_path)
            
            results = model(image)
            
            plate_text = ""
            for box in results[0].boxes.xyxy:
                x1, y1, x2, y2 = map(int, box)
                cropped = image[y1:y2, x1:x2]
                ocr_result = reader.readtext(cropped)
                if ocr_result:
                    plate_text = ocr_result[0][1]
                    break
            
            cleaned_plate_text = re.sub(r"[^A-Z0-9]", "", plate_text.upper())
            
            if cleaned_plate_text:
                try:
                    vehicle = Vehicle.objects.get(license_plate=cleaned_plate_text)
                    open_log = EntryExitLog.objects.filter(vehicle=vehicle, is_open=True).first()
                    if open_log:
                        mode = "exit"
                    else:
                        mode = "entry"
                except Vehicle.DoesNotExist:
                    mode = "entry"
                
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                final_filename = f"{cleaned_plate_text}_{timestamp}.jpg"
                final_path = os.path.join(entries_dir, final_filename)
                
                if os.path.exists(final_path):
                    os.remove(final_path)
                    
                shutil.move(temp_path, final_path)
                
                log_url = f"http://127.0.0.1:8000/parking/log/?plate={cleaned_plate_text}"
                import requests
                response = requests.get(log_url)
                api_response = response.json() if response.status_code == 200 else {"error": response.text}
                
                context = {
                    'success': True,
                    'output': f"✅ Plate detected: {cleaned_plate_text}\n✅ Mode determined: {mode}\n✅ Image saved as: {final_path}\n✅ API Response: {api_response}",
                    'plate_number': cleaned_plate_text,
                    'mode': mode,
                    'image_path': f'/entries/{final_filename}'
                }
            else:
                context = {
                    'success': False,
                    'output': "❌ No license plate detected in the image.",
                    'plate_number': None,
                    'mode': None
                }
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            context = {
                'success': False,
                'output': f"❌ Error processing image: {str(e)}",
                'plate_number': None,
                'mode': None
            }
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        return render(request, 'parking/upload_result.html', context)
    
    return render(request, 'parking/upload_image.html', {})
