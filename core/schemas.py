"""Pydantic schemas describing the contract between the portal and machine agents."""

from pydantic import BaseModel, Field


class FilesCapability(BaseModel):
    """Configuration of the "files" capability (list, upload, delete files on the machine).

    Attributes:
        accept: Allowed file extensions, including the dot (e.g. [".pcn"]).
            An empty list means every extension is accepted.
        max_mb: Maximum size of an uploaded file, in megabytes.
    """

    accept: list[str] = Field(default_factory=list)
    max_mb: int = 50


class StatusCapability(BaseModel):
    """Configuration of the "status" capability (online check and basic health info).

    It currently has no options: its presence in the manifest only means
    the agent exposes a status endpoint.
    """


class Capabilities(BaseModel):
    """Capabilities exposed by a machine agent.

    Each attribute is either the configuration of a capability or None
    when the machine does not provide it.

    Attributes:
        files: Configuration of the "files" capability, if available.
        status: Configuration of the "status" capability, if available.
    """

    files: FilesCapability | None = None
    status: StatusCapability | None = None


class Manifest(BaseModel):
    """Self-description returned by a machine agent at GET /manifest.

    Attributes:
        name: Human-readable name of the machine as declared by the agent.
        capabilities: Capabilities the agent exposes and their configuration.
    """

    name: str = ""
    capabilities: Capabilities = Field(default_factory=Capabilities)


class Status(BaseModel):
    """Current state of a machine, as returned by GET /status.

    Attributes:
        online: Whether the agent answered.
        gadget_active: Whether the USB gadget is exposed to the machine.
        files_count: Number of files currently on the machine.
        detail: Reason why the machine is offline, if any.
    """

    online: bool = True
    gadget_active: bool = False
    files_count: int = 0
    detail: str = ""