import pytest
import pytest_asyncio
import uuid


@pytest_asyncio.fixture
async def order_from_cart(client, auth_headers, test_product):
    """Adds an item to cart and creates an order, returning the order response JSON."""
    await client.post("/cart/items", json={
        "product_id": test_product,
        "quantity": 2
    }, headers=auth_headers)

    response = await client.post("/orders/", headers=auth_headers)
    return response.json()


@pytest.mark.asyncio
async def test_orders_requires_auth(client):
    response = await client.get("/orders/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_order_success(client, auth_headers, test_product):
    await client.post("/cart/items", json={
        "product_id": test_product,
        "quantity": 3
    }, headers=auth_headers)

    response = await client.post("/orders/", headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["status"] == "pending"
    assert data["total"] == "75.00"  # 25.00 * 3
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 3


@pytest.mark.asyncio
async def test_create_order_empty_cart(client, auth_headers):
    response = await client.post("/orders/", headers=auth_headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(client, auth_headers, test_product):
    await client.post("/cart/items", json={
        "product_id": test_product,
        "quantity": 999
    }, headers=auth_headers)

    response = await client.post("/orders/", headers=auth_headers)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_order_decrements_stock_and_clears_cart(client, auth_headers, test_product):
    before = await client.get(f"/products/{test_product}")
    stock_before = before.json()["stock_quantity"]

    await client.post("/cart/items", json={
        "product_id": test_product,
        "quantity": 4
    }, headers=auth_headers)
    await client.post("/orders/", headers=auth_headers)

    after = await client.get(f"/products/{test_product}")
    assert after.json()["stock_quantity"] == stock_before - 4

    cart = await client.get("/cart/", headers=auth_headers)
    assert cart.json()["items"] == []


@pytest.mark.asyncio
async def test_list_orders(client, auth_headers, order_from_cart):
    response = await client.get("/orders/", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert any(o["id"] == order_from_cart["id"] for o in data["items"])


@pytest.mark.asyncio
async def test_get_order_by_id(client, auth_headers, order_from_cart):
    response = await client.get(f"/orders/{order_from_cart['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == order_from_cart["id"]


@pytest.mark.asyncio
async def test_get_order_not_found(client, auth_headers):
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/orders/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_order_wrong_owner(client, auth_headers, order_from_cart):
    other_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json={"email": other_email, "password": "SecurePass123!"})
    await client.post("/auth/login", json={"email": other_email, "password": "SecurePass123!"})

    response = await client.get(f"/orders/{order_from_cart['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_order_success(client, auth_headers, order_from_cart):
    response = await client.patch(f"/orders/{order_from_cart['id']}/cancel", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_order_already_cancelled(client, auth_headers, order_from_cart):
    await client.patch(f"/orders/{order_from_cart['id']}/cancel", headers=auth_headers)
    response = await client.patch(f"/orders/{order_from_cart['id']}/cancel", headers=auth_headers)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cancel_order_restores_stock(client, auth_headers, test_product, order_from_cart):
    # order_from_cart already reserved 2 units, so read stock AFTER the order exists
    after_order = await client.get(f"/products/{test_product}")
    stock_after_order = after_order.json()["stock_quantity"]

    response = await client.patch(f"/orders/{order_from_cart['id']}/cancel", headers=auth_headers)
    assert response.status_code == 200

    after_cancel = await client.get(f"/products/{test_product}")
    assert after_cancel.json()["stock_quantity"] == stock_after_order + 2


@pytest.mark.asyncio
async def test_cancel_order_twice_does_not_restore_stock_twice(
    client, auth_headers, test_product, order_from_cart
):
    await client.patch(f"/orders/{order_from_cart['id']}/cancel", headers=auth_headers)
    after_first = await client.get(f"/products/{test_product}")
    stock_after_first = after_first.json()["stock_quantity"]

    second = await client.patch(f"/orders/{order_from_cart['id']}/cancel", headers=auth_headers)
    assert second.status_code == 409

    after_second = await client.get(f"/products/{test_product}")
    assert after_second.json()["stock_quantity"] == stock_after_first


@pytest.mark.asyncio
async def test_cancel_paid_order_returns_409(client, auth_headers, test_product, paid_order):
    before = await client.get(f"/products/{test_product}")
    stock_before = before.json()["stock_quantity"]

    response = await client.patch(f"/orders/{paid_order}/cancel", headers=auth_headers)
    assert response.status_code == 409

    # order stays paid and stock is untouched
    order = await client.get(f"/orders/{paid_order}", headers=auth_headers)
    assert order.json()["status"] == "paid"
    after = await client.get(f"/products/{test_product}")
    assert after.json()["stock_quantity"] == stock_before


@pytest.mark.asyncio
async def test_create_order_with_multiple_products_decrements_each(
    client, auth_headers, admin_client, test_product
):
    # test_product gives us product A; create a second product B with its own category
    category = await admin_client.post("/categories/", json={
        "name": f"Test Category {uuid.uuid4().hex[:8]}"
    })
    second = await admin_client.post("/products/", json={
        "name": f"Test Product {uuid.uuid4().hex[:8]}",
        "price": "10.00",
        "stock_quantity": 50,
        "category_id": category.json()["id"],
    })
    second_id = second.json()["id"]

    a_before = (await client.get(f"/products/{test_product}")).json()["stock_quantity"]
    b_before = (await client.get(f"/products/{second_id}")).json()["stock_quantity"]

    await client.post("/cart/items", json={"product_id": test_product, "quantity": 3}, headers=auth_headers)
    await client.post("/cart/items", json={"product_id": second_id, "quantity": 2}, headers=auth_headers)

    response = await client.post("/orders/", headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == "95.00"  # 25.00 * 3 + 10.00 * 2

    a_after = (await client.get(f"/products/{test_product}")).json()["stock_quantity"]
    b_after = (await client.get(f"/products/{second_id}")).json()["stock_quantity"]
    assert a_after == a_before - 3
    assert b_after == b_before - 2