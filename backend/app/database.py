import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# When false (default), the app runs with NO database and never tries to connect.
USE_DB = os.getenv("USE_DB", "false").lower() == "true"

DB_USER = os.getenv("DB_USER", "chatbot_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")

# Base is always needed so the models can be defined (this does not connect).
Base = declarative_base()

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = None
SessionLocal = None

if USE_DB:
    # Create the schema and async engine only when a database is enabled.
    # Wrapped so an unreachable database logs a warning instead of crashing the app.
    try:
        sync_engine = create_engine(
            SQLALCHEMY_DATABASE_URL.replace("+asyncpg", ""),
            pool_size=5, max_overflow=10, pool_timeout=30, pool_recycle=1800,
        )
        with sync_engine.connect() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS chatbot"))
            connection.commit()
    except Exception as e:
        logger.warning(f"Database schema setup skipped (could not connect): {e}")

    try:
        engine = create_async_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_size=5, max_overflow=10, pool_timeout=30, pool_recycle=1800,
        )
        SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    except Exception as e:
        logger.warning(f"Async DB engine setup skipped: {e}")


async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
