from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    path('stat', views.stat),
    path("getstatus", views.getStatus)
]
