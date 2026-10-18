"""The contract every language model provider implements, and the data it exchanges.

Only this module is imported by the services: they ask a provider for a reply without knowing
whether it comes from a model running on this machine or from an API on the internet.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    """One message of a conversation sent to the model."""

    role: Role
    content: str


@dataclass(frozen=True)
class LlmResult:
    """The model's reply and how long it took to produce it.

    `load_ms` is the time the provider spent loading the model before generating; a provider that
    does not report it, such as an API that keeps no model of ours in memory, reports zero.
    """

    content: str
    model: str
    elapsed_ms: int
    load_ms: int
    output_tokens: int


class LlmClient(Protocol):
    """Anything that can answer a conversation: a local model, an API or a test double."""

    @property
    def model(self) -> str:
        """Name of the model the client sends the conversations to."""
        ...

    def chat(self, messages: list[ChatMessage]) -> LlmResult:
        """Send the conversation and return the model's reply."""
        ...
