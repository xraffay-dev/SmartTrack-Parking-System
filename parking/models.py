from django.db import models
from django.utils import timezone

class Vehicle(models.Model):
    LICENSE_TYPE = [
        ('STAFF', 'Staff'),
        ('VISITOR', 'Visitor'),
    ]
    
    license_plate = models.CharField(max_length=20, unique=True)
    owner_name = models.CharField(max_length=100, blank=True, null=True)
    vehicle_type = models.CharField(max_length=10, choices=LICENSE_TYPE, default='VISITOR')
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.license_plate

class EntryExitLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(blank=True, null=True)
    image = models.ImageField(upload_to='plate_images/', blank=True, null=True)

    def duration(self):
        if self.exit_time:
            return self.exit_time - self.entry_time
        return None

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.entry_time.strftime('%Y-%m-%d %H:%M')}"
