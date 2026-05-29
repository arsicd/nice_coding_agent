from pathlib import Path
from typing import List

from core.sandbox.base import (
    NodeMixin,
    PythonMixin,
    SubprocessSandbox,
)


class BaseMacOSSandbox(SubprocessSandbox):
    """
    Runs snippets under macOS ``sandbox-exec`` using a seatbelt profile.
    """

    def __init__(
        self,
        project_root: Path,
        profile_path: Path | None = None,
        **kwargs,
    ):
        super().__init__(project_root=project_root, **kwargs)
        self.profile_path = (
            Path(profile_path)
            if profile_path
            else Path(__file__).parent / "profiles" / "readonly.sb"
        ).resolve()
        if not self.profile_path.exists():
            raise ValueError(f"profile not found: {self.profile_path}")

    def _wrap_command(self, argv: List[str], scratch_dir: Path) -> List[str]:
        return [
            "sandbox-exec",
            "-f",
            str(self.profile_path),
            "-D",
            f"SCRATCH_DIR={scratch_dir}",
            *argv,
        ]


class PythonMacOSSandbox(PythonMixin, BaseMacOSSandbox):
    """Python under macOS sandbox-exec."""


class NodeMacOSSandbox(NodeMixin, BaseMacOSSandbox):
    """Node.js / TypeScript under macOS sandbox-exec."""
