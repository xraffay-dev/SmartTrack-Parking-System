from django.urls import path
from . import views
from .views import analytics_view, vehicle_detail, log_plate, launch_stream, upload_image

urlpatterns = [
    path("log/", log_plate, name="log_plate"),
    path("analytics/", analytics_view, name="analytics"),
    path("vehicle/<str:plate>/", vehicle_detail, name="vehicle_detail"),
    path("launch-stream/", launch_stream, name="launch_stream"),
    path("upload-image/", upload_image, name="upload_image"),
]
