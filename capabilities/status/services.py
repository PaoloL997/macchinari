"""Operations of the "status" capability, performed through the machine agent."""

from core.client import AgentClient, AgentError
from core.models import Machine
from core.schemas import Status


class CapabilityNotAvailable(Exception):
    """The machine does not expose the "status" capability."""


def get_status(machine: Machine) -> Status:
    """Ask the agent for the current state of the machine.

    An unreachable agent is not an error here: it means the machine is offline.

    Args:
        machine: Machine to query.

    Returns:
        The machine status; online is False if the agent did not answer.

    Raises:
        CapabilityNotAvailable: If the machine does not expose "status".
    """
    if machine.parsed_manifest.capabilities.status is None:
        raise CapabilityNotAvailable(f"{machine.name} does not support status")
    try:
        return AgentClient(machine).get("/status", Status)
    except AgentError as e:
        return Status(online=False, detail=str(e))