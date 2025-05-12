from django.contrib import admin
from .models import Vehicle, EntryExitLog
from django.utils.html import format_html
from django.urls import reverse


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    change_list_template = "admin/parking/vehicle/change_list.html"
    list_display = ("license_plate", "view_history_link")

    def view_history_link(self, obj):
        # Generate the URL for the vehicle's detail page based on license_plate
        url = reverse("vehicle_detail", args=[obj.license_plate])
        return format_html(
            f'<a href="{url}" target="_blank" class="button">View History</a>'
        )

    view_history_link.short_description = "History"

    def changelist_view(self, request, extra_context=None):
        # Add custom extra context for the changelist view
        if extra_context is None:
            extra_context = {}
        extra_context["show_analytics_button"] = True
        extra_context["analytics_url"] = reverse(
            "analytics"
        )  # URL for the analytics page
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(EntryExitLog)
class EntryExitLogAdmin(admin.ModelAdmin):
    change_list_template = "admin/parking/vehicle/change_list.html"
    list_display = ("vehicle", "entry_time", "exit_time", "get_duration_readable", "get_image_icon")

    def get_duration_readable(self, obj):
        if obj.exit_time and obj.entry_time:
            duration = obj.exit_time - obj.entry_time
            total_seconds = int(duration.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            hours, minutes = divmod(minutes, 60)
            return (
                f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s"
            )
        return "-"

    get_duration_readable.short_description = "Duration"

    def get_image_icon(self, obj):
        if obj.image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="height:32px;width:auto;"/></a>',
                obj.image.url, obj.image.url
            )
        else:
            return "-"
    get_image_icon.short_description = "Image"
    get_image_icon.allow_tags = True

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context["show_analytics_button"] = True
        extra_context["analytics_url"] = reverse("analytics")
        return super().changelist_view(request, extra_context=extra_context)
