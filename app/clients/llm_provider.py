"""Chooses which language model provider answers the conversations."""

import logging
from collections.abc import Callable

from app.clients.anthropic_client import AnthropicClient
from app.clients.llm_client import LlmClient
from app.clients.ollama_client import OllamaClient
from app.config import LLM_PROVIDER_VARIABLE, LlmProvider, Settings
from app.exceptions import InvalidSettingError

logger = logging.getLogger(__name__)

LlmClientBuilder = Callable[[Settings], LlmClient]

# Each builder is handed only its own provider's settings, so a provider cannot read another
# one's credentials.
BUILTIN_PROVIDERS: dict[LlmProvider, LlmClientBuilder] = {
    LlmProvider.OLLAMA: lambda settings: OllamaClient.from_settings(settings.ollama),
    LlmProvider.ANTHROPIC: lambda settings: AnthropicClient.from_settings(settings.anthropic),
}


class LlmProviderRegistry:
    """Holds one client builder per provider and creates the one the settings ask for.

    This is the only place that knows the platform has more than one provider. Supporting a new
    one means writing its client and adding a line to BUILTIN_PROVIDERS; the services, the routes
    and the settings of the other providers stay as they are.
    """

    def __init__(self, builders: dict[LlmProvider, LlmClientBuilder] | None = None) -> None:
        self._builders = dict(BUILTIN_PROVIDERS if builders is None else builders)

    def register(self, provider: LlmProvider, builder: LlmClientBuilder) -> None:
        """Add the builder of one provider, or replace the one already registered."""
        self._builders[provider] = builder

    def create(self, settings: Settings) -> LlmClient:
        """Build the client of the configured provider, failing when it has no builder."""
        builder = self._builders.get(settings.llm_provider)
        if builder is None:
            raise InvalidSettingError(
                LLM_PROVIDER_VARIABLE, f"no client is registered for {settings.llm_provider.value}"
            )

        client = builder(settings)
        logger.info("Language model: %s (%s)", settings.llm_provider.value, client.model)
        return client
