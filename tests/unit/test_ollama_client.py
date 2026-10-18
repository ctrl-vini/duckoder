"""Tests for the Ollama-backed language model client."""

import re
from collections.abc import Callable
from typing import Any

import ollama
import pytest

from app.clients.llm_client import ChatMessage
from app.clients.ollama_client import OllamaClient, OllamaOptions
from app.exceptions import LlmUnavailableError

OPTIONS = OllamaOptions(temperature=0.5, context_size=4096, keep_alive="10m")


class StubOllamaApi:
    """Stands in for ollama.Client: records the request and returns a canned reply or error."""

    def __init__(
        self, reply: ollama.ChatResponse | None = None, error: Exception | None = None
    ) -> None:
        self.reply = reply
        self.error = error
        self.requests: list[dict[str, Any]] = []

    def chat(self, **request: Any) -> ollama.ChatResponse:
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.reply


def make_reply(content: str = "void setup() {}") -> ollama.ChatResponse:
    return ollama.ChatResponse(
        model="test-model",
        message=ollama.Message(role="assistant", content=content),
        load_duration=1_500_000_000,
        eval_count=42,
    )


def fake_clock(*readings: float) -> Callable[[], float]:
    return iter(readings).__next__


def test_chat_returns_reply_and_metrics() -> None:
    api = StubOllamaApi(reply=make_reply())
    client = OllamaClient(api, "test-model", OPTIONS, clock=fake_clock(10.0, 12.5))

    result = client.chat([ChatMessage(role="user", content="Blink the LED")])

    assert result.content == "void setup() {}"
    assert result.model == "test-model"
    assert result.elapsed_ms == 2500
    assert result.load_ms == 1500
    assert result.output_tokens == 42


def test_chat_sends_messages_model_and_options() -> None:
    api = StubOllamaApi(reply=make_reply())
    client = OllamaClient(api, "test-model", OPTIONS)
    messages = [
        ChatMessage(role="system", content="You write ESP32 code."),
        ChatMessage(role="user", content="Blink the LED"),
    ]

    client.chat(messages)

    request = api.requests[0]
    assert request["model"] == "test-model"
    assert request["messages"] == [
        {"role": "system", "content": "You write ESP32 code."},
        {"role": "user", "content": "Blink the LED"},
    ]
    assert request["options"] == {"temperature": 0.5, "num_ctx": 4096}
    assert request["keep_alive"] == "10m"


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(ConnectionError("Failed to connect to Ollama"), id="service-down"),
        pytest.param(ollama.ResponseError("model 'missing' not found", 404), id="model-missing"),
    ],
)
def test_ollama_failures_become_llm_unavailable(error: Exception) -> None:
    client = OllamaClient(StubOllamaApi(error=error), "test-model", OPTIONS)

    with pytest.raises(LlmUnavailableError, match=re.escape(str(error))):
        client.chat([ChatMessage(role="user", content="Blink the LED")])
