from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.database import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AT-SV Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from src.api.routes import auth, health, users, taxes, transactions

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(taxes.router, prefix="/api/v1")
    app.include_router(transactions.router, prefix="/api/v1")

    return app


app = create_app()
