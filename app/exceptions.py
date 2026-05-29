class AppError(Exception):
    pass


class MCPError(AppError):
    pass


class FileReadError(MCPError):
    pass

    def __init__(self, path: str, cause: Exception | None = None):
        self.path = path
        super().__init__(
            f"Could not read `{path}`: {cause}" if cause else f"Could not read `{path}`"
        )


class DirectoryTreeError(MCPError):
    pass


class AgentError(AppError):
    pass


class EmptyContextError(AgentError):
    pass

    def __init__(self):
        super().__init__(
            "Context is empty — add at least one entry before asking the LLM."
        )
