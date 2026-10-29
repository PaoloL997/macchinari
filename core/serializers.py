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
    """

    plant = serializers.StringRelatedField()
    capabilities = serializers.SerializerMethodField()

    class Meta:
        model = Machine
        fields = ["id", "name", "description", "plant", "illustration", "capabilities"]

    def get_capabilities(self, machine: Machine) -> list[str]:
        """List the capabilities the machine exposes.

        Args:
            machine: Machine being serialized.

        Returns:
            Names of the capabilities present in the manifest (e.g. ["files", "status"]).
        """
        caps = machine.parsed_manifest.capabilities.model_dump()
        return [name for name, config in caps.items() if config is not None]