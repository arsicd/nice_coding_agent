import platform
from pathlib import Path

from core.sandbox.base import Sandbox, SandboxResult
from core.sandbox.macos import PythonMacOSSandbox, NodeMacOSSandbox


def make_sandbox(project_root: Path, language: str, **kwargs) -> Sandbox:
    """Factory that picks a backend based on the host OS and language."""
    system = platform.system()

    if system == "Darwin":
        if language == "python":
            return PythonMacOSSandbox(project_root=project_root, **kwargs)
        elif language == "node" or language == "javascript":
            return NodeMacOSSandbox(
                project_root=project_root,
                executable="node",
                is_typescript=False,
                **kwargs,
            )
        elif language == "typescript":
            return NodeMacOSSandbox(
                project_root=project_root,
                executable="tsx",
                is_typescript=True,
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported language on macOS: {language}")

    # elif system == "Linux":
    #     # Route Linux sandboxes here later...
    else:
        raise NotImplementedError(f"No sandbox backend for {system} yet")


__all__ = [
    "Sandbox",
    "SandboxResult",
    "PythonMacOSSandbox",
    "NodeMacOSSandbox",
    "make_sandbox",
]
