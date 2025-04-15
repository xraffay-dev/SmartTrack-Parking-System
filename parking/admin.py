from django.contrib import admin
from .models import Vehicle, EntryExitLog
from django.utils.html import format_html
from django.urls import reverse




@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'vehicle_type', 'owner_name', 'view_history_link')

    def view_history_link(self, obj):
        url = reverse('vehicle_detail', args=[obj.license_plate])
        return format_html(f'<a href="{url}" target="_blank">View History</a>')

    view_history_link.short_description = 'History'

@admin.register(EntryExitLog)
class EntryExitLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'entry_time', 'exit_time', 'duration')
    list_filter = ('entry_time', 'exit_time')
    search_fields = ('vehicle__license_plate',)
