import os
from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Literal
import shutil

from pydantic.error_wrappers import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from lib.logger import get_logger

logger = get_logger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class LlmModel:
    name: str
    price_input: float
    price_output: float


@dataclass
class LlmModels:
    data: list[LlmModel] = field(default_factory=list)

    def __post_init__(self):
        self.data = []


Provider = Literal["openrouter", "alibaba", "google", "nvidia", "kimi", "mimo"]


class Settings(BaseSettings):
    project_root: Path | None = None
    exa_api_key: str = ""
    openrouter_http_referer: str = "http://localhost:8080"
    openrouter_app_title: str = "Coding Agent"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    alibaba_base_url: str = ""
    alibaba_api_key: str = ""
    google_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_api_key: str = ""
    kimi_base_url: str = "https://api.kimi.com/coding/v1"
    kimi_api_key: str = ""
    mimo_base_url: str = "https://api.xiaomimimo.com/v1"
    mimo_api_key: str = ""

    summarization_model_provider: Provider
    summarization_model: str
    summarization_concurrency: int
    strict_model_provider: Provider
    strict_model: str
    creative_model_provider: Provider
    creative_model: str
    strict_model_high_provider: Provider
    strict_model_high: str
    creative_model_high_provider: Provider
    creative_model_high: str

    agent_max_steps: int = 25
    postgres_uri: str
    db_schema: str

    use_rag: bool
    code_embedder: str
    doc_embedder: str
    reranker: str
    embedding_device: str  # "mps", "cpu, "cuda"
    chunk_size: int
    chunk_overlap: int

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def all_providers(self) -> list[Provider]:
        return list(
            {
                self.strict_model_provider,
                self.creative_model_provider,
                self.strict_model_high_provider,
                self.creative_model_high_provider,
                self.summarization_model_provider,
            }
        )

    def validation_errors(self) -> str | None:
        missing_configs = set()
        base_url_ignore = {"google"}
        messages = []

        for provider in self.all_providers():
            if not getattr(self, f"{provider}_api_key"):
                missing_configs.add(provider)
            if provider not in base_url_ignore:
                if not getattr(self, f"{provider}_base_url"):
                    missing_configs.add(provider)
        if missing_configs:
            messages.append("Providers not configured: " + ", ".join(missing_configs))

        if not settings.postgres_uri or not settings.db_schema:
            messages.append("Postgres parameters not configured")

        if messages:
            return "\n".join(messages)
        return None


def _ensure_file(target: Path, example: Path) -> bool:
    if target.is_file():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    if example.is_file():
        shutil.copy(example, target)
        logger.info(
            f"Created '{target.resolve()}' from {example.name}, adjust as needed."
        )
        return True
    else:
        raise ValueError(f"'{example.resolve()}' file not found.")


def get_env_file_path(project_path: Path) -> Path:
    nice_dir = project_path / ".nice"
    env_file_path = nice_dir / ".env"
    ignore_file_path = nice_dir / ".ignore"

    _ensure_file(ignore_file_path, PACKAGE_ROOT / "example.ignore")
    created = _ensure_file(env_file_path, PACKAGE_ROOT / "example.env")
    if created:
        content = env_file_path.read_text()
        content = content.replace("DB_SCHEMA=\n", f"DB_SCHEMA={project_path.name}\n")
        env_file_path.write_text(content)

    return env_file_path


def init_settings():
    global _settings
    if _settings is not None:
        return _settings

    env_project_path = os.environ.get("NICEDIR", str(Path.cwd()))

    project_path = Path(env_project_path).resolve()

    env_path = get_env_file_path(project_path)
    try:
        _settings = Settings(_env_file=env_path)
        _settings.project_root = project_path
        logger.info("Settings loaded")
    except ValidationError as exc:
        print("Configuration error in your .env file:\n")
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"])
            print(f"  • {loc}: {err['msg']}")
        print("\nFound .env file - adjust settings - use example.env for reference.")
        sys.exit(1)

    return _settings


def reload_settings() -> "Settings":
    """Force re-read of the .env file and rebuild the settings singleton."""
    global _settings
    _settings = None  # clear the cache
    return init_settings()


_settings: Settings = None


class _SettingsProxy:
    def __getattr__(self, name):
        if _settings is None:
            init_settings()
        return getattr(_settings, name)


settings = _SettingsProxy()
