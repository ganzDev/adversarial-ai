
from environment.tool_schemas import ToolRequest, ToolResult


def authorize_and_execute(request: ToolRequest) -> ToolResult:
    """Temporary gateway stub that denies all requests."""
    return ToolResult(
        allowed=False,
        reason="Gateway authorization is not implemented yet",
        risk="high",
    )
