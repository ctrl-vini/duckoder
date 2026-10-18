"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import SecretStr

from app.exceptions import InvalidSettingError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
DEFAULT_BOARDS_DIR = PROJECT_ROOT / "data" / "boards"
DEFAULT_CONVERSATIONS_DIR = PROJECT_ROOT / "data" / "conversations"
DEFAULT_BOARD_ID = "esp32"
LLM_PROVIDER_VARIABLE = "APP_LLM_PROVIDER"


class LlmProvider(StrEnum):
    """The language model services the platform can generate code with."""

    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"


@dataclass(frozen=True)
class OllamaSettings:
    """Where the Ollama server is and how it should generate."""

    url: str
    model: str
    temperature: float
    context_size: int
    keep_alive: str


@dataclass(frozen=True)
class AnthropicSettings:
    """Credentials and limits of the Claude API.

    The key is a SecretStr, so printing the settings, logging them or showing them in a traceback
    writes `SecretStr('**********')` instead of the key. Only `get_secret_value()` reveals it, and
    the only call to it is the one that builds the API client.
    """

    api_key: SecretStr
    model: str
    max_tokens: int
    timeout_s: float


@dataclass(frozen=True)
class Settings:
    """Immutable runtime configuration.

    Every provider has its own section, so each client is built with its provider's settings and
    never receives another provider's credentials.
    """

    host: str
    port: int
    llm_provider: LlmProvider
    ollama: OllamaSettings
    anthropic: AnthropicSettings
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
        # The Claude API is the default; APP_LLM_PROVIDER=ollama answers with a local model.
        llm_provider=_load_llm_provider(),
        ollama=OllamaSettings(
            url=os.getenv("APP_OLLAMA_URL", "http://localhost:11434"),
            model=os.getenv("APP_OLLAMA_MODEL", "qwen2.5-coder:7b"),
            temperature=float(os.getenv("APP_LLM_TEMPERATURE", "0.7")),
            context_size=int(os.getenv("APP_LLM_CONTEXT_SIZE", "8192")),
            keep_alive=os.getenv("APP_LLM_KEEP_ALIVE", "30m"),
        ),
        anthropic=AnthropicSettings(
            api_key=SecretStr(os.getenv("APP_ANTHROPIC_API_KEY", "")),
            model=os.getenv("APP_ANTHROPIC_MODEL", "claude-sonnet-5-5"),
            max_tokens=int(os.getenv("APP_ANTHROPIC_MAX_TOKENS", "4096")),
            timeout_s=float(os.getenv("APP_ANTHROPIC_TIMEOUT_S", "120")),
        ),
        max_requests_per_hour=int(os.getenv("APP_MAX_REQUESTS_PER_HOUR", "60")),
        boards_dir=Path(os.getenv("APP_BOARDS_DIR", str(DEFAULT_BOARDS_DIR))),
        default_board_id=os.getenv("APP_DEFAULT_BOARD", DEFAULT_BOARD_ID),
        conversations_dir=Path(os.getenv("APP_CONVERSATIONS_DIR", str(DEFAULT_CONVERSATIONS_DIR))),
        static_dir=STATIC_DIR,
    )


def _load_llm_provider() -> LlmProvider:
    """Read which provider answers the conversations, naming the valid ones when it is wrong."""
    name = os.getenv(LLM_PROVIDER_VARIABLE, LlmProvider.ANTHROPIC.value).strip().lower()
    try:
        return LlmProvider(name)
    except ValueError:
        choices = ", ".join(provider.value for provider in LlmProvider)
        raise InvalidSettingError(LLM_PROVIDER_VARIABLE, f"expected one of {choices}") from None
