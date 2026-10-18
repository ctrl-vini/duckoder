"""Language model access through Ollama: the only module that talks to a local model."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

import ollama

from app.clients.llm_client import ChatMessage, LlmResult
from app.config import OllamaSettings
from app.exceptions import LlmUnavailableError

NANOSECONDS_PER_MILLISECOND = 1_000_000
MILLISECONDS_PER_SECOND = 1_000


@dataclass(frozen=True)
class OllamaOptions:
    """Sampling and memory settings applied to every request to Ollama."""

    temperature: float
    context_size: int
    keep_alive: str


class OllamaClient:
    """LlmClient backed by an Ollama server."""

    def __init__(
        self,
        client: ollama.Client,
        model: str,
        options: OllamaOptions,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._client = client
        self._model = model
        self._options = options
        self._clock = clock

    @classmethod
    def from_settings(cls, settings: OllamaSettings) -> Self:
        """Build a client for the server, model and options in the Ollama settings."""
        options = OllamaOptions(
            temperature=settings.temperature,
            context_size=settings.context_size,
            keep_alive=settings.keep_alive,
        )
        return cls(ollama.Client(host=settings.url), settings.model, options)

    @property
    def model(self) -> str:
        """Name of the model the requests are sent to."""
        return self._model

    def chat(self, messages: list[ChatMessage]) -> LlmResult:
        """Send the conversation and return the reply with its timing."""
        started_at = self._clock()
        try:
            response = self._client.chat(
                model=self._model,
                messages=_to_ollama_messages(messages),
                options={
                    "temperature": self._options.temperature,
                    "num_ctx": self._options.context_size,
                },
                keep_alive=self._options.keep_alive,
            )
        except (ConnectionError, ollama.ResponseError) as error:
            raise LlmUnavailableError(str(error)) from error
        elapsed_ms = round((self._clock() - started_at) * MILLISECONDS_PER_SECOND)

        return LlmResult(
            content=response.message.content or "",
            model=response.model or self._model,
            elapsed_ms=elapsed_ms,
            load_ms=(response.load_duration or 0) // NANOSECONDS_PER_MILLISECOND,
            output_tokens=response.eval_count or 0,
        )


def _to_ollama_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    return [{"role": message.role, "content": message.content} for message in messages]
