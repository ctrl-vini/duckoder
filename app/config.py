"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
DEFAULT_BOARDS_DIR = PROJECT_ROOT / "data" / "boards"
DEFAULT_CONVERSATIONS_DIR = PROJECT_ROOT / "data" / "conversations"
DEFAULT_BOARD_ID = "esp32"


@dataclass(frozen=True)
class Settings:
    """Immutable runtime configuration."""

    host: str
    port: int
    ollama_url: str
    ollama_model: str
    llm_temperature: float
    llm_context_size: int
    llm_keep_alive: str
    max_requests_per_hour: int
    boards_dir: Path
    default_board_id: str
    conversations_dir: Path
    static_dir: Path


def load_settings() -> Settings:
    """Build the settings from APP_* environment variables, falling back to defaults."""
    return Settings(
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
        ollama_url=os.getenv("APP_OLLAMA_URL", "http://localhost:11434"),
        ollama_model=os.getenv("APP_OLLAMA_MODEL", "qwen2.5-coder:7b"),
        llm_temperature=float(os.getenv("APP_LLM_TEMPERATURE", "0.7")),
        llm_context_size=int(os.getenv("APP_LLM_CONTEXT_SIZE", "8192")),
        llm_keep_alive=os.getenv("APP_LLM_KEEP_ALIVE", "30m"),
        max_requests_per_hour=int(os.getenv("APP_MAX_REQUESTS_PER_HOUR", "60")),
        boards_dir=Path(os.getenv("APP_BOARDS_DIR", str(DEFAULT_BOARDS_DIR))),
        default_board_id=os.getenv("APP_DEFAULT_BOARD", DEFAULT_BOARD_ID),
        conversations_dir=Path(os.getenv("APP_CONVERSATIONS_DIR", str(DEFAULT_CONVERSATIONS_DIR))),
        static_dir=STATIC_DIR,
    )
