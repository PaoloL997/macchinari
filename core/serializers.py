"""Serializers exposing machines to the frontend."""

from rest_framework import serializers

from .models import Machine


class MachineSerializer(serializers.ModelSerializer):
    """Public representation of a machine.

    Agent URL and token are intentionally excluded: they must never reach
    the browser.

    Attributes:
        plant: Name of the plant instead of its id.
        capabilities: Names of the capabilities declared in the manifest.
        files: Configuration of the "files" capability (accepted extensions
            and max size), or None if the machine does not support files.
    """

    plant = serializers.StringRelatedField()
    capabilities = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()

    class Meta:
        model = Machine
        fields = ["id", "name", "description", "plant", "illustration", "capabilities", "files"]

    def get_capabilities(self, machine: Machine) -> list[str]:
        """List the capabilities the machine exposes.

        Args:
            machine: Machine being serialized.

        Returns:
            Names of the capabilities present in the manifest (e.g. ["files", "status"]).
        """
        caps = machine.parsed_manifest.capabilities.model_dump()
        return [name for name, config in caps.items() if config is not None]

    def get_files(self, machine: Machine) -> dict | None:
        """Return the "files" configuration of the machine.

        Args:
            machine: Machine being serialized.

        Returns:
            A dict with "accept" and "max_mb", or None if not supported.
        """
        config = machine.parsed_manifest.capabilities.files
        return config.model_dump() if config else None