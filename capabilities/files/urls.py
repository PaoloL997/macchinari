"""URLs of the "files" capability API."""

from django.urls import path

from .views import FileDetailView, FileListView

urlpatterns = [
    path("machines/<int:machine_id>/files/", FileListView.as_view(), name="files-list"),
    path("machines/<int:machine_id>/files/<str:name>/", FileDetailView.as_view(), name="files-detail"),
]