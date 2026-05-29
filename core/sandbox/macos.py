import subprocess
import sys
import tempfile
from abc import abstractmethod
from pathlib import Path
from typing import Dict, List

from core.sandbox.base import Sandbox, SandboxResult


class BaseMacOSSandbox(Sandbox):
    """
    Base class for running code under macOS sandbox-exec.
    Handles scratch directories, subprocess execution, timeouts, and output truncation.
    """

    def __init__(
        self,
        project_root: Path,
        profile_path: Path | None = None,
        max_output_bytes: int = 10_000,
    ):
        self.project_root = Path(project_root).resolve()
        self.profile_path = (
            Path(profile_path)
            if profile_path
            else Path(__file__).parent / "profiles" / "readonly.sb"
        ).resolve()
        self.max_output_bytes = max_output_bytes

        if not self.project_root.exists():
            raise ValueError(f"project_root does not exist: {self.project_root}")
        if not self.profile_path.exists():
            raise ValueError(f"profile not found: {self.profile_path}")

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """The file extension for the generated snippet (e.g., '.py', '.ts')."""
        pass

    @abstractmethod
    def _get_executable_args(self) -> List[str]:
        """Returns the base command to run the snippet (e.g., ['node'], ['/usr/bin/python3'])."""
        pass

    def _get_env(self, scratch_dir: Path) -> Dict[str, str]:
        """Returns the base environment variables. Subclasses should call super() and update."""
        return {
            "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin",
            "HOME": str(scratch_dir),
            "TMPDIR": str(scratch_dir),
            "LC_ALL": "en_US.UTF-8",
        }

    def run(self, code: str, timeout: float = 10.0) -> SandboxResult:
        with tempfile.TemporaryDirectory(prefix="sbx_") as scratch:
            scratch_dir = Path(scratch).resolve()

            # Write snippet to a file in scratch
            snippet_path = scratch_dir / f"snippet{self.file_extension}"
            snippet_path.write_text(code)

            env = self._get_env(scratch_dir)

            cmd = [
                "sandbox-exec",
                "-f",
                str(self.profile_path),
                "-D",
                f"SCRATCH_DIR={scratch_dir}",
                *self._get_executable_args(),
                str(snippet_path),
            ]

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(self.project_root),
                    env=env,
                    capture_output=True,
                    timeout=timeout,
                    text=True,
                )
                stdout = self._truncate(proc.stdout)
                stderr = self._truncate(proc.stderr)
                return SandboxResult(
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=proc.returncode,
                    timed_out=False,
                )
            except subprocess.TimeoutExpired as e:
                stdout = self._truncate(e.stdout.decode() if e.stdout else "")
                stderr = self._truncate(e.stderr.decode() if e.stderr else "")
                return SandboxResult(
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=-1,
                    timed_out=True,
                )

    def _truncate(self, text: str) -> str:
        if not text:
            return ""
        data = text.encode("utf-8", errors="replace")
        if len(data) <= self.max_output_bytes:
            return text
        truncated = data[: self.max_output_bytes].decode("utf-8", errors="replace")
        return (
            truncated
            + f"\n... [truncated, {len(data) - self.max_output_bytes} more bytes]"
        )


class PythonMacOSSandbox(BaseMacOSSandbox):
    """Python implementation of the macOS sandbox."""

    file_extension = ".py"

    def __init__(
        self, project_root: Path, python_executable: Path | None = None, **kwargs
    ):
        super().__init__(project_root, **kwargs)
        self.python_executable = Path(python_executable or sys.executable).resolve()

        if not self.python_executable.exists():
            raise ValueError(f"python not found: {self.python_executable}")

    def _get_executable_args(self) -> List[str]:
        return [str(self.python_executable)]

    def _get_env(self, scratch_dir: Path) -> Dict[str, str]:
        env = super()._get_env(scratch_dir)
        env.update(
            {
                "PYTHONPATH": str(self.project_root),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUNBUFFERED": "1",
            }
        )
        return env


class NodeMacOSSandbox(BaseMacOSSandbox):
    """Node.js / TypeScript implementation of the macOS sandbox."""

    def __init__(
        self,
        project_root: Path,
        executable: str | Path = "node",
        is_typescript: bool = True,
        **kwargs,
    ):
        super().__init__(project_root, **kwargs)
        self.executable = str(executable)
        self._is_ts = is_typescript

    @property
    def file_extension(self) -> str:
        return ".ts" if self._is_ts else ".js"

    def _get_executable_args(self) -> List[str]:
        return [self.executable]

    def _get_env(self, scratch_dir: Path) -> Dict[str, str]:
        env = super()._get_env(scratch_dir)
        env.update(
            {
                "NODE_PATH": str(self.project_root / "node_modules"),
                "NODE_NO_WARNINGS": "1",
            }
        )
        return env
