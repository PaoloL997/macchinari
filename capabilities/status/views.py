"""API views of the "status" capability."""

from rest_framework import status as http_status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.models import Machine

from . import services


class StatusView(GenericAPIView):
    """Return the current state of a machine (GET).

    Attributes:
        queryset: Machines the API can work on (only active ones).
        lookup_url_kwarg: Name of the URL parameter holding the machine id.
    """

    queryset = Machine.objects.filter(active=True)
    lookup_url_kwarg = "machine_id"

    def get(self, request, machine_id):
        """Return the machine status.

        Args:
            request: The current HTTP request.
            machine_id: Primary key of the machine.

        Returns:
            A response with the machine status, or 404 if the machine
            does not support status.
        """
        machine = self.get_object()
        try:
            result = services.get_status(machine)
        except services.CapabilityNotAvailable as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_404_NOT_FOUND)
        return Response(result.model_dump())