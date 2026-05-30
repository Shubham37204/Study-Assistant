from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import query, upload
from api.routes.documents import router as documents_router
from api.routes.jobs import router as jobs_router
from config import settings
from core.cache import ping_redis
from db.database import create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _configure_langsmith() -> None:
    if not settings.langchain_api_key:
        return
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"]     = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"]     = settings.langchain_project
    logger.info("LangSmith tracing enabled for project: %s", settings.langchain_project)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    _configure_langsmith()
    create_tables()

    redis_ok = ping_redis()
    logger.info("Redis: %s", "connected" if redis_ok else "unavailable (cache disabled)")

    yield

    logger.info("Shutting down")


app = FastAPI(
    title="Study Assistant API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(query.router)
app.include_router(documents_router)
app.include_router(jobs_router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "redis": ping_redis(),
    }
