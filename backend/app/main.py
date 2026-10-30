from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import answer, evaluate, health, query, retrieve
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm hybrid retrieval engine and embedder once at startup
    try:
        from app.api.routes.retrieve import get_hybrid_retrieval_engine
        get_hybrid_retrieval_engine()
    except Exception:
        pass
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(query.router, prefix=settings.api_prefix)
app.include_router(retrieve.router, prefix=settings.api_prefix)
app.include_router(evaluate.router, prefix=settings.api_prefix)
app.include_router(answer.router, prefix=settings.api_prefix)
