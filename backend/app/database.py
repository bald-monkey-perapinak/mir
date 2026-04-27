import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings

def _make_engine():
\
\
\
\
\
\
\
\
\
       
    import urllib.parse

    url = settings.DATABASE_URL

                                                                                
                                                       
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

                                                                                
                                                                   
    parsed = urllib.parse.urlparse(url)
    params = dict(urllib.parse.parse_qsl(parsed.query))

                                                                  
    wants_ssl = (
        params.pop("sslmode",          "").lower() in (
            "require", "verify-full", "verify-ca")
        or params.pop("ssl",           "").lower() in ("require", "true", "1")
                                            
        or params.pop("channel_binding", "") != ""
    )

                                                   
    clean_query = urllib.parse.urlencode(params)
    clean_url = urllib.parse.urlunparse(parsed._replace(query=clean_query))

                                                                                
    connect_args: dict = {}
    if wants_ssl:
                                                                                  
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE                                         
        connect_args["ssl"] = ssl_ctx

    return create_async_engine(
        clean_url,
        echo=False,
                                                                   
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args=connect_args,
    )

engine = _make_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
                                                       
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
