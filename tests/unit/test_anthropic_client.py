"""Tests for the Claude API language model client."""

from collections.abc import Callable
from typing import Any

import anthropic
import httpx2
import pytest
from anthropic.types import Message, TextBlock, Usage
from pydantic import SecretStr

from app.clients.anthropic_client import AnthropicClient, AnthropicOptions
from app.clients.llm_client import ChatMessage
from app.config import AnthropicSettings
from app.exceptions import InvalidSettingError, LlmUnavailableError

OPTIONS = AnthropicOptions(max_tokens=1024, timeout_s=30.0)
MODEL = "claude-test-model"
API_URL = "https://api.anthropic.com/v1/messages"


class StubMessages:
    """Stands in for client.messages: records the request and returns a canned reply or error."""

    def __init__(self, reply: Message | None = None, error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.requests: list[dict[str, Any]] = []

    def create(self, **request: Any) -> Message:
        self.requests.append(request)
        if self.error:
            raise self.error
        assert self.reply is not None
        return self.reply


class StubAnthropicApi:
    """Stands in for anthropic.Anthropic, of which only the messages resource is used."""

    def __init__(self, reply: Message | None = None, error: Exception | None = None) -> None:
        self.messages = StubMessages(reply, error)


def make_reply(*texts: str, output_tokens: int = 42) -> Message:
    return Message(
        id="msg_01",
        type="message",
        role="assistant",
        model=MODEL,
        content=[TextBlock(type="text", text=text) for text in texts],
        usage=Usage(input_tokens=120, output_tokens=output_tokens),
    )


def make_settings(api_key: str = "test-key") -> AnthropicSettings:
    return AnthropicSettings(
        api_key=SecretStr(api_key), model=MODEL, max_tokens=1024, timeout_s=30.0
    )


def status_error(status_code: int, message: str) -> anthropic.APIStatusError:
    response = httpx2.Response(status_code, request=httpx2.Request("POST", API_URL))
    return anthropic.APIStatusError(message, response=response, body=None)


def fake_clock(*readings: float) -> Callable[[], float]:
    return iter(readings).__next__


def test_chat_returns_reply_and_metrics() -> None:
    api = StubAnthropicApi(reply=make_reply("void setup() {}"))
    client = AnthropicClient(api, MODEL, OPTIONS, clock=fake_clock(10.0, 12.5))

    result = client.chat([ChatMessage(role="user", content="Blink the LED")])

    assert result.content == "void setup() {}"
    assert result.model == MODEL
    assert result.elapsed_ms == 2500
    assert result.output_tokens == 42
    # The API keeps no model of ours in memory, so there is no loading time to report.
    assert result.load_ms == 0


def test_the_reply_joins_every_text_block() -> None:
    api = StubAnthropicApi(reply=make_reply("void setup() {}", "\nvoid loop() {}"))
    client = AnthropicClient(api, MODEL, OPTIONS)

    result = client.chat([ChatMessage(role="user", content="Blink the LED")])

    assert result.content == "void setup() {}\nvoid loop() {}"


def test_the_instructions_are_sent_apart_from_the_conversation() -> None:
    api = StubAnthropicApi(reply=make_reply())
    client = AnthropicClient(api, MODEL, OPTIONS)

    client.chat(
        [
            ChatMessage(role="system", content="You write ESP32 code."),
            ChatMessage(role="user", content="Blink the LED"),
            ChatMessage(role="assistant", content="void setup() {}"),
            ChatMessage(role="user", content="Now every two seconds"),
        ]
    )

    request = api.messages.requests[0]
    assert request["system"] == "You write ESP32 code."
    assert request["messages"] == [
        {"role": "user", "content": "Blink the LED"},
        {"role": "assistant", "content": "void setup() {}"},
        {"role": "user", "content": "Now every two seconds"},
    ]


def test_chat_sends_the_model_and_the_token_ceiling() -> None:
    api = StubAnthropicApi(reply=make_reply())
    client = AnthropicClient(api, MODEL, OPTIONS)

    client.chat([ChatMessage(role="user", content="Blink the LED")])

    request = api.messages.requests[0]
    assert request["model"] == MODEL
    assert request["max_tokens"] == 1024
    assert request["timeout"] == 30.0


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        pytest.param(
            status_error(429, "rate limited"),
            "The Claude API answered with status 429.",
            id="rate-limited",
        ),
        pytest.param(
            status_error(401, "invalid key"),
            "The Claude API answered with status 401.",
            id="key-refused",
        ),
        pytest.param(
            anthropic.APIConnectionError(request=httpx2.Request("POST", API_URL)),
            "The Claude API could not be reached.",
            id="unreachable",
        ),
    ],
)
def test_api_failures_become_llm_unavailable(error: Exception, expected: str) -> None:
    client = AnthropicClient(StubAnthropicApi(error=error), MODEL, OPTIONS)

    with pytest.raises(LlmUnavailableError, match=expected):
        client.chat([ChatMessage(role="user", content="Blink the LED")])


def test_the_failure_does_not_repeat_what_the_api_sent_back() -> None:
    # An error body can quote the request, and the request holds the whole prompt, so only the
    # kind of failure may reach the browser.
    error = status_error(400, "invalid request: messages.0.content: Blink the LED")
    client = AnthropicClient(StubAnthropicApi(error=error), MODEL, OPTIONS)

    with pytest.raises(LlmUnavailableError) as raised:
        client.chat([ChatMessage(role="user", content="Blink the LED")])

    assert "Blink the LED" not in str(raised.value)


def test_from_settings_builds_a_client_for_the_configured_model() -> None:
    client = AnthropicClient.from_settings(make_settings())

    assert client.model == MODEL


def test_from_settings_without_a_key_fails_before_the_server_starts() -> None:
    with pytest.raises(InvalidSettingError, match="APP_ANTHROPIC_API_KEY"):
        AnthropicClient.from_settings(make_settings(api_key=""))
