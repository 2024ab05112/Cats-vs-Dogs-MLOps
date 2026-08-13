"""URL configuration for dj_frontend."""
from django.urls import path, include

urlpatterns = [
    path("", include("webapp.urls")),
]
