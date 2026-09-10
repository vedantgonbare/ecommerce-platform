import pytest
import pytest_asyncio
import uuid
from unittest.mock import patch
from app.core.redis import invalidate_pattern
from app.modules.products.service import get_all_products as real_get_all_products


@pytest_asyncio.fixture(autouse=True)
async def clear_products_cache():
    """Ensures every cache test starts and ends with no leftover products:list:* keys,
    so tests can't bleed into each other or into dev data."""
    await invalidate_pattern("products:list:*")
    yield
    await invalidate_pattern("products:list:*")

@pytest_asyncio.fixture
async def product_with_category(client):
    """Creates a fresh category + product for cache tests, returns both ids."""
    category_response = await client.post("/categories/", json={
        "name": f"Cache Test Category {uuid.uuid4().hex[:8]}"
    })
    category_id = category_response.json()["id"]

    product_response = await client.post("/products/", json={
        "name": f"Cache Test Product {uuid.uuid4().hex[:8]}",
        "price": "25.00",
        "stock_quantity": 100,
        "category_id": category_id,
    })
    product_id = product_response.json()["id"]

    return {"product_id": product_id, "category_id": category_id}

@pytest.mark.asyncio
async def test_list_products_cache_populates_key(client, product_with_category):
    category_id = product_with_category["category_id"]
    cache_key = f"products:list:limit=20:offset=0:category_id={category_id}"

    from app.core.redis import redis_client
    assert await redis_client.get(cache_key) is None  # sanity check: nothing cached yet

    response = await client.get(f"/products/?category_id={category_id}")
    assert response.status_code == 200

    cached_value = await redis_client.get(cache_key)
    assert cached_value is not None

@pytest.mark.asyncio
async def test_list_products_cache_hit_skips_db(client, product_with_category):
    category_id = product_with_category["category_id"]

    with patch(
        "app.modules.products.router.get_all_products",
        side_effect=real_get_all_products,
    ) as mock_get_all:
        response1 = await client.get(f"/products/?category_id={category_id}")
        assert response1.status_code == 200

        response2 = await client.get(f"/products/?category_id={category_id}")
        assert response2.status_code == 200

    assert mock_get_all.call_count == 1


@pytest.mark.asyncio
async def test_create_product_invalidates_cache(client, product_with_category):
    category_id = product_with_category["category_id"]
    cache_key = f"products:list:limit=20:offset=0:category_id={category_id}"

    from app.core.redis import redis_client

    # populate the cache first
    response = await client.get(f"/products/?category_id={category_id}")
    assert response.status_code == 200
    assert await redis_client.get(cache_key) is not None  # sanity check: cache is warm

    # creating a new product in the same category should invalidate the listing cache
    await client.post("/products/", json={
        "name": f"New Product {uuid.uuid4().hex[:8]}",
        "price": "30.00",
        "stock_quantity": 50,
        "category_id": category_id,
    })

    assert await redis_client.get(cache_key) is None


@pytest.mark.asyncio
async def test_update_product_invalidates_cache(client, product_with_category):
    category_id = product_with_category["category_id"]
    product_id = product_with_category["product_id"]
    cache_key = f"products:list:limit=20:offset=0:category_id={category_id}"

    from app.core.redis import redis_client

    response = await client.get(f"/products/?category_id={category_id}")
    assert response.status_code == 200
    assert await redis_client.get(cache_key) is not None  # sanity check: cache is warm

    await client.put(f"/products/{product_id}", json={"price": "40.00"})

    assert await redis_client.get(cache_key) is None


@pytest.mark.asyncio
async def test_delete_product_invalidates_cache(client, product_with_category):
    category_id = product_with_category["category_id"]
    product_id = product_with_category["product_id"]
    cache_key = f"products:list:limit=20:offset=0:category_id={category_id}"

    from app.core.redis import redis_client

    response = await client.get(f"/products/?category_id={category_id}")
    assert response.status_code == 200
    assert await redis_client.get(cache_key) is not None  # sanity check: cache is warm

    await client.delete(f"/products/{product_id}")

    assert await redis_client.get(cache_key) is None

@pytest.mark.asyncio
async def test_different_query_params_use_different_cache_keys(client, product_with_category):
    category_id = product_with_category["category_id"]

    from app.core.redis import redis_client

    response1 = await client.get(f"/products/?category_id={category_id}&offset=0")
    assert response1.status_code == 200

    response2 = await client.get(f"/products/?category_id={category_id}&offset=20")
    assert response2.status_code == 200

    key_offset_0 = f"products:list:limit=20:offset=0:category_id={category_id}"
    key_offset_20 = f"products:list:limit=20:offset=20:category_id={category_id}"

    assert await redis_client.get(key_offset_0) is not None
    assert await redis_client.get(key_offset_20) is not None