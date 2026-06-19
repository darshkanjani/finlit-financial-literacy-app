# FinLit - Financial Literacy Web App

FinLit is a full-stack financial literacy and planning web app built for a final-year Cardiff University Emerging Technologies group project. It helps users build a financial profile, understand spending, set savings goals, run stress-test scenarios, and receive AI-assisted financial guidance grounded in a small financial knowledge base.

This repository is a cleaned public portfolio version. Secrets, local databases, generated build files and large generated ML artifacts have been removed.

## Project context

* University project: final-year Emerging Technologies group project at Cardiff University
* Team size: 7 students
* My role: backend lead
* Main contribution: FastAPI backend, authentication, stress-test engine integration, RAG-backed advice/chat, API contracts, schemas, service structure, tests and backend/frontend integration support

## Core features

| Area               | What it does                                                                                                         |
| ------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Authentication     | Register, login, logout, password reset flow, HttpOnly JWT cookies and Argon2 server-side password hashing           |
| Financial profile  | Stores income, expenses, savings buffer, employment context and user financial information                           |
| Spending breakdown | Categorises spending against needs, wants and savings style targets                                                  |
| Goal planning      | Savings goals, progress tracking and forecast support                                                                |
| Stress testing     | Runs deterministic scenarios such as job loss, emergency expense and promotion to estimate financial resilience      |
| AI advice and chat | Uses retrieval-augmented generation with FAISS and sentence-transformers, then calls an LLM provider when configured |
| CSV upload         | Parses bank CSV files, previews transactions and maps spending into profile categories                               |
| Frontend           | React, TypeScript and Vite dashboard for onboarding, goals, stress testing, advice and chat                          |

## Tech stack

| Layer           | Tools                                                                       |
| --------------- | --------------------------------------------------------------------------- |
| Backend         | Python, FastAPI, SQLAlchemy, SQLite, Pydantic                               |
| Auth            | JWT, HttpOnly cookies, Argon2                                               |
| AI / RAG        | FAISS, sentence-transformers, OpenAI API wrapper with fallback behaviour    |
| ML / Simulation | scikit-learn, deterministic stress engine, optional generated cutback model |
| Frontend        | React, TypeScript, Vite, Tailwind CSS, shadcn/ui, wretch                    |
| Testing         | pytest, Vitest, React Testing Library                                       |

## Repository layout

```text
finlit-portfolio/
├── backend/      # FastAPI backend
├── frontend/     # React / TypeScript frontend
├── .gitignore
└── README.md
```

## Quick start

Run the backend and frontend in separate terminal windows.

### 1. Backend

```bash
cd backend
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

```text
API: http://localhost:8000
Swagger docs: http://localhost:8000/docs
Health check: http://localhost:8000/health
```

The SQLite database is created automatically on first startup.

### 2. Frontend

```bash
cd frontend
cp .env.example .env
bun install
bun run dev
```

Frontend URL:

```text
http://localhost:5173
```

Use `localhost` rather than `127.0.0.1` for both services so browser cookies behave correctly during local development.

## Optional AI setup

The app runs without an LLM API key, but advice/chat features will use fallback behaviour. To enable live LLM calls, set this in `backend/.env`:

```env
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key-here
```

Do not commit your `.env` file.

## Optional password reset email setup

The public version does not include SMTP credentials. To send real password reset emails, configure these in `backend/.env`:

```env
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your-email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
MAIL_USE_CREDENTIALS=true
```

For local development only, you can set:

```env
RETURN_RESET_TOKEN_IN_RESPONSE=true
```

Keep this false in any shared, hosted or deployed environment.

## Optional ML artifact

The trained `cutback_model.joblib` file is not included in this public version. The app still works without it because the stress-test service falls back to rule-based defaults.

To regenerate the optional model locally:

```bash
cd backend
python -m app.ml.cutback_model
```

## Tests

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
bun run test
```

## Notes for recruiters and reviewers

This was a university group project, not a production financial product. The portfolio value is in the architecture and implementation: security-conscious browser authentication patterns, typed API contracts, service-layer backend structure, deterministic simulation logic, RAG integration, testing and full-stack integration.

No real financial advice should be inferred from the demo outputs.

## Licence

No open-source licence is currently provided. This repository is shared for portfolio and review purposes.

