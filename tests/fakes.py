"""Test doubles shared by the test modules."""

from app.clients.llm_client import ChatMessage, LlmResult

FAKE_REPLY = "```cpp\nvoid setup() {}\nvoid loop() {}\n```\nO código não faz nada."
FAKE_MODEL = "fake-model"


class FakeLlmClient:
    """LlmClient that returns a canned reply and records every conversation it receives."""

    model = FAKE_MODEL

    def __init__(self, reply: str = FAKE_REPLY) -> None:
        self.reply = reply
        self.error: Exception | None = None
        self.received: list[list[ChatMessage]] = []

    def chat(self, messages: list[ChatMessage]) -> LlmResult:
        self.received.append(messages)
        if self.error:
            raise self.error
        return LlmResult(
            content=self.reply, model=FAKE_MODEL, elapsed_ms=1200, load_ms=0, output_tokens=30
        )
