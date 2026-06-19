# FinLit Backend

FastAPI backend for FinLit. It provides authentication, financial profile storage, spending analysis, savings goals, stress-test simulations, CSV upload, AI-assisted chat and structured advice.

## Setup

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger docs:

```text
http://localhost:8000/docs
```

## Environment variables

See `.env.example` for all settings.

Minimum local setup:

```env
DATABASE_URL=sqlite:///./finlit.db
JWT_SECRET=change-me-in-production-use-a-long-random-string
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key-here
```

LLM and SMTP settings are optional for local review. The app includes fallback behaviour when no LLM key is configured.

## Architecture

```text
backend/
├── app/
│   ├── main.py                  # FastAPI app factory, CORS, health check, DB table creation
│   ├── core/                    # Settings, JWT, password hashing
│   ├── db/                      # SQLAlchemy models and session handling
│   ├── schemas/                 # Pydantic request/response models
│   ├── api/v1/endpoints/        # FastAPI routes by feature area
│   ├── services/                # Business logic
│   ├── rag/                     # FAISS retriever and financial knowledge base
│   ├── ml/                      # Stress-test engine and optional cutback model
│   └── tests/                   # pytest suite
├── requirements.txt
├── requirements-torch-cpu.txt
└── pytest.ini
```

## Key backend design choices

- Endpoints stay thin. Validation and request/response handling live in routers, while business logic lives in services.
- Pydantic schemas define API contracts between frontend and backend.
- SQLAlchemy models are not returned directly to the frontend.
- Auth uses HttpOnly JWT cookies and Argon2 server-side password hashing.
- The stress-test engine is deterministic and explainable rather than a black-box prediction engine.
- RAG retrieves relevant financial knowledge-base chunks with FAISS before calling the LLM provider.

## Tests

```bash
pytest
```
