from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# The engine manages the actual connection pool to Postgres.
# Created once, reused for the life of the app.
engine = create_async_engine(settings.database_url, echo=True)

# A factory that produces new AsyncSession objects on demand.
# We don't create one global session — each request gets its own.
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Dependency for FastAPI routes: yields a session, closes it after.
async def get_db():
    async with async_session_factory() as session:
        yield session