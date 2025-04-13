from django.urls import path
from . import views

urlpatterns = [
    path('entry/', views.log_entry, name='log_entry'),
    path('exit/', views.log_exit, name='log_exit'),
]
