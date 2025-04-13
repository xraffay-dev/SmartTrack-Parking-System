# from django.contrib import admin
# from .models import Vehicle, EntryExitLog

# admin.site.register(Vehicle)
# admin.site.register(EntryExitLog)

from django.contrib import admin
from .models import Vehicle, EntryExitLog

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('license_plate',)

@admin.register(EntryExitLog)
class EntryExitLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'entry_time', 'exit_time', 'duration')
    list_filter = ('entry_time', 'exit_time')
    search_fields = ('vehicle__license_plate',)
