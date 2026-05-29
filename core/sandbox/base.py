import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def format_for_llm(self) -> str:
        """Compact representation for tool output."""
        parts = []
        if self.timed_out:
            parts.append("[TIMEOUT after execution]")
        parts.append(f"exit_code: {self.exit_code}")
        if self.stdout:
            parts.append(f"stdout:\n{self.stdout}")
        if self.stderr:
            parts.append(f"stderr:\n{self.stderr}")
        return "\n".join(parts)


class Sandbox(ABC):
    @abstractmethod
    def run(self, code: str, timeout: float = 10.0) -> SandboxResult: ...


class SubprocessSandbox(Sandbox):
    """
    Generic, OS-independent orchestration for running a code snippet under an
    external sandbox wrapper via a subprocess.
    """

    def __init__(
        self,
        project_root: Path,
        max_output_bytes: int = 10_000,
    ):
        self.project_root = Path(project_root).resolve()
        self.max_output_bytes = max_output_bytes

        if not self.project_root.exists():
            raise ValueError(f"project_root does not exist: {self.project_root}")

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """The file extension for the generated snippet (e.g., '.py', '.ts')."""
        ...

    @abstractmethod
    def _get_executable_args(self) -> List[str]:
        """Base command to run the snippet (e.g., ['node'], ['/usr/bin/python3'])."""
        ...

    def _get_env(self, scratch_dir: Path) -> Dict[str, str]:
        """Base environment variables. Mixins call super() and update."""
        return {
            "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin",
            "HOME": str(scratch_dir),
            "TMPDIR": str(scratch_dir),
            "LC_ALL": "en_US.UTF-8",
        }

    @abstractmethod
    def _wrap_command(self, argv: List[str], scratch_dir: Path) -> List[str]:
        """
        Wrap the interpreter argv with the OS-specific sandbox launcher.

        ``argv`` is the full command (interpreter + snippet path). Implementations
        return the argv to actually exec, e.g. prefixed with the sandbox tool and
        whatever flags grant read-all / scratch-write / no-network.
        """
        ...

    def run(self, code: str, timeout: float = 10.0) -> SandboxResult:
        with tempfile.TemporaryDirectory(prefix="sbx_") as scratch:
            scratch_dir = Path(scratch).resolve()

            snippet_path = scratch_dir / f"snippet{self.file_extension}"
            snippet_path.write_text(code)

            env = self._get_env(scratch_dir)

            argv = [*self._get_executable_args(), str(snippet_path)]
            cmd = self._wrap_command(argv, scratch_dir)

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(self.project_root),
                    env=env,
                    capture_output=True,
                    timeout=timeout,
                    text=True,
                )
                return SandboxResult(
                    stdout=self._truncate(proc.stdout),
                    stderr=self._truncate(proc.stderr),
                    exit_code=proc.returncode,
                    timed_out=False,
                )
            except subprocess.TimeoutExpired as e:
                stdout = (
                    e.stdout.decode()
                    if isinstance(e.stdout, bytes)
                    else (e.stdout or "")
                )
                stderr = (
                    e.stderr.decode()
                    if isinstance(e.stderr, bytes)
                    else (e.stderr or "")
                )
                return SandboxResult(
                    stdout=self._truncate(stdout),
                    stderr=self._truncate(stderr),
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


class PythonMixin:
    """
    Supplies Python interpreter behavior. Combine with an OS subclass of
    SubprocessSandbox. Must appear *before* the OS class in the MRO so its
    cooperative __init__ runs and forwards **kwargs via super().
    """

    file_extension = ".py"

    def __init__(
        self,
        project_root: Path,
        python_executable: Path | None = None,
        **kwargs,
    ):
        super().__init__(project_root=project_root, **kwargs)
        exe = Path(python_executable) if python_executable else Path(sys.executable)
        self.python_executable = exe.absolute()
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


class NodeMixin:
    """
    Supplies Node.js / TypeScript interpreter behavior. Combine with an OS
    subclass of SubprocessSandbox.
    """

    def __init__(
        self,
        project_root: Path,
        executable: str | Path = "node",
        is_typescript: bool = True,
        **kwargs,
    ):
        super().__init__(project_root=project_root, **kwargs)
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
