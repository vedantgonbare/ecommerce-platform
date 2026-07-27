import pytest
import pytest_asyncio
import uuid
from decimal import Decimal


@pytest_asyncio.fixture
async def test_category(client):
    """Creates a fresh category for a single test and returns its id (str)."""
    response = await client.post("/categories/", json={
        "name": f"Test Category {uuid.uuid4().hex[:8]}"
    })
    assert response.status_code == 201
    return response.json()["id"]

@pytest.mark.asyncio
async def test_create_product_success(client, test_category):
    response = await client.post("/products/", json={
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse",
        "price": "29.99",
        "stock_quantity": 50,
        "category_id": test_category
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Wireless Mouse"
    assert data["price"] == "29.99"
    assert data["category_id"] == test_category
    assert "id" in data


@pytest.mark.asyncio
async def test_create_product_bad_category(client):
    fake_category_id = str(uuid.uuid4())

    response = await client.post("/products/", json={
        "name": "Orphan Product",
        "price": "10.00",
        "stock_quantity": 5,
        "category_id": fake_category_id
    })

    assert response.status_code == 400

@pytest.mark.asyncio
async def test_get_product_success(client, test_category):
    create_response = await client.post("/products/", json={
        "name": "Keyboard",
        "price": "49.99",
        "stock_quantity": 20,
        "category_id": test_category
    })
    product_id = create_response.json()["id"]

    response = await client.get(f"/products/{product_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == "Keyboard"


@pytest.mark.asyncio
async def test_get_product_not_found(client):
    fake_id = str(uuid.uuid4())

    response = await client.get(f"/products/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_product_partial(client, test_category):
    create_response = await client.post("/products/", json={
        "name": "Monitor",
        "description": "24-inch monitor",
        "price": "199.99",
        "stock_quantity": 10,
        "category_id": test_category
    })
    product_id = create_response.json()["id"]

    response = await client.put(f"/products/{product_id}", json={
        "stock_quantity": 15
    })

    assert response.status_code == 200
    data = response.json()
    assert data["stock_quantity"] == 15
    # Untouched fields must survive the partial update
    assert data["name"] == "Monitor"
    assert data["description"] == "24-inch monitor"
    assert data["price"] == "199.99"

@pytest.mark.asyncio
async def test_update_product_zero_value(client, test_category):
    create_response = await client.post("/products/", json={
        "name": "Clearance Item",
        "price": "5.00",
        "stock_quantity": 100,
        "category_id": test_category
    })
    product_id = create_response.json()["id"]

    response = await client.put(f"/products/{product_id}", json={
        "price": "0.00",
        "stock_quantity": 0
    })

    assert response.status_code == 200
    data = response.json()
    assert data["price"] == "0.00"
    assert data["stock_quantity"] == 0


@pytest.mark.asyncio
async def test_delete_product(client, test_category):
    create_response = await client.post("/products/", json={
        "name": "Discontinued Widget",
        "price": "12.00",
        "stock_quantity": 3,
        "category_id": test_category
    })
    product_id = create_response.json()["id"]

    first_delete = await client.delete(f"/products/{product_id}")
    assert first_delete.status_code == 204

    second_delete = await client.delete(f"/products/{product_id}")
    assert second_delete.status_code == 404

@pytest.mark.asyncio
async def test_search_products_with_results(client, test_category):
    unique_word = uuid.uuid4().hex[:8]
    await client.post("/products/", json={
        "name": f"Bluetooth Speaker {unique_word}",
        "price": "39.99",
        "stock_quantity": 10,
        "category_id": test_category
    })

    response = await client.get(f"/products/search?q={unique_word}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(unique_word in item["name"] for item in data)


@pytest.mark.asyncio
async def test_search_products_empty(client):
    response = await client.get("/products/search?q=zzzznonexistentqueryzzzz")

    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_pagination(client, test_category):
    for i in range(3):
        await client.post("/products/", json={
            "name": f"Pagination Item {i} {uuid.uuid4().hex[:6]}",
            "price": "10.00",
            "stock_quantity": 1,
            "category_id": test_category
        })

    response = await client.get(f"/products/?category_id={test_category}&limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    response_page_2 = await client.get(f"/products/?category_id={test_category}&limit=2&offset=2")
    data_page_2 = response_page_2.json()
    assert data_page_2["total"] == 3
    assert len(data_page_2["items"]) == 1


@pytest.mark.asyncio
async def test_filter_by_category(client, test_category):
    other_category_resp = await client.post("/categories/", json={
        "name": f"Other Category {uuid.uuid4().hex[:8]}"
    })
    other_category_id = other_category_resp.json()["id"]

    await client.post("/products/", json={
        "name": f"In Test Category {uuid.uuid4().hex[:6]}",
        "price": "10.00",
        "stock_quantity": 1,
        "category_id": test_category
    })
    await client.post("/products/", json={
        "name": f"In Other Category {uuid.uuid4().hex[:6]}",
        "price": "10.00",
        "stock_quantity": 1,
        "category_id": other_category_id
    })

    response = await client.get(f"/products/?category_id={test_category}")
    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["category_id"] == test_category