from django.urls import path
from . import views
from .views import analytics_view

urlpatterns = [
    path('entry/', views.log_entry, name='log_entry'),
    path('exit/', views.log_exit, name='log_exit'),
     path('analytics/', analytics_view, name='analytics'),
]
