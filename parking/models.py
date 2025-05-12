from django.db import models
from django.utils import timezone
import os
import re


class Vehicle(models.Model):
    license_plate = models.CharField(max_length=20, unique=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        self.license_plate = re.sub(r"[^A-Z0-9]", "", self.license_plate.upper().strip())

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ("license_plate",)

    def __str__(self):
        return self.license_plate


def entry_image_upload_path(instance, filename):
    plate = instance.vehicle.license_plate.replace(' ', '').replace('-', '')
    entry_time = instance.entry_time.strftime('%Y%m%d_%H%M%S') if instance.entry_time else timezone.now().strftime('%Y%m%d_%H%M%S')
    ext = os.path.splitext(filename)[1] or '.jpg'
    return f'entries/{plate}_{entry_time}{ext}'


class EntryExitLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(blank=True, null=True)
    image = models.ImageField(upload_to=entry_image_upload_path, blank=True, null=True)
    is_open = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["vehicle", "is_open"], name="unique_open_log_per_vehicle")
        ]

    def duration(self):
        if self.exit_time:
            return self.exit_time - self.entry_time
        return None

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.entry_time.strftime('%Y-%m-%d %H:%M')}"


class ParkingLog(models.Model):
    plate = models.CharField(max_length=20)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    charge = models.IntegerField(null=True, blank=True)

    def calculate_charge(self):
        if self.exit_time:
            duration = self.exit_time - self.entry_time
            hours = duration.total_seconds() / 3600
            return int(hours * 50)
        return 0
