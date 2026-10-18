"""Translates domain exceptions into HTTP responses, in one place."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions import (
    BoardNotFoundError,
    ConversationNotFoundError,
    LlmUnavailableError,
    MessageNotFoundError,
    RateLimitExceededError,
)

ExceptionHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]

STATUS_BY_EXCEPTION: dict[type[Exception], int] = {
    BoardNotFoundError: status.HTTP_404_NOT_FOUND,
    ConversationNotFoundError: status.HTTP_404_NOT_FOUND,
    MessageNotFoundError: status.HTTP_404_NOT_FOUND,
    LlmUnavailableError: status.HTTP_502_BAD_GATEWAY,
    RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
}


def register_error_handlers(app: FastAPI) -> None:
    """Answer each domain exception with its status code and the error message as detail."""
    for exception_type, status_code in STATUS_BY_EXCEPTION.items():
        app.add_exception_handler(exception_type, _respond_with(status_code))


def _respond_with(status_code: int) -> ExceptionHandler:
    async def handle(request: Request, error: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(error)})

    return handle
