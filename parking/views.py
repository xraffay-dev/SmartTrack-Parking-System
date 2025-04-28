import re
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from django.http import JsonResponse
from .models import Vehicle, EntryExitLog, ParkingLog
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg, DurationField, ExpressionWrapper, F


def normalize_plate(plate):
    # Remove all non-alphanumeric characters
    cleaned = re.sub(r"[^A-Za-z0-9]", "", plate).upper()

    # Split letters and digits
    match = re.match(r"^([A-Z]+)(\d+)$", cleaned)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return cleaned  # fallback if pattern doesn't match


def format_duration(duration):
    if not duration:
        return "N/A"
    total_seconds = int(duration.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s"


def log_plate(request):
    plate = request.GET.get("plate")
    mode = request.GET.get("mode", "entry")

    if not plate:
        return JsonResponse({"error": "Plate not provided"}, status=400)

    plate = normalize_plate(plate)

    if mode == "entry":
        # --- Parking Log ---
        open_logs = ParkingLog.objects.filter(plate=plate, exit_time__isnull=True)
        if open_logs.exists():
            # Reuse exit logic by changing mode to exit
            request.GET = request.GET.copy()
            request.GET["mode"] = "exit"
            return log_plate(request)

        ParkingLog.objects.create(plate=plate, entry_time=now())

        # --- EntryExitLog ---
        # Check if vehicle exists, otherwise create it
        vehicle, _ = Vehicle.objects.get_or_create(license_plate=plate)

        EntryExitLog.objects.create(vehicle=vehicle, entry_time=now())

        return JsonResponse({"message": "Entry logged", "plate": plate})

    elif mode == "exit":
        try:
            # --- Parking Log ---
            log = ParkingLog.objects.get(plate=plate, exit_time__isnull=True)
            log.exit_time = now()
            log.charge = log.calculate_charge()
            log.save()

            # --- EntryExitLog ---
            # find open EntryExitLog and close it
            vehicle = Vehicle.objects.get(license_plate=plate)
            open_log = EntryExitLog.objects.filter(
                vehicle=vehicle, exit_time__isnull=True
            ).first()
            if open_log:
                open_log.exit_time = now()
                open_log.save()

            return JsonResponse(
                {
                    "message": "Exit logged",
                    "plate": plate,
                    "duration": str(log.exit_time - log.entry_time),
                    "charge": log.charge,
                }
            )
        except (ParkingLog.DoesNotExist, Vehicle.DoesNotExist):
            return JsonResponse(
                {"error": "No active entry found for this plate"}, status=404
            )

    return JsonResponse({"error": "Invalid mode"}, status=400)


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

    completed_visits = 0  # count only visits with exit_time

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
