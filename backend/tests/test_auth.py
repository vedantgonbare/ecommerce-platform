import pytest

@pytest.mark.asyncio
async def test_register_success(client):
    response = await client.post("/auth/register", json={
        "email": "testuser1@example.com",
        "password": "SecurePass123!"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser1@example.com"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "SecurePass123!"
    })

    response = await client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "AnotherPass456!"
    })

    assert response.status_code == 409

@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/auth/register", json={
        "email": "loginuser@example.com",
        "password": "SecurePass123!"
    })

    response = await client.post("/auth/login", json={
        "email": "loginuser@example.com",
        "password": "SecurePass123!"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data