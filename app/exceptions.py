"""Domain exceptions raised by the services."""

from pathlib import Path


class BoardNotFoundError(Exception):
    """Raised when no hardware profile exists for the requested board id."""

    def __init__(self, board_id: str) -> None:
        super().__init__(f"Board not found: {board_id}")
        self.board_id = board_id


class InvalidBoardProfileError(Exception):
    """Raised when a hardware profile file cannot be read, parsed or validated."""

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"Invalid board profile {path.name}: {reason}")
        self.path = path


class LlmUnavailableError(Exception):
    """Raised when the language model cannot produce a reply (service down, model missing...)."""


class RateLimitExceededError(Exception):
    """Raised when the server has already generated as many replies this hour as it is allowed."""

    def __init__(self, retry_after_s: int) -> None:
        super().__init__(f"Too many requests. Try again in {retry_after_s} s.")
        self.retry_after_s = retry_after_s


class ConversationNotFoundError(Exception):
    """Raised when no conversation exists for the requested id."""

    def __init__(self, conversation_id: str) -> None:
        super().__init__(f"Conversation not found: {conversation_id}")
        self.conversation_id = conversation_id


class MessageNotFoundError(Exception):
    """Raised when a conversation has no message with the requested id."""

    def __init__(self, message_id: str) -> None:
        super().__init__(f"Message not found: {message_id}")
        self.message_id = message_id
