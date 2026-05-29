import shutil
import subprocess
from pathlib import Path
from typing import List

from core.sandbox.base import (
    NodeMixin,
    PythonMixin,
    SubprocessSandbox,
)


class BubblewrapSandbox(SubprocessSandbox):
    """
    Runs snippets under bubblewrap (``bwrap``), an unprivileged user-namespace
    sandbox. Maps onto the same guarantees as the macOS seatbelt profile:

      whole-FS read       ->  --ro-bind / /
      scratch writable    ->  --bind <scratch> <scratch>
      write-deny elsewhere->  implied (everything else is read-only)
      no network          ->  --unshare-net
      cwd = project_root  ->  --chdir <project_root>

    Requires the ``bwrap`` binary and unprivileged user namespaces, both checked
    at construction so failures surface early and clearly (mirroring how the
    macOS backend validates the profile path).
    """

    def __init__(
        self,
        project_root: Path,
        bwrap_path: str | Path | None = None,
        **kwargs,
    ):
        super().__init__(project_root=project_root, **kwargs)

        resolved = str(bwrap_path) if bwrap_path else shutil.which("bwrap")
        if not resolved:
            raise ValueError(
                "bubblewrap (bwrap) not found on PATH. Install it, e.g. "
                "`apt install bubblewrap` / `dnf install bubblewrap`."
            )
        self.bwrap_path = resolved
        self._check_userns()

    def _check_userns(self) -> None:
        """
        Verify unprivileged user namespaces work by running a trivial bwrap
        invocation. Some hardened/older kernels disable them.
        """
        try:
            proc = subprocess.run(
                [self.bwrap_path, "--ro-bind", "/", "/", "--unshare-net", "true"],
                capture_output=True,
                timeout=10,
                text=True,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            raise ValueError(f"bwrap sanity check failed to run: {e}") from e
        if proc.returncode != 0:
            raise ValueError(
                "bwrap is present but cannot create a sandbox (unprivileged user "
                "namespaces may be disabled). "
                "Check `sysctl kernel.unprivileged_userns_clone`. "
                f"stderr: {proc.stderr.strip()}"
            )

    def _wrap_command(self, argv: List[str], scratch_dir: Path) -> List[str]:
        return [
            self.bwrap_path,
            "--ro-bind",
            "/",
            "/",  # read-all
            "--dev",
            "/dev",  # minimal device nodes (incl. /dev/null)
            "--proc",
            "/proc",  # many runtimes need /proc
            "--tmpfs",
            "/tmp",  # writable, isolated /tmp
            "--bind",
            str(scratch_dir),
            str(scratch_dir),  # scratch is writable
            "--unshare-net",  # no network
            "--unshare-pid",  # isolate PIDs
            "--unshare-ipc",
            "--unshare-uts",
            "--die-with-parent",  # killed if agent dies (timeout safety)
            "--new-session",  # detach controlling terminal
            "--chdir",
            str(self.project_root),
            *argv,
        ]


class PythonLinuxSandbox(PythonMixin, BubblewrapSandbox):
    """Python under bubblewrap."""


class NodeLinuxSandbox(NodeMixin, BubblewrapSandbox):
    """Node.js / TypeScript under bubblewrap."""
