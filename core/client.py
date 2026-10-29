"""HTTP client used by the portal to talk to machine agents."""

from typing import Any

import httpx
from pydantic import TypeAdapter, ValidationError


class AgentError(Exception):
    """The agent is unreachable, returned an error or an unexpected response."""


class AgentClient:
    """Client for the HTTP API exposed by the agent of a single machine.

    Attributes:
        machine: Machine whose agent this client talks to.
        base_url: Agent base URL without trailing slash.
        headers: Headers sent with every request, including the auth token.
    """

    TIMEOUT = httpx.Timeout(5.0, connect=2.0)

    def __init__(self, machine):
        """Build a client for the given machine.

        Args:
            machine: Machine instance providing agent_url and agent_token.
        """
        self.machine = machine
        self.base_url = machine.agent_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {machine.agent_token}"}

    def request(self, method: str, path: str, timeout=None, **kwargs) -> httpx.Response:
        """Send a request to the agent and translate failures into AgentError.

        Args:
            method: HTTP method (e.g. "GET", "POST", "DELETE").
            path: Path relative to the agent base URL (e.g. "/files").
            timeout: Optional httpx timeout overriding the default one.
            **kwargs: Extra arguments passed to httpx.request (e.g. files, json).

        Returns:
            The successful HTTP response.

        Raises:
            AgentError: If the agent times out, is unreachable or answers
                with a 4xx/5xx status code.
        """
        url = f"{self.base_url}{path}"
        try:
            response = httpx.request(
                method,
                url,
                headers=self.headers,
                timeout=timeout or self.TIMEOUT,
                **kwargs,
            )
            response.raise_for_status()
        except httpx.TimeoutException as e:
            raise AgentError(f"{self.machine.name}: timeout") from e
        except httpx.HTTPStatusError as e:
            raise AgentError(
                f"{self.machine.name}: HTTP {e.response.status_code} - {e.response.text[:200]}"
            ) from e
        except httpx.RequestError as e:
            raise AgentError(
                f"{self.machine.name}: unreachable ({e.__class__.__name__})"
            ) from e
        return response

    def get(self, path: str, schema: Any) -> Any:
        """Send a GET request and validate the JSON response against a schema.

        Args:
            path: Path relative to the agent base URL.
            schema: Expected type of the response (e.g. Manifest, list[FileInfo]).

        Returns:
            The response body parsed and validated as the given schema.

        Raises:
            AgentError: If the request fails or the response does not match
                the schema.
        """
        response = self.request("GET", path)
        try:
            return TypeAdapter(schema).validate_json(response.content)
        except ValidationError as e:
            raise AgentError(
                f"{self.machine.name}: unexpected response from {path} ({e.error_count()} errors)"
            ) from e