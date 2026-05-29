from pathlib import Path

from core.sandbox.base import SandboxResult, Sandbox


class DockerSandbox(Sandbox):
    def __init__(self, project_root: Path, image: str):
        self.project_root = Path(project_root).resolve()
        self.image = image
        raise NotImplementedError("Docker backend not implemented yet")

    def run(self, code: str, timeout: float = 10.0) -> SandboxResult:
        raise NotImplementedError
