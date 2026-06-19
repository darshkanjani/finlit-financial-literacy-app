"""

FastAPI entry point.

What happens on startup:
- app created
- CORS enabled so React can call the API
- routers mounted at /api/v1
- tables created in SQLite file if missing (dev/demo)

TODO:
- later: move create_all behind a flag if needed
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine
from app.db.base import Base  # models should inherit from this


def create_app() -> FastAPI:
    app = FastAPI(title="FinLit API", version="0.1")

    # CORS: let frontend dev server call backend
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

# create tables on startup (SQLite file persists, so not recreated each time)
Base.metadata.create_all(bind=engine)
