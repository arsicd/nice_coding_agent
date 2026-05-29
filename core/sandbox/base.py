from abc import ABC, abstractmethod
from dataclasses import dataclass


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
            parts.append(f"[TIMEOUT after execution]")
        parts.append(f"exit_code: {self.exit_code}")
        if self.stdout:
            parts.append(f"stdout:\n{self.stdout}")
        if self.stderr:
            parts.append(f"stderr:\n{self.stderr}")
        return "\n".join(parts)


class Sandbox(ABC):
    @abstractmethod
    def run(self, code: str, timeout: float = 10.0) -> SandboxResult: ...
