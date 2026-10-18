"""Routes for conversations and their messages."""

from fastapi import APIRouter, status

from app.dependencies import ConversationServiceDep, RateLimited
from app.schemas.conversation import Conversation, ConversationCreate, Message, MessageCreate
from app.schemas.pin_usage import PinUsage

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_conversation(body: ConversationCreate, service: ConversationServiceDep) -> Conversation:
    """Start a conversation about one board."""
    return service.start(body.board_id)


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, service: ConversationServiceDep) -> Conversation:
    """Return a conversation with all its messages."""
    return service.get(conversation_id)


@router.post(
    "/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    dependencies=[RateLimited],
)
def send_message(
    conversation_id: str, body: MessageCreate, service: ConversationServiceDep
) -> Message:
    """Send what the student asks for and return the model's reply."""
    return service.send_message(conversation_id, body.content)


@router.get("/{conversation_id}/messages/{message_id}/pin-usage")
def get_pin_usage(
    conversation_id: str, message_id: str, service: ConversationServiceDep
) -> PinUsage:
    """Return the board components a message's code uses, so the student knows what to wire."""
    return service.get_pin_usage(conversation_id, message_id)
