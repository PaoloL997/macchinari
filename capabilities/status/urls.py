"""URLs of the "status" capability API."""

from django.urls import path

from .views import StatusView

urlpatterns = [
    path("machines/<int:machine_id>/status/", StatusView.as_view(), name="status"),
]