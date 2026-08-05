from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app


def test_user_can_complete_prompt_flow_and_export_markdown() -> None:
    email = f"test-{uuid4()}@example.com"
    with TestClient(app) as client:
        registration = client.post("/api/v1/auth/register", json={"email": email, "password": "bardzo-bezpieczne-haslo-123", "first_name": "Jan", "last_name": "Testowy"})
        assert registration.status_code == 201

        login = client.post("/api/v1/auth/login", json={"email": email, "password": "bardzo-bezpieczne-haslo-123"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        created = client.post("/api/v1/prompts", json={"brief": "Chcę napisać książkę", "model_target": "chatgpt", "level": "professional", "category": "other"}, headers=headers)
        assert created.status_code == 201
        draft = created.json()
        assert draft["status"] == "needs_clarification"

        answers = {question: "Praktyczna odpowiedź dla początkujących w formie listy." for question in draft["questions"]}
        completed = client.post(f"/api/v1/prompts/{draft['id']}/answers", json={"answers": answers}, headers=headers)
        assert completed.status_code == 200
        assert completed.json()["quality_score"] >= 70

        exported = client.get(f"/api/v1/prompts/{draft['id']}/export?format=markdown", headers=headers)
        assert exported.status_code == 200
        assert "# Prompt dla ChatGPT" in exported.text
