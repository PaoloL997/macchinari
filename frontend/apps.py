"""App configuration of the frontend."""

from django.apps import AppConfig


class FrontendConfig(AppConfig):
    """Configuration of the "frontend" app, which serves the single-page portal."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "frontend"
