from django.shortcuts import render
from django.http import JsonResponse
from .models import Vehicle, EntryExitLog
from django.utils import timezone
from django.db.models import Count, Avg, Q, DurationField, ExpressionWrapper, F
from django.shortcuts import get_object_or_404
from datetime import timedelta
import datetime

def format_duration(duration):
    if not duration:
        return "N/A"
    total_seconds = int(duration.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s"

def log_entry(request):
    license_plate = request.GET.get('plate')
    if not license_plate:
        return JsonResponse({'error': 'License plate required'}, status=400)

    vehicle, _ = Vehicle.objects.get_or_create(license_plate=license_plate.upper())

    EntryExitLog.objects.create(vehicle=vehicle)
    return JsonResponse({'status': 'Entry logged', 'plate': license_plate})

def log_exit(request):
    license_plate = request.GET.get('plate')
    if not license_plate:
        return JsonResponse({'error': 'License plate required'}, status=400)

    try:
        vehicle = Vehicle.objects.get(license_plate=license_plate.upper())
        log = EntryExitLog.objects.filter(vehicle=vehicle, exit_time__isnull=True).latest('entry_time')
        log.exit_time = timezone.now()
        log.save()
        return JsonResponse({'status': 'Exit logged', 'duration': str(log.duration())})
    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Vehicle not found'}, status=404)
    except EntryExitLog.DoesNotExist:
        return JsonResponse({'error': 'No active entry found for this vehicle'}, status=404)

def analytics_view(request):
    total_logs = EntryExitLog.objects.count()
    currently_parked = EntryExitLog.objects.filter(exit_time__isnull=True).count()

    # Parking duration (only logs with exits)
    durations = EntryExitLog.objects.exclude(exit_time__isnull=True).annotate(
        duration=ExpressionWrapper(F('exit_time') - F('entry_time'), output_field=DurationField())
    )
    avg_duration = durations.aggregate(avg=Avg('duration'))['avg']
    avg_duration_readable = format_duration(avg_duration)
    
    # Most frequent vehicles
    top_vehicles = EntryExitLog.objects.values('vehicle__license_plate') \
        .annotate(count=Count('id')) \
        .order_by('-count')[:5]

    context = {
        'total_logs': total_logs,
        'currently_parked': currently_parked,
        'avg_duration': avg_duration_readable,
        'top_vehicles': top_vehicles,
    }

    return render(request, 'parking/analytics.html', context)

def vehicle_detail(request, plate):
    vehicle = Vehicle.objects.get(license_plate=plate)
    logs = EntryExitLog.objects.filter(vehicle=vehicle).order_by('entry_time')

    total_visits = logs.count()
    total_time = timedelta()
    formated_total_time = format_duration(total_time)
    currently_parked = False
    days_visited = set()

    log_data = []

    for log in logs:
        duration = None
        if log.exit_time:
            duration = log.exit_time - log.entry_time
            total_time += duration
        else:
            currently_parked = True
        days_visited.add(log.entry_time.date())
        formated_duration = format_duration(duration)
        log_data.append({
            'entry_time': log.entry_time,
            'exit_time': log.exit_time,
            'duration': formated_duration,
        })

    context = {
        'vehicle': vehicle,
        'logs': log_data,
        'total_visits': total_visits,
        'total_time': str(format_duration(total_time)),
        'days_visited': len(days_visited),
        'currently_parked': currently_parked,
    }
    return render(request, 'parking/vehicle_detail.html', context)