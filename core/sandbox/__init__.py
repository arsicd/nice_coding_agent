import platform
from pathlib import Path

from core.sandbox.base import Sandbox, SandboxResult
from core.sandbox.resolvers import find_project_python
from core.sandbox.macos import PythonMacOSSandbox, NodeMacOSSandbox
from core.sandbox.linux import PythonLinuxSandbox, NodeLinuxSandbox


def make_sandbox(project_root: Path, language: str, **kwargs) -> Sandbox:
    """Factory that picks a backend based on the host OS and language."""
    system = platform.system()

    if system == "Darwin":
        if language == "python":
            kwargs.setdefault("python_executable", find_project_python(project_root))
            return PythonMacOSSandbox(project_root=project_root, **kwargs)
        elif language in ("node", "javascript"):
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

    elif system == "Linux":
        if language == "python":
            kwargs.setdefault("python_executable", find_project_python(project_root))
            return PythonLinuxSandbox(project_root=project_root, **kwargs)
        elif language in ("node", "javascript"):
            return NodeLinuxSandbox(
                project_root=project_root,
                executable="node",
                is_typescript=False,
                **kwargs,
            )
        elif language == "typescript":
            return NodeLinuxSandbox(
                project_root=project_root,
                executable="tsx",
                is_typescript=True,
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported language on Linux: {language}")

    else:
        raise NotImplementedError(f"No sandbox backend for {system} yet")


__all__ = [
    "Sandbox",
    "SandboxResult",
    "PythonMacOSSandbox",
    "NodeMacOSSandbox",
    "PythonLinuxSandbox",
    "NodeLinuxSandbox",
    "make_sandbox",
]
