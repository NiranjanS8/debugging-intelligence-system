from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("Starting DIS", extra={"operation": "startup", "env": settings.app_env})

    for subdir in ("frontend", "backend", "infra", "uncategorized"):
        (settings.knowledge_base_path / subdir).mkdir(parents=True, exist_ok=True)
    settings.chroma_persist_path.mkdir(parents=True, exist_ok=True)

    logger.info("DIS is ready", extra={"operation": "startup"})
    yield
    logger.info("Shutting down DIS", extra={"operation": "shutdown"})


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "An LLM-powered system that converts debugging sessions into "
            "a self-evolving knowledge base with semantic search, similarity "
            "detection, and debugging intelligence."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["System"])
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": "0.1.0",
            "environment": settings.app_env,
        }

    # Routes registered in later phases
    # from app.api.debug_routes import router as debug_router
    # app.include_router(debug_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
