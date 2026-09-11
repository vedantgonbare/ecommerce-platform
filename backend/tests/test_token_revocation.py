import uuid
import pytest

@pytest.mark.asyncio
async def test_refresh_after_logout_rejected(client):
    email = f"revoke_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123!"

    await client.post("/auth/register", json={"email": email, "password": password})
    await client.post("/auth/login", json={"email": email, "password": password})

    logout_response = await client.post("/auth/logout")
    assert logout_response.status_code == 200

    refresh_response = await client.post("/auth/refresh")
    assert refresh_response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_without_logout_succeeds(client):
    email = f"norevoke_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123!"

    await client.post("/auth/register", json={"email": email, "password": password})
    await client.post("/auth/login", json={"email": email, "password": password})

    refresh_response = await client.post("/auth/refresh")
    assert refresh_response.status_code == 200


@pytest.mark.asyncio
async def test_logout_with_no_cookies_succeeds(client):
    response = await client.post("/auth/logout")
    assert response.status_code == 200