"""Serializers validating the input of the "files" API."""

from rest_framework import serializers


class UploadSerializer(serializers.Serializer):
    """Input of a file upload.

    Attributes:
        file: The uploaded file.
    """

    file = serializers.FileField()