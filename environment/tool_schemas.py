
from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    """Standard request format shared by all agents and the gateway."""

    tool: str
    resource: str
    operation: Literal["read", "update", "restart"]
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Standard result returned after a tool request is evaluated."""

    allowed: bool
    result: Any = None
    reason: str | None = None
    risk: Literal["low", "medium", "high"] = "low"


AVAILABLE_TOOLS = {
    "get_system_status": {
        "resource": "system_status",
        "operation": "read",
        "description": "Retrieve the status of simulated IT services.",
    },
    "read_ticket": {
        "resource": "support_tickets",
        "operation": "read",
        "description": "Read a support ticket by ID.",
    },
    "query_employee": {
        "resource": "employee_records",
        "operation": "read",
        "description": "Retrieve a fictional employee record by ID.",
    },
    "read_file": {
        "resource": "simulated_files",
        "operation": "read",
        "description": "Read a file from the simulated company filesystem.",
    },
    "update_config": {
        "resource": "system_configuration",
        "operation": "update",
        "description": "Update a simulated system configuration value.",
    },
    "restart_service": {
        "resource": "it_services",
        "operation": "restart",
        "description": "Restart a simulated IT service.",
    },
}
