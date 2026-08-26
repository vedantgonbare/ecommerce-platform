import uuid
import pytest


@pytest.mark.asyncio
async def test_create_review_unverified_purchase_403(client, auth_headers, pending_order, test_product):
    response = await client.post(
        f"/products/{test_product}/reviews",
        json={"rating": 5, "comment": "Great!"},
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_review_success_201(client, auth_headers, paid_order, test_product):
    response = await client.post(
        f"/products/{test_product}/reviews",
        json={"rating": 4, "comment": "Solid product"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["rating"] == 4
    assert body["comment"] == "Solid product"


@pytest.mark.asyncio
async def test_create_review_invalid_rating_422(client, auth_headers, paid_order, test_product):
    response = await client.post(
        f"/products/{test_product}/reviews",
        json={"rating": 6, "comment": "Too high"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_product_reviews_empty_list(client, test_product):
    response = await client.get(f"/products/{test_product}/reviews")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_product_reviews_returns_created_review(client, auth_headers, paid_order, test_product):
    await client.post(
        f"/products/{test_product}/reviews",
        json={"rating": 3, "comment": "Okay"},
        headers=auth_headers,
    )
    # deliberately no auth_headers here — proves the GET route is public
    response = await client.get(f"/products/{test_product}/reviews")
    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 1
    assert reviews[0]["rating"] == 3


@pytest.mark.asyncio
async def test_update_review_success(client, auth_headers, paid_order, test_product):
    create_response = await client.post(
        f"/products/{test_product}/reviews",
        json={"rating": 2, "comment": "Meh"},
        headers=auth_headers,
    )
    review_id = create_response.json()["id"]

    response = await client.patch(
        f"/reviews/{review_id}",
        json={"rating": 5, "comment": "Actually great after using it more"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["rating"] == 5
    assert body["comment"] == "Actually great after using it more"


@pytest.mark.asyncio
async def test_update_review_not_found_404(client, auth_headers):
    fake_id = uuid.uuid4()
    response = await client.patch(
        f"/reviews/{fake_id}",
        json={"rating": 5},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_review_wrong_owner_404(client, auth_headers, paid_order, test_product):
    create_response = await client.post(
        f"/products/{test_product}/reviews",
        json={"rating": 4, "comment": "Owner's review"},
        headers=auth_headers,
    )
    review_id = create_response.json()["id"]

    other_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json={"email": other_email, "password": "SecurePass123!"})
    login_response = await client.post("/auth/login", json={"email": other_email, "password": "SecurePass123!"})
    other_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = await client.patch(
        f"/reviews/{review_id}",
        json={"rating": 1},
        headers=other_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_review_success_204(client, auth_headers, paid_order, test_product):
    create_response = await client.post(
        f"/products/{test_product}/reviews",
        json={"rating": 3, "comment": "To be deleted"},
        headers=auth_headers,
    )
    review_id = create_response.json()["id"]

    response = await client.delete(f"/reviews/{review_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_review_then_404_on_second_delete(client, auth_headers, paid_order, test_product):
    create_response = await client.post(
        f"/products/{test_product}/reviews",
        json={"rating": 3, "comment": "Delete me twice"},
        headers=auth_headers,
    )
    review_id = create_response.json()["id"]

    first = await client.delete(f"/reviews/{review_id}", headers=auth_headers)
    assert first.status_code == 204

    second = await client.delete(f"/reviews/{review_id}", headers=auth_headers)
    assert second.status_code == 404