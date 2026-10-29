"""API views of the "files" capability."""

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from core.client import AgentError
from core.models import Machine

from . import services
from .serializers import UploadSerializer


def current_user(request):
    """Return the logged-in user, or None for anonymous requests.

    Args:
        request: The current HTTP request.

    Returns:
        The authenticated user or None.
    """
    return request.user if request.user.is_authenticated else None


def error_response(error: Exception) -> Response:
    """Translate a service error into an HTTP response.

    Args:
        error: Exception raised by the files services.

    Returns:
        A response with a status code matching the error.
    """
    if isinstance(error, services.CapabilityNotAvailable):
        return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(error, services.FileRejected):
        return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class MachineFilesBaseView(GenericAPIView):
    """Base view for the files API: resolves the machine from the URL.

    Attributes:
        queryset: Machines the API can work on (only active ones).
        lookup_url_kwarg: Name of the URL parameter holding the machine id.
    """

    queryset = Machine.objects.filter(active=True)
    lookup_url_kwarg = "machine_id"


class FileListView(MachineFilesBaseView):
    """List the files of a machine (GET) or upload a new one (POST)."""

    serializer_class = UploadSerializer
    parser_classes = [MultiPartParser]

    def get(self, request, machine_id):
        """Return the names of the files on the machine.

        Args:
            request: The current HTTP request.
            machine_id: Primary key of the machine.

        Returns:
            A response with the list of file names.
        """
        machine = self.get_object()
        try:
            names = services.list_files(machine)
        except (services.CapabilityNotAvailable, AgentError) as e:
            return error_response(e)
        return Response(names)

    def post(self, request, machine_id):
        """Upload a file to the machine.

        Args:
            request: The current HTTP request, with the file in the "file" field.
            machine_id: Primary key of the machine.

        Returns:
            A response with the uploaded file name, or an error.
        """
        machine = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded = serializer.validated_data["file"]
        try:
            services.upload_file(machine, uploaded.name, uploaded.read(), current_user(request))
        except (services.CapabilityNotAvailable, services.FileRejected, AgentError) as e:
            return error_response(e)
        return Response({"uploaded": uploaded.name}, status=status.HTTP_201_CREATED)


class FileDetailView(MachineFilesBaseView):
    """Delete a single file from a machine (DELETE)."""

    def delete(self, request, machine_id, name):
        """Delete a file from the machine.

        Args:
            request: The current HTTP request.
            machine_id: Primary key of the machine.
            name: Name of the file to delete.

        Returns:
            An empty response, or an error.
        """
        machine = self.get_object()
        try:
            services.delete_file(machine, name, current_user(request))
        except (services.CapabilityNotAvailable, AgentError) as e:
            return error_response(e)
        return Response(status=status.HTTP_204_NO_CONTENT)