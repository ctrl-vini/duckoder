"""Tests for loading settings from the environment."""

import pytest

from app.config import LlmProvider, load_settings
from app.exceptions import InvalidSettingError

LLM_VARIABLES = (
    "APP_HOST",
    "APP_PORT",
    "APP_LLM_PROVIDER",
    "APP_OLLAMA_URL",
    "APP_OLLAMA_MODEL",
    "APP_ANTHROPIC_API_KEY",
    "APP_ANTHROPIC_MODEL",
    "APP_MAX_REQUESTS_PER_HOUR",
)


def clear_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in LLM_VARIABLES:
        monkeypatch.delenv(name, raising=False)


def test_defaults_are_used_when_variables_are_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_variables(monkeypatch)

    settings = load_settings()

    assert settings.port == 8000
    assert settings.ollama.url == "http://localhost:11434"
    assert settings.llm_provider is LlmProvider.ANTHROPIC


def test_environment_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("APP_OLLAMA_MODEL", "other-model")

    settings = load_settings()

    assert settings.port == 9000
    assert settings.ollama.model == "other-model"


def test_the_provider_is_read_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_variables(monkeypatch)
    monkeypatch.setenv("APP_LLM_PROVIDER", " Ollama ")

    settings = load_settings()

    assert settings.llm_provider is LlmProvider.OLLAMA


def test_an_unknown_provider_is_refused_with_the_valid_ones(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_LLM_PROVIDER", "openai")

    with pytest.raises(InvalidSettingError, match="ollama, anthropic"):
        load_settings()


def test_the_api_key_is_not_written_when_the_settings_are_printed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The settings reach the logs and the tracebacks; the key must not travel with them.
    monkeypatch.setenv("APP_ANTHROPIC_API_KEY", "sk-ant-secret-value")

    settings = load_settings()

    assert "sk-ant-secret-value" not in repr(settings)
    assert settings.anthropic.api_key.get_secret_value() == "sk-ant-secret-value"
