"""Dependency providers that hand routes the service instances built at startup."""

from typing import Annotated

from fastapi import Depends, Request

from app.services.board_registry import BoardRegistry
from app.services.conversation_service import ConversationService
from app.services.rate_limiter import RequestRateLimiter


def get_board_registry(request: Request) -> BoardRegistry:
    """Return the board registry created with the application."""
    return request.app.state.board_registry


def get_conversation_service(request: Request) -> ConversationService:
    """Return the conversation service created with the application."""
    return request.app.state.conversation_service


def get_rate_limiter(request: Request) -> RequestRateLimiter:
    """Return the rate limiter created with the application."""
    return request.app.state.rate_limiter


def enforce_rate_limit(
    limiter: Annotated[RequestRateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Count this request against the hour's limit, refusing it once the limit is reached."""
    limiter.record_request()


BoardRegistryDep = Annotated[BoardRegistry, Depends(get_board_registry)]
ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]
# Declared by the routes that ask the model for a reply, the only ones that cost anything.
RateLimited = Depends(enforce_rate_limit)
