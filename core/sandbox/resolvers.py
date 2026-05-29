import subprocess
from pathlib import Path


def find_project_python(project_root: Path) -> Path | None:
    root = Path(project_root)

    for candidate in (
        root / ".venv" / "bin" / "python",
        root / "venv" / "bin" / "python",
    ):
        if candidate.exists():
            return candidate.absolute()

    try:
        out = subprocess.run(
            ["uv", "python", "find"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            p = Path(out.stdout.strip())
            if p.exists():
                return p.absolute()
    except (OSError, subprocess.TimeoutExpired):
        pass

    return None
