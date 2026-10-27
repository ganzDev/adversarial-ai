
from typing import Any

from environment.tool_schemas import (
    AVAILABLE_TOOLS,
    ToolRequest,
    ToolResult,
)
from security.gateway import authorize_and_execute


class VictimAgent:
    """A basic agent that routes all tool requests through the gateway."""

    def run_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> ToolResult:
        # Reject unknown tools before constructing a request.
        if tool_name not in AVAILABLE_TOOLS:
            return ToolResult(
                allowed=False,
                reason=f"Unknown tool: {tool_name}",
                risk="high",
            )

        # Build the standard request shared with the gateway.
        definition = AVAILABLE_TOOLS[tool_name]

        request = ToolRequest(
            tool=tool_name,
            resource=definition["resource"],
            operation=definition["operation"],
            arguments=arguments or {},
        )

        # The gateway is the only execution entry point.
        return authorize_and_execute(request)


if __name__ == "__main__":
    agent = VictimAgent()

    result = agent.run_tool(
        "query_employee",
        {"record_id": 101},
    )

    print("Victim AI tool request:")
    print(result.model_dump())
