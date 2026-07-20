import os
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres18@localhost:5433/ecommerce_test"
import pytest_asyncio
from app.db.base import Base
from app.modules.users.models import User  # noqa: F401 — import registers the table
from app.db.session import engine
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import async_session_factory
from app.db.session import get_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with async_session_factory() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac