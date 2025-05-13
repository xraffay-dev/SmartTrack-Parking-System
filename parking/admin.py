from django.contrib import admin
from .models import Vehicle, EntryExitLog
from django.utils.html import format_html
from django.urls import reverse


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    change_list_template = "admin/parking/vehicle/change_list.html"
    list_display = ("license_plate", "view_history_link")

    def view_history_link(self, obj):
        url = reverse("vehicle_detail", args=[obj.license_plate])
        return format_html(
            f'<a href="{url}" target="_blank" class="button" style>View History</a>'
        )

    view_history_link.short_description = "History"

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context["show_analytics_button"] = True
        extra_context["analytics_url"] = reverse(
            "analytics"
        )
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(EntryExitLog)
class EntryExitLogAdmin(admin.ModelAdmin):
    change_list_template = "admin/parking/vehicle/change_list.html"
    list_display = ("vehicle", "entry_time", "exit_time", "get_duration_readable", "get_entry_image", "get_exit_image")

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
    
    def get_entry_image(self, obj):
        import os
        from django.conf import settings
        
        license_plate = obj.vehicle.license_plate.strip().upper()
        
        entry_timestamp = obj.entry_time.strftime('%Y%m%d_%H%M%S')
        
        entries_dir = os.path.join(settings.BASE_DIR, 'entries')
        if os.path.exists(entries_dir):
            entry_image_prefix = f"{license_plate}_{entry_timestamp[:8]}"  # Match the date part
            
            for filename in os.listdir(entries_dir):
                if filename.startswith(license_plate) and entry_timestamp[:8] in filename:
                    image_url = f"/entries/{filename}"
                    return format_html(
                        '<a href="{}" target="_blank"><img src="{}" style="height:32px;width:auto;" title="{}" /></a>',
                        image_url, image_url, filename
                    )
        
        if obj.image and not obj.exit_time:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="height:32px;width:auto;"/></a>',
                obj.image.url, obj.image.url
            )
            
        return "-"
    
    get_entry_image.short_description = "Entry Image"
    get_entry_image.allow_tags = True

    def get_exit_image(self, obj):
        import os
        from django.conf import settings
        import datetime
        
        if not obj.exit_time:
            return "-"
            
        license_plate = obj.vehicle.license_plate.strip().upper()
        
        entry_time = obj.entry_time
        exit_time = obj.exit_time
        
        buffer_before = exit_time - datetime.timedelta(minutes=5)
        buffer_after = exit_time + datetime.timedelta(minutes=5)
        
        entry_timestamp_str = entry_time.strftime('%Y%m%d_%H%M%S')
        
        entries_dir = os.path.join(settings.BASE_DIR, 'entries')
        if os.path.exists(entries_dir):
            matching_files = []
            for filename in os.listdir(entries_dir):
                if filename.startswith(license_plate):
                    try:
                        parts = filename.split('_')
                        if len(parts) >= 3:
                            timestamp_str = f"{parts[1]}_{parts[2].split('.')[0]}"
                            
                            if timestamp_str <= entry_timestamp_str:
                                continue
                                
                            matching_files.append((filename, timestamp_str))
                    except Exception as e:
                        print(f"Error parsing filename {filename}: {e}")
                        continue
            
            if matching_files:
                matching_files.sort(key=lambda x: x[1], reverse=True)
                
                exit_filename, _ = matching_files[0]
                image_url = f"/entries/{exit_filename}"
                return format_html(
                    '<a href="{}" target="_blank"><img src="{}" style="height:32px;width:auto;" title="{}" /></a>',
                    image_url, image_url, exit_filename
                )
        
        if obj.image:
            try:
                image_name = os.path.basename(obj.image.name)
                entry_image_html = self.get_entry_image(obj)
                if entry_image_html != "-" and image_name in entry_image_html:
                    return "-" 
                
                return format_html(
                    '<a href="{}" target="_blank"><img src="{}" style="height:32px;width:auto;"/></a>',
                    obj.image.url, obj.image.url
                )
            except:
                pass
            
        return "-"
    
    get_exit_image.short_description = "Exit Image"
    get_exit_image.allow_tags = True

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context["show_analytics_button"] = True
        extra_context["analytics_url"] = reverse("analytics")
        return super().changelist_view(request, extra_context=extra_context)
