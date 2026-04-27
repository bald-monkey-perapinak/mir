import logging
import os
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database…")
    await init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info("Database initialised.")
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
