
from environment.tool_schemas import ToolRequest, ToolResult


def authorize_and_execute(request: ToolRequest) -> ToolResult:
    """
    Temporary integration stub.

    Person 2 must replace this with real authorization checks
    before any protected tool can execute.
    """
    return ToolResult(
        allowed=False,
        reason="Gateway authorization is not implemented yet",
        risk="high",
    )
