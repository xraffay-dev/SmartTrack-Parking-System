from django.shortcuts import render
from django.http import JsonResponse
from .models import Vehicle, EntryExitLog
from django.utils import timezone

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
