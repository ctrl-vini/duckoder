"""Application factory: the single place where the services are built and wired together."""

from fastapi import FastAPI

from app.clients.llm_client import LlmClient
from app.clients.llm_provider import LlmProviderRegistry
from app.config import Settings
from app.errors import register_error_handlers
from app.frontend import FrontendFiles
from app.repositories.conversation_repository import ConversationRepository
from app.routers import boards, conversations, version
from app.services.board_registry import BoardRegistry
from app.services.conversation_service import ConversationService
from app.services.prompt_builder import PromptBuilder
from app.services.rate_limiter import RequestRateLimiter

APP_TITLE = "Duckoder"
APP_VERSION = "1.3.1"


def create_app(settings: Settings, llm_client: LlmClient | None = None) -> FastAPI:
    """Create the application; pass llm_client to replace the configured provider, as tests do."""
    app = FastAPI(title=APP_TITLE, version=APP_VERSION)

    board_registry = BoardRegistry.from_directory(settings.boards_dir, settings.default_board_id)
    app.state.board_registry = board_registry
    app.state.rate_limiter = RequestRateLimiter(settings.max_requests_per_hour)
    app.state.conversation_service = ConversationService(
        boards=board_registry,
        conversations=ConversationRepository(settings.conversations_dir),
        prompt_builder=PromptBuilder.from_file(),
        llm_client=llm_client or LlmProviderRegistry().create(settings),
    )

    register_error_handlers(app)
    app.include_router(boards.router)
    app.include_router(conversations.router)
    app.include_router(version.router)

    # Mounted at "/", the frontend would capture every API route, so it must be registered last.
    app.mount("/", FrontendFiles(directory=settings.static_dir, html=True), name="frontend")
    return app
