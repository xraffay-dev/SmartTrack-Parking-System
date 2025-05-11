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
    # Remove all non-alphanumeric characters and make uppercase
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

    # Normalize plate before any DB operation
    plate = re.sub(r"[^A-Z0-9]", "", plate.upper().strip())
    image_file = request.FILES.get("image") if request.method == "POST" else None

    try:
        with transaction.atomic():
            vehicle, created = Vehicle.objects.select_for_update().get_or_create(license_plate=plate)

            open_log = EntryExitLog.objects.filter(vehicle=vehicle, is_open=True).order_by('-entry_time').first()
            if open_log:
                # Mark exit only, do NOT create a new entry
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

            # No open log, create new entry
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

    # Parking duration (only logs with exits)
    durations = EntryExitLog.objects.exclude(exit_time__isnull=True).annotate(
        duration=ExpressionWrapper(
            F("exit_time") - F("entry_time"), output_field=DurationField()
        )
    )
    avg_duration = durations.aggregate(avg=Avg("duration"))["avg"]
    avg_duration_readable = format_duration(avg_duration)

    # Most frequent vehicles
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
