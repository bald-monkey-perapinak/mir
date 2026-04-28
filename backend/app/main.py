import logging
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.scenarios import router as scenarios_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _prewarm() -> None:
    """
    Фоновая задача: компилирует LangGraph-графы и загружает модель эмбеддингов
    сразу при старте, чтобы первый реальный запрос не тормозил.
    """
    try:
        # 1. Компилируем все три LangGraph-графа (каждый ~0.1–0.3 с)
        from app.processor import _get_graph as _doc_graph
        from app.scenario_generator import _get_graph as _scen_graph
        from app.training_engine import _get_graph as _engine_graph

        _doc_graph()
        _scen_graph()
        _engine_graph()
        logger.info("[prewarm] LangGraph graphs compiled ✓")

        # 2. Загружаем ONNX-модель эмбеддингов (fastembed, ~0.3 с)
        #    Запускаем в потоке, чтобы не блокировать event loop
        from app.llm import embeddings
        emb = embeddings()
        await asyncio.to_thread(emb._load)
        logger.info("[prewarm] Embedding model loaded ✓")

    except Exception as exc:  # не роняем приложение из-за прогрева
        logger.warning(f"[prewarm] non-fatal error: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database…")
    await init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info("Database initialised.")

    # Запускаем прогрев параллельно — API уже принимает запросы,
    # а модели грузятся в фоне (обычно готовы через ~1 с после старта)
    asyncio.create_task(_prewarm())

    logger.info("API ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="AI Medical Trainer",
    version="1.0.0",
    lifespan=lifespan,
)

_origins = settings.get_allowed_origins()
_wildcard = _origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=not _wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(scenarios_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
