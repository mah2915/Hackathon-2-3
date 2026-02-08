"""
Database connection and session management.
"""
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings


settings = get_settings()

def clean_database_url(original_url: str) -> str:
    """
    Clean the database URL to be compatible with asyncpg.
    Removes problematic parameters and ensures proper format.
    """
    # Handle Neon's psql format first
    if original_url.startswith("psql '"):
        # Extract the actual PostgreSQL URL from the psql wrapper
        import re
        match = re.search(r"psql '(.*)'", original_url)
        if match:
            original_url = match.group(1)

    # Parse the URL
    parsed = urlparse(original_url)

    # Parse query parameters
    query_params = parse_qs(parsed.query)

    # Remove parameters that cause issues with asyncpg
    problematic_params = ['sslmode', 'channel_binding']
    for param in problematic_params:
        query_params.pop(param, None)

    # Reconstruct query string without problematic parameters
    clean_query = urlencode(query_params, doseq=True)

    # Reconstruct URL with clean query string
    clean_url = parsed._replace(query=clean_query).geturl()

    # Replace with asyncpg driver
    if clean_url.startswith("postgresql://"):
        clean_url = clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return clean_url

# Convert PostgreSQL URL to async format and clean problematic parameters
database_url = clean_database_url(settings.DATABASE_URL)

# Create async engine with connection pooling
engine = create_async_engine(
    database_url,
    echo=False,  # Set to True for SQL query logging
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """
    Initialize database tables.
    Creates all tables defined in SQLModel metadata.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    Yields a session and ensures it's closed after use.
    """
    async with async_session_maker() as session:
        yield session
