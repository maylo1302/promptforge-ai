# PromptForge AI

PromptForge AI to polska platforma SaaS do projektowania promptów dla ChatGPT i Claude. Zamiast natychmiast tworzyć wynik, aplikacja wykrywa luki w opisie, zadaje pytania doprecyzowujące, a następnie buduje ustrukturyzowany prompt wraz z oceną jakości i analizą.

## Architektura

```text
frontend (React + Vite)  ── HTTPS/JWT ──>  backend (FastAPI)
       │                                      │
       └─ React Query / formularze             ├─ SQLAlchemy ──> PostgreSQL (Neon)
                                              └─ adaptery AI ──> OpenAI / Anthropic
```

- **Frontend** — React, TypeScript, Tailwind, React Router, React Query, React Hook Form, Zod i Framer Motion.
- **Backend** — FastAPI z Pydantic, SQLAlchemy, Alembic, JWT access/refresh, bcrypt oraz warstwą dostawców AI.
- **Dane** — PostgreSQL w środowisku produkcyjnym; SQLite jest wyłącznie wygodnym ustawieniem lokalnym.
- **Bezpieczeństwo** — krótkotrwały access token, rotowany refresh token w ciasteczku HttpOnly, CSRF dla operacji ciasteczkowych, ograniczanie żądań, CORS z listą dozwolonych źródeł, nagłówki bezpieczeństwa i ORM parametryzujący zapytania.

## Struktura

```text
backend/                 API FastAPI, migracje i testy Pytest
frontend/                aplikacja React oraz testy Vitest
docker-compose.yml       środowisko lokalne z PostgreSQL
.env.example             komplet wymaganych zmiennych środowiskowych
```

## Uruchomienie lokalne

1. Skopiuj `.env.example` do `.env` i ustaw długi `JWT_SECRET_KEY`. Klucze dostawców AI są opcjonalne: bez nich generator działa w trybie deterministycznym, przydatnym do lokalnych testów.
2. Z Dockerem uruchom `docker compose up --build`.
3. Bez Dockera:

   ```bash
   cd backend && python -m venv .venv && .venv/bin/pip install -e ".[dev]"
   alembic upgrade head
   uvicorn app.main:app --reload

   cd ../frontend && pnpm install && pnpm dev
   ```

Interfejs będzie dostępny na `http://localhost:5173`, a dokumentacja API na `http://localhost:8000/docs`.

## Wdrożenie

- **Vercel:** ustaw katalog główny projektu na `frontend`, zbuduj poleceniem `pnpm build` i ustaw `VITE_API_URL` na adres Rendera zakończony `/api/v1`.
- **Render:** utwórz usługę Web z katalogu `backend`; ustaw zmienne z `.env.example`, przede wszystkim `DATABASE_URL` Neona, `JWT_SECRET_KEY`, `FRONTEND_ORIGINS`, a opcjonalnie klucze dostawców AI.
- **Neon:** użyj łańcucha połączenia PostgreSQL z `sslmode=require`, następnie uruchom `alembic upgrade head` w kroku wdrożenia.
- **E-mail odzyskiwania hasła:** ustaw `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM` i publiczny `FRONTEND_URL`. Bez SMTP aplikacja nie ujawnia tokenu resetu i jedynie bezpiecznie informuje użytkownika o przyjęciu żądania.

Nigdy nie zapisuj pliku `.env`, tokenów ani kluczy API w repozytorium.
