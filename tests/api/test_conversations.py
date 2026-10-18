"""Tests for the conversation routes."""

from dataclasses import replace

from fastapi.testclient import TestClient

from app.config import Settings
from app.exceptions import LlmUnavailableError
from app.main import create_app
from tests.fakes import FakeLlmClient


def start_conversation(client: TestClient) -> str:
    response = client.post("/conversations", json={"board_id": "test-board"})
    return response.json()["id"]


def test_create_conversation_returns_201_with_an_empty_history(client: TestClient) -> None:
    response = client.post("/conversations", json={"board_id": "test-board"})

    assert response.status_code == 201
    body = response.json()
    assert body["board_id"] == "test-board"
    assert body["messages"] == []


def test_create_conversation_for_unknown_board_returns_404(client: TestClient) -> None:
    response = client.post("/conversations", json={"board_id": "missing-board"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Board not found: missing-board"}


def test_send_message_returns_the_reply(client: TestClient) -> None:
    conversation_id = start_conversation(client)

    response = client.post(
        f"/conversations/{conversation_id}/messages", json={"content": "Pisque o LED"}
    )

    assert response.status_code == 201
    reply = response.json()
    assert reply["role"] == "assistant"
    assert reply["code"] == "void setup() {}\nvoid loop() {}"
    assert reply["explanation"] == "O código não faz nada."
    assert reply["metrics"]["elapsed_ms"] == 1200


def test_get_conversation_returns_every_message(client: TestClient) -> None:
    conversation_id = start_conversation(client)
    client.post(f"/conversations/{conversation_id}/messages", json={"content": "Pisque o LED"})

    response = client.get(f"/conversations/{conversation_id}")

    assert response.status_code == 200
    assert [message["role"] for message in response.json()["messages"]] == ["user", "assistant"]


def test_unknown_conversation_returns_404(client: TestClient) -> None:
    response = client.get(f"/conversations/{'0' * 32}")

    assert response.status_code == 404


def test_blank_message_returns_422(client: TestClient) -> None:
    conversation_id = start_conversation(client)

    response = client.post(f"/conversations/{conversation_id}/messages", json={"content": "   "})

    assert response.status_code == 422


def test_model_failure_returns_502(client: TestClient, llm_client: FakeLlmClient) -> None:
    conversation_id = start_conversation(client)
    llm_client.error = LlmUnavailableError("Failed to connect to Ollama")

    response = client.post(
        f"/conversations/{conversation_id}/messages", json={"content": "Pisque o LED"}
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Failed to connect to Ollama"}


def test_pin_usage_returns_the_components_to_wire(
    client: TestClient, llm_client: FakeLlmClient
) -> None:
    conversation_id = start_conversation(client)
    llm_client.reply = "```cpp\nvoid setup() { pinMode(2, OUTPUT); pinMode(13, OUTPUT); }\n```"
    reply = client.post(
        f"/conversations/{conversation_id}/messages", json={"content": "Pisque o LED"}
    ).json()

    response = client.get(f"/conversations/{conversation_id}/messages/{reply['id']}/pin-usage")

    assert response.status_code == 200
    body = response.json()
    assert [component["name"] for component in body["components"]] == ["LED"]
    assert body["unlisted_gpios"] == [13]


def test_pin_usage_of_unknown_message_returns_404(client: TestClient) -> None:
    conversation_id = start_conversation(client)

    response = client.get(f"/conversations/{conversation_id}/messages/{'0' * 32}/pin-usage")

    assert response.status_code == 404
    assert response.json() == {"detail": f"Message not found: {'0' * 32}"}


def test_more_messages_than_the_hour_allows_returns_429(
    settings: Settings, llm_client: FakeLlmClient
) -> None:
    capped = TestClient(create_app(replace(settings, max_requests_per_hour=1), llm_client))
    conversation_id = start_conversation(capped)
    url = f"/conversations/{conversation_id}/messages"

    first = capped.post(url, json={"content": "Pisque o LED"})
    second = capped.post(url, json={"content": "Agora a cada dois segundos"})

    assert first.status_code == 201
    assert second.status_code == 429
    assert "Try again" in second.json()["detail"]
