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
        assert completed.json()["quality_score"] >= 20

        exported = client.get(f"/api/v1/prompts/{draft['id']}/export?format=markdown", headers=headers)
        assert exported.status_code == 200
        assert "# Prompt dla ChatGPT" in exported.text


def test_draft_can_be_resumed_edited_and_deleted_after_reload() -> None:
    email = f"resume-{uuid4()}@example.com"
    password = "bardzo-bezpieczne-haslo-123"
    with TestClient(app) as first_session:
        assert first_session.post("/api/v1/auth/register", json={"email": email, "password": password, "first_name": "Jan", "last_name": "Testowy"}).status_code == 201
        login = first_session.post("/api/v1/auth/login", json={"email": email, "password": password})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        draft = first_session.post("/api/v1/prompts", json={"brief": "Chcę przygotować plan wdrożenia aplikacji dla zespołu operacyjnego", "model_target": "chatgpt", "level": "professional", "category": "business"}, headers=headers).json()
        prompt_id = draft["id"]
        assert draft["status"] == "needs_clarification"

    with TestClient(app) as reloaded_session:
        login = reloaded_session.post("/api/v1/auth/login", json={"email": email, "password": password})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        restored = reloaded_session.get(f"/api/v1/prompts/{prompt_id}", headers=headers)
        assert restored.status_code == 200
        assert restored.json()["status"] == "needs_clarification"
        answers = {question: "Dla zespołu operacyjnego, w tabeli etapów z terminami, budżetem i kryteriami akceptacji." for question in restored.json()["questions"]}
        generated = reloaded_session.post(f"/api/v1/prompts/{prompt_id}/answers", json={"answers": answers}, headers=headers)
        assert generated.status_code == 200
        assert generated.json()["status"] == "generated"
        edited_content = f"{generated.json()['content']}\n\n## Dopisek\nZatwierdzone przez zespół."
        assert reloaded_session.patch(f"/api/v1/prompts/{prompt_id}", json={"content": edited_content}, headers=headers).status_code == 200

    with TestClient(app) as final_session:
        login = final_session.post("/api/v1/auth/login", json={"email": email, "password": password})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert "Zatwierdzone przez zespół" in final_session.get(f"/api/v1/prompts/{prompt_id}", headers=headers).json()["content"]
        assert final_session.delete(f"/api/v1/prompts/{prompt_id}", headers=headers).status_code == 204
        assert final_session.get(f"/api/v1/prompts/{prompt_id}", headers=headers).status_code == 404
        assert final_session.get("/api/v1/prompts", headers=headers).json()["total"] == 0


def test_placeholder_answers_are_rejected_before_prompt_generation() -> None:
    email = f"placeholder-{uuid4()}@example.com"
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/register", json={"email": email, "password": "bardzo-bezpieczne-haslo-123", "first_name": "Jan", "last_name": "Testowy"}).status_code == 201
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "bardzo-bezpieczne-haslo-123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        draft = client.post("/api/v1/prompts", json={"brief": "Chcę zbudować osobistego agenta biurowego.", "model_target": "chatgpt", "level": "professional", "category": "programming"}, headers=headers).json()

        response = client.post(f"/api/v1/prompts/{draft['id']}/answers", json={"answers": {question: "ma działać" for question in draft["questions"]}}, headers=headers)
        assert response.status_code == 422
        assert "zbyt ogólna" in response.json()["detail"]
        assert client.get(f"/api/v1/prompts/{draft['id']}", headers=headers).json()["status"] == "needs_clarification"


def test_office_agent_flow_generates_domain_specific_prompt() -> None:
    email = f"office-agent-{uuid4()}@example.com"
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/register", json={"email": email, "password": "bardzo-bezpieczne-haslo-123", "first_name": "Jan", "last_name": "Testowy"}).status_code == 201
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "bardzo-bezpieczne-haslo-123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        draft = client.post("/api/v1/prompts", json={"brief": "Chcę zbudować osobistego agenta biurowego do organizacji codziennej pracy.", "model_target": "chatgpt", "level": "professional", "category": "programming"}, headers=headers).json()
        assert draft["status"] == "needs_clarification"
        assert len(draft["questions"]) == 5
        answers = {
            question: answer for question, answer in zip(draft["questions"], [
                "Gmail, Google Calendar, Google Drive i lista zadań; dostęp wyłącznie do kontaktów służbowych, kalendarza i dokumentów projektowych.",
                "Każdego ranka podsumowuje spotkania i priorytety, a w piątek przygotowuje tygodniowe podsumowanie zadań.",
                "Tworzy szkice odpowiedzi automatycznie, ale wysłanie e-maila, spotkania lub zmianę dokumentu wykonuje wyłącznie po zatwierdzeniu.",
                "Przechowuje preferencje i nazwy projektów przez 30 dni; nie zapisuje haseł ani danych zdrowotnych.",
                "Przy braku danych prosi o doprecyzowanie, przy błędzie pokazuje powiadomienie i nie wykonuje akcji; sukces to brak pominiętych spotkań i 80% zadań w terminie.",
            ])
        }
        response = client.post(f"/api/v1/prompts/{draft['id']}/answers", json={"answers": answers}, headers=headers)
        assert response.status_code == 200
        generated = response.json()
        assert generated["status"] == "generated"
        assert generated["quality_score"] >= 80
        assert "Codzienne przepływy pracy" in generated["content"]
        assert "Mierzalne testy akceptacyjne" in generated["content"]
