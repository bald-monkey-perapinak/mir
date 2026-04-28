from pathlib import Path
from pydantic_settings import BaseSettings

_ROOT_ENV = Path(__file__).parents[2] / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/medical_trainer"
    REDIS_URL: str    = "redis://redis:6379"

    JWT_SECRET:       str = "change-me-in-production"
    JWT_ALGORITHM:    str = "HS256"
    JWT_EXPIRE_HOURS: int = 48

    BOT_TOKEN:          str = ""
    WEBAPP_URL:         str = "http://localhost:3000"
    ALLOWED_ORIGINS:    str = ""
    ADMIN_TELEGRAM_IDS: str = ""

    GROQ_API_KEY: str = ""
    GROQ_MODEL:   str = "llama-3.1-8b-instant"

    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIM:   int = 384

    UPLOAD_DIR:       str = "/app/uploads"
    MAX_FILE_SIZE_MB: int = 50

    class Config:
        env_file = str(_ROOT_ENV)

    def get_admin_ids(self) -> list[int]:
        if not self.ADMIN_TELEGRAM_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_TELEGRAM_IDS.split(",") if x.strip()]

    def get_allowed_origins(self) -> list[str]:
        origins = set()
        if self.WEBAPP_URL:
            origins.add(self.WEBAPP_URL.rstrip("/"))
        if self.ALLOWED_ORIGINS:
            for o in self.ALLOWED_ORIGINS.split(","):
                o = o.strip().rstrip("/")
                if o:
                    origins.add(o)
        return list(origins) if origins else ["*"]


settings = Settings()
