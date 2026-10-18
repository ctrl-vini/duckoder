"""Tests for the registry that picks the language model provider."""

from dataclasses import replace

import pytest
from pydantic import SecretStr

from app.clients.anthropic_client import AnthropicClient
from app.clients.llm_client import LlmClient
from app.clients.llm_provider import LlmProviderRegistry
from app.clients.ollama_client import OllamaClient
from app.config import LlmProvider, Settings
from app.exceptions import InvalidSettingError
from tests.fakes import FakeLlmClient


def with_provider(settings: Settings, provider: LlmProvider) -> Settings:
    """Return the settings asking for one provider, with a key so Anthropic can be built."""
    return replace(
        settings,
        llm_provider=provider,
        anthropic=replace(settings.anthropic, api_key=SecretStr("test-key")),
    )


def test_creates_the_local_client_for_ollama(settings: Settings) -> None:
    client = LlmProviderRegistry().create(with_provider(settings, LlmProvider.OLLAMA))

    assert isinstance(client, OllamaClient)
    assert client.model == settings.ollama.model


def test_creates_the_api_client_for_anthropic(settings: Settings) -> None:
    client = LlmProviderRegistry().create(with_provider(settings, LlmProvider.ANTHROPIC))

    assert isinstance(client, AnthropicClient)
    assert client.model == settings.anthropic.model


def test_a_provider_without_a_builder_is_refused(settings: Settings) -> None:
    registry = LlmProviderRegistry(builders={})

    with pytest.raises(InvalidSettingError, match="APP_LLM_PROVIDER"):
        registry.create(with_provider(settings, LlmProvider.OLLAMA))


def test_a_registered_builder_replaces_the_built_in_one(settings: Settings) -> None:
    registry = LlmProviderRegistry()
    fake = FakeLlmClient()
    registry.register(LlmProvider.OLLAMA, lambda _: fake)

    client: LlmClient = registry.create(with_provider(settings, LlmProvider.OLLAMA))

    assert client is fake
