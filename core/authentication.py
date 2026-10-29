"""Authentication classes of the API."""

from rest_framework import authentication


class SessionAuthentication(authentication.SessionAuthentication):
    """Session authentication that answers 401 instead of 403 to anonymous calls.

    DRF returns 403 for the stock SessionAuthentication because it declares no
    ``WWW-Authenticate`` header. Declaring one makes anonymous requests fail
    with 401, so the JavaScript client can tell "not logged in" (session
    expired, redirect to the login page) from "forbidden" (e.g. CSRF failure).
    """

    def authenticate_header(self, request) -> str:
        """Return the value of the ``WWW-Authenticate`` header for 401 responses."""
        return "Session"
