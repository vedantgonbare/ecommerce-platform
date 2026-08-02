import pytest
import pytest_asyncio
import uuid


@pytest_asyncio.fixture
async def test_product(client):
    """Creates a fresh category + product for a single test and returns the product's id (str)."""
    category_response = await client.post("/categories/", json={
        "name": f"Cart Test Category {uuid.uuid4().hex[:8]}"
    })
    category_id = category_response.json()["id"]

    product_response = await client.post("/products/", json={
        "name": f"Cart Test Product {uuid.uuid4().hex[:8]}",
        "price": "25.00",
        "stock_quantity": 100,
        "category_id": category_id
    })
    return product_response.json()["id"]


@pytest.mark.asyncio
async def test_cart_requires_auth(client):
    response = await client.get("/cart/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_view_empty_cart(client, auth_headers):
    response = await client.get("/cart/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["subtotal"] == "0"


@pytest.mark.asyncio
async def test_add_item_to_cart(client, auth_headers, test_product):
    response = await client.post("/cart/items", json={
        "product_id": test_product,
        "quantity": 2
    }, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["subtotal"] == "50.00"


@pytest.mark.asyncio
async def test_add_item_bumps_quantity(client, auth_headers, test_product):
    await client.post("/cart/items", json={
        "product_id": test_product,
        "quantity": 2
    }, headers=auth_headers)

    response = await client.post("/cart/items", json={
        "product_id": test_product,
        "quantity": 3
    }, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 5


@pytest.mark.asyncio
async def test_add_item_bad_product(client, auth_headers):
    fake_product_id = str(uuid.uuid4())

    response = await client.post("/cart/items", json={
        "product_id": fake_product_id,
        "quantity": 1
    }, headers=auth_headers)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_item_quantity(client, auth_headers, test_product):
    await client.post("/cart/items", json={
        "product_id": test_product,
        "quantity": 1
    }, headers=auth_headers)

    response = await client.put(f"/cart/items/{test_product}", json={
        "quantity": 7
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["quantity"] == 7


@pytest.mark.asyncio
async def test_update_item_not_in_cart(client, auth_headers, test_product):
    response = await client.put(f"/cart/items/{test_product}", json={
        "quantity": 3
    }, headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_item(client, auth_headers, test_product):
    await client.post("/cart/items", json={
        "product_id": test_product,
        "quantity": 1
    }, headers=auth_headers)

    first_delete = await client.delete(f"/cart/items/{test_product}", headers=auth_headers)
    assert first_delete.status_code == 200
    assert first_delete.json()["items"] == []

    second_delete = await client.delete(f"/cart/items/{test_product}", headers=auth_headers)
    assert second_delete.status_code == 404