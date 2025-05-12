from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path("admin/", admin.site.urls),
    path("parking/", include("parking.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve files from entries directory in development
if settings.DEBUG:
    entries_dir = os.path.join(settings.BASE_DIR, 'entries')
    if not os.path.exists(entries_dir):
        os.makedirs(entries_dir)
    urlpatterns += static('/entries/', document_root=entries_dir)
