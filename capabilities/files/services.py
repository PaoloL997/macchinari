"""Operations of the "files" capability, performed through the machine agent."""

from urllib.parse import quote

import httpx

from core.client import AgentClient, AgentError
from core.models import Machine, Operation
from core.schemas import FilesCapability

UPLOAD_TIMEOUT = httpx.Timeout(60.0, connect=2.0)


class CapabilityNotAvailable(Exception):
    """The machine does not expose the "files" capability."""


class FileRejected(Exception):
    """The file does not satisfy the machine rules (extension or size)."""


def get_config(machine: Machine) -> FilesCapability:
    """Return the "files" configuration of a machine.

    Args:
        machine: Machine to read the configuration from.

    Returns:
        The "files" capability configuration from the machine manifest.

    Raises:
        CapabilityNotAvailable: If the machine does not expose "files".
    """
    config = machine.parsed_manifest.capabilities.files
    if config is None:
        raise CapabilityNotAvailable(f"{machine.name} does not support files")
    return config


def validate_file(name: str, size: int, config: FilesCapability) -> None:
    """Check a file against the machine rules.

    Args:
        name: File name.
        size: File size in bytes.
        config: "files" configuration of the machine.

    Raises:
        FileRejected: If the extension is not accepted or the file is too large.
    """
    accepted = [ext.lower() for ext in config.accept]
    if accepted and not name.lower().endswith(tuple(accepted)):
        raise FileRejected(f"Extension not allowed. Accepted: {', '.join(config.accept)}")
    if size > config.max_mb * 1024 * 1024:
        raise FileRejected(f"File too large. Maximum: {config.max_mb} MB")


def log_operation(machine: Machine, user, action: str, filename: str, success: bool, detail: str = "") -> None:
    """Save an audit record of an operation.

    Args:
        machine: Machine the action was performed on.
        user: User who performed the action, or None if anonymous.
        action: "upload" or "delete".
        filename: Name of the file involved.
        success: Whether the agent completed the action.
        detail: Error message, if any.
    """
    Operation.objects.create(
        machine=machine,
        user=user,
        action=action,
        filename=filename,
        success=success,
        detail=detail,
    )


def list_files(machine: Machine) -> list[str]:
    """List the files currently on the machine.

    Args:
        machine: Machine to query.

    Returns:
        Names of the files on the machine.

    Raises:
        CapabilityNotAvailable: If the machine does not expose "files".
        AgentError: If the agent cannot be reached or answers with an error.
    """
    get_config(machine)
    return AgentClient(machine).get("/files", list[str])


def upload_file(machine: Machine, name: str, content: bytes, user=None) -> None:
    """Validate a file and upload it to the machine.

    Args:
        machine: Target machine.
        name: File name.
        content: File content.
        user: User performing the upload, or None if anonymous.

    Raises:
        CapabilityNotAvailable: If the machine does not expose "files".
        FileRejected: If the file does not satisfy the machine rules.
        AgentError: If the agent cannot complete the upload.
    """
    config = get_config(machine)
    validate_file(name, len(content), config)
    try:
        AgentClient(machine).request(
            "POST",
            "/files",
            files={"file": (name, content)},
            timeout=UPLOAD_TIMEOUT,
        )
    except AgentError as e:
        log_operation(machine, user, "upload", name, False, str(e))
        raise
    log_operation(machine, user, "upload", name, True)


def delete_file(machine: Machine, name: str, user=None) -> None:
    """Delete a file from the machine.

    Args:
        machine: Target machine.
        name: Name of the file to delete.
        user: User performing the deletion, or None if anonymous.

    Raises:
        CapabilityNotAvailable: If the machine does not expose "files".
        AgentError: If the agent cannot complete the deletion.
    """
    get_config(machine)
    try:
        AgentClient(machine).request("DELETE", f"/files/{quote(name)}", timeout=UPLOAD_TIMEOUT)
    except AgentError as e:
        log_operation(machine, user, "delete", name, False, str(e))
        raise
    log_operation(machine, user, "delete", name, True)