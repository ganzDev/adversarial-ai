from typing import Any, Callable
from environment import tools
from environment.tool_schemas import(
    AVAILABLE_TOOLS,
    ToolRequest,
    ToolResult,
)

TOOL_DISPATCH: dict[str, Callable[..., Any]] = {
    "get_system_status": tools.get_system_status,
    "read_ticket": tools.read_ticket,
    "query_employee": tools.query_employee,
    "read_file": tools.read_file,
    "update_config": tools.update_config,
    "restart_service": tools.restart_service,
}

def dispatch_tool(request: ToolRequest) -> Any:
    """Dispatch the tool request to appropriate function."""
    tool_function = TOOL_DISPATCH.get(request.tool)
    if tool_function is None:
        raise ValueError(f"No dispatch function found for tool '{request.tool}'")

    return tool_function(**request.arguments)

def authorize_and_execute(request: ToolRequest) -> ToolResult:
    """Authorize and execute a validated tool request. Returns a ToolResult indicating success or failure."""

    if request.tool not in AVAILABLE_TOOLS:
        return ToolResult(
            allowed=False,
            reason=f"Tool '{request.tool}' is not available.",
            risk="high",
        )

    definition = AVAILABLE_TOOLS[request.tool]
    if request.resource != definition["resource"]:
        return ToolResult(
            allowed=False,
            reason=(
                f"Resource mismatch for '{request.tool}': "
                f"expected '{definition['resource']}', "
                f"received '{request.resource}'."
            ),
            risk="high",
        )

    if request.operation != definition["operation"]:
        return ToolResult(
            allowed=False,
            reason=(
                f"Operation mismatch for '{request.tool}': "
                f"expected '{definition['operation']}', "
                f"received '{request.operation}'."
            ),
            risk="high",
        )

    argument_error = validate_arguments(request)
    if argument_error is not None:
        return ToolResult(
            allowed=False,
            reason=argument_error,
            risk="high",
        )

    if request.tool in {"update_config", "restart_service"}:
        return ToolResult(
            allowed=False,
            reason="Human-approval is required for this operation.",
            risk="high",
        )

    try:
        result = dispatch_tool(request)
    except (ValueError, TypeError) as exc:
        return ToolResult(
            allowed=False,
            reason=str(exc),
            risk="high",
        )

    return ToolResult(
        allowed=True,
        result=result,
        reason="Tool request approved.",
        risk="low",
    )

    ## fail-closed
    # return ToolResult(
    #     allowed=False,
    #     reason="Gateway authorization is not implemented yet",
    #     risk="high",
    # )

def validate_arguments(request: ToolRequest) -> str | None:
    """Validate arguments per specific tool requested."""
    arguments = request.arguments

    if request.tool == "get_system_status":
        if arguments:
            return "get_system_status does not accept any arguments."

    elif request.tool == "read_ticket":
        if set(arguments) != {"ticket_id"}:
            return "read_ticket accepts only 'ticket_id' argument."

        ticket_id = arguments["ticket_id"]
        if isinstance(ticket_id, bool) or not isinstance(ticket_id, int):
            return "ticket_id must be an integer."

        if ticket_id < 0:
            return "ticket_id must be a non-negative int."

    elif request.tool == "query_employee":
        if set(arguments) != {"record_id"}:
            return "query_employee accepts only 'record_id' argument."

        record_id = arguments["record_id"]
        if isinstance(record_id, bool) or not isinstance(record_id, int):
            return "record_id must be an integer."

        if record_id < 0:
            return "record_id must be a non-negative int."

    elif request.tool == "read_file":
        if set(arguments) != {"path"}:
            return "read_file accepts only 'path' argument."

        path = arguments["path"]
        if not isinstance(path, str):
            return "path must be a string."

    elif request.tool == "update_config":
        if set(arguments) != {"key", "value"}:
            return "update_config accepts only 'key: string' and 'value: any' arguments."

        key = arguments["key"]
        if not isinstance(key, str):
            return "key must be a string."

    elif request.tool == "restart_service":
        if set(arguments) != {"service"}:
            return "restart_service accepts only 'service' argument."

        service = arguments["service"]
        if not isinstance(service, str):
            return "service must be a string."

    return None  # No argument errors found