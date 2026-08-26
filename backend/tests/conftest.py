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
import uuid
from app.core.celery_app import celery_app
from app.modules.payments.service import mark_order_paid

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

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

@pytest_asyncio.fixture
async def auth_headers(client):
    email = f"cartuser_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123!"

    await client.post("/auth/register", json={"email": email, "password": password})
    login_response = await client.post("/auth/login", json={"email": email, "password": password})

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def test_product(client):
    """Creates a fresh category + product for a single test and returns the product's id (str)."""
    category_response = await client.post("/categories/", json={
        "name": f"Test Category {uuid.uuid4().hex[:8]}"
    })
    category_id = category_response.json()["id"]

    product_response = await client.post("/products/", json={
        "name": f"Test Product {uuid.uuid4().hex[:8]}",
        "price": "25.00",
        "stock_quantity": 100,
        "category_id": category_id
    })
    return product_response.json()["id"]


@pytest_asyncio.fixture
async def pending_order(client, auth_headers, test_product):
    """Creates a cart item + order for a single test, returns the order's id (str)."""
    await client.post(
        "/cart/items",
        json={"product_id": test_product, "quantity": 2},
        headers=auth_headers,
    )
    order_response = await client.post("/orders/", headers=auth_headers)
    return order_response.json()["id"]

@pytest_asyncio.fixture
async def paid_order(pending_order):
    """Takes a pending_order and marks it paid directly via the internal
    trusted-caller function — bypassing Stripe entirely, since we're testing
    review logic, not payments."""
    async with async_session_factory() as session:
        await mark_order_paid(session, pending_order)
    return pending_order