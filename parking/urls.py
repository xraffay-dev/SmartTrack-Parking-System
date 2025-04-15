from django.urls import path
from . import views
from .views import analytics_view, vehicle_detail   

urlpatterns = [
    path('entry/', views.log_entry, name='log_entry'),
    path('exit/', views.log_exit, name='log_exit'),
    path('analytics/', analytics_view, name='analytics'),
    path('vehicle/<str:plate>/', vehicle_detail, name='vehicle_detail'),
]