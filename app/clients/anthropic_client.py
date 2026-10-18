"""Language model access through the Claude API: the only module that talks to Anthropic."""

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Self

import anthropic

from app.clients.llm_client import ChatMessage, LlmResult
from app.config import AnthropicSettings
from app.exceptions import InvalidSettingError, LlmUnavailableError

API_KEY_VARIABLE = "APP_ANTHROPIC_API_KEY"
MILLISECONDS_PER_SECOND = 1_000
# The API runs the model on Anthropic's machines, so there is no model of ours to load first.
NO_LOAD_TIME_MS = 0
# Every retry is time the student spends waiting, so a failed request is retried once at most.
MAX_RETRIES = 1
SYSTEM_ROLE = "system"
SYSTEM_PROMPT_SEPARATOR = "\n\n"
TEXT_BLOCK = "text"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnthropicOptions:
    """Limits applied to every request.

    The API takes no temperature; what bounds a reply there is a ceiling of output tokens, which
    is also what bounds the cost of one request.
    """

    max_tokens: int
    timeout_s: float


class AnthropicClient:
    """LlmClient backed by the Claude API."""

    def __init__(
        self,
        client: anthropic.Anthropic,
        model: str,
        options: AnthropicOptions,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._client = client
        self._model = model
        self._options = options
        self._clock = clock

    @classmethod
    def from_settings(cls, settings: AnthropicSettings) -> Self:
        """Build a client for the key and model in the settings; without a key it does not start.

        Failing here stops the server at startup, instead of letting every student's first
        message come back as an error from a platform that could never have answered.
        """
        key = settings.api_key.get_secret_value()
        if not key:
            raise InvalidSettingError(API_KEY_VARIABLE, "the Claude API needs a key")

        options = AnthropicOptions(max_tokens=settings.max_tokens, timeout_s=settings.timeout_s)
        api = anthropic.Anthropic(api_key=key, max_retries=MAX_RETRIES)
        return cls(api, settings.model, options)

    @property
    def model(self) -> str:
        """Name of the model the requests are sent to."""
        return self._model

    def chat(self, messages: list[ChatMessage]) -> LlmResult:
        """Send the conversation and return the reply with its timing."""
        instructions, conversation = _split_system_prompt(messages)
        started_at = self._clock()
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._options.max_tokens,
                system=instructions or anthropic.NOT_GIVEN,
                messages=conversation,
                timeout=self._options.timeout_s,
            )
        except anthropic.AnthropicError as error:
            # The whole error is written here, where only the server sees it, and the caller is
            # given the short reason that is safe to show the student.
            logger.warning("The Claude API did not answer: %s", error)
            raise LlmUnavailableError(_safe_reason(error)) from error
        elapsed_ms = round((self._clock() - started_at) * MILLISECONDS_PER_SECOND)

        return LlmResult(
            content=_text_of(response),
            model=response.model or self._model,
            elapsed_ms=elapsed_ms,
            load_ms=NO_LOAD_TIME_MS,
            output_tokens=response.usage.output_tokens,
        )


def _split_system_prompt(messages: Sequence[ChatMessage]) -> tuple[str, list[dict[str, Any]]]:
    """Separate the instructions, which the API takes in their own field, from the conversation."""
    instructions = SYSTEM_PROMPT_SEPARATOR.join(
        message.content for message in messages if message.role == SYSTEM_ROLE
    )
    conversation = [
        {"role": message.role, "content": message.content}
        for message in messages
        if message.role != SYSTEM_ROLE
    ]
    return instructions, conversation


def _text_of(response: anthropic.types.Message) -> str:
    """Join the text the model wrote, leaving out any block that is not text."""
    return "".join(block.text for block in response.content if block.type == TEXT_BLOCK)


def _safe_reason(error: anthropic.AnthropicError) -> str:
    """Describe the failure without repeating what the API sent back.

    This reason reaches the browser as the error detail, so it carries the kind of failure and
    nothing else: an error body can quote the request, and the request holds the whole prompt.
    """
    if isinstance(error, anthropic.APIStatusError):
        return f"The Claude API answered with status {error.status_code}."
    return "The Claude API could not be reached."
