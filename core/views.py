"""API views for machines."""

from rest_framework import viewsets

from .models import Machine
from .serializers import MachineSerializer


class MachineViewSet(viewsets.ReadOnlyModelViewSet):
    """List active machines and show the details of a single machine."""

    queryset = Machine.objects.filter(active=True).select_related("plant")
    serializer_class = MachineSerializer