from django.urls import path
from . import views
from .views import analytics_view, vehicle_detail, log_plate

urlpatterns = [
    path("log/", log_plate, name="log_plate"),
    path("analytics/", analytics_view, name="analytics"),
    path("vehicle/<str:plate>/", vehicle_detail, name="vehicle_detail"),
]
