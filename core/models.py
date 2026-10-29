"""Database models for plants, machines and the operations performed on them."""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import FileExtensionValidator
from pydantic import ValidationError

from core.schemas import Manifest


class Plant(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class Machine(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)
    plant = models.ForeignKey(Plant, on_delete=models.PROTECT, related_name="machines")
    illustration = models.FileField(
        upload_to="illustrations/",
        validators=[FileExtensionValidator(["svg", "png", "webp"])],
        blank=True,
    )
    agent_url = models.URLField(help_text="E.g. http://100.x.y.z:8000 (Pi Tailscale IP)")
    agent_token = models.CharField(max_length=200)
    manifest = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["plant", "name"]

    def __str__(self):
        return f"{self.name} ({self.plant})"

    def clean(self):
        try:
            Manifest.model_validate(self.manifest)
        except ValidationError as e:
            raise DjangoValidationError({"manifest": str(e)})

    @property
    def parsed_manifest(self) -> Manifest:
        return Manifest.model_validate(self.manifest)

    def has_capability(self, name: str) -> bool:
        return getattr(self.parsed_manifest.capabilities, name, None) is not None

class Operation(models.Model):
    ACTIONS = [
        ("upload", "Upload"),
        ("delete", "Delete"),
    ]

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="operations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTIONS)
    filename = models.CharField(max_length=255)
    success = models.BooleanField()
    detail = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.action} {self.filename}"

