class AgentError(Exception):
    pass


class MCPConnectionError(AgentError):
    pass


class MCPToolError(AgentError):
    pass

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class AgentInvocationError(AgentError):
    pass
