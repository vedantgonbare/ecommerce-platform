import uuid
from unittest.mock import patch, MagicMock

import pytest


@pytest.mark.asyncio
async def test_checkout_order_success(client, auth_headers, pending_order):
    fake_session = MagicMock()
    fake_session.id = "cs_test_fake123"
    fake_session.url = "https://checkout.stripe.com/c/pay/cs_test_fake123"

    with patch("stripe.checkout.Session.create", return_value=fake_session):
        response = await client.post(
            f"/orders/{pending_order}/checkout", headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "cs_test_fake123"
    assert data["checkout_url"] == "https://checkout.stripe.com/c/pay/cs_test_fake123"


@pytest.mark.asyncio
async def test_checkout_order_not_found(client, auth_headers):
    fake_order_id = str(uuid.uuid4())

    with patch("stripe.checkout.Session.create") as mock_create:
        response = await client.post(
            f"/orders/{fake_order_id}/checkout", headers=auth_headers
        )

    assert response.status_code == 404
    mock_create.assert_not_called()

@pytest.mark.asyncio
async def test_webhook_checkout_completed_marks_order_paid(
    client, auth_headers, pending_order
):
    fake_event = {
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"order_id": pending_order}}},
    }

    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        response = await client.post(
            "/orders/webhook",
            content=b"{}",
            headers={"stripe-signature": "fake_sig"},
        )

    assert response.status_code == 200

    order_response = await client.get(f"/orders/{pending_order}", headers=auth_headers)
    assert order_response.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_webhook_invalid_signature_returns_400(client):
    import stripe

    with patch(
        "stripe.Webhook.construct_event",
        side_effect=stripe.error.SignatureVerificationError("bad sig", "sig_header"),
    ):
        response = await client.post(
            "/orders/webhook",
            content=b"{}",
            headers={"stripe-signature": "wrong_sig"},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_payment_success_returns_order(client, auth_headers, pending_order):
    fake_session = MagicMock()
    fake_session.id = "cs_test_success456"
    fake_session.url = "https://checkout.stripe.com/c/pay/cs_test_success456"

    with patch("stripe.checkout.Session.create", return_value=fake_session):
        await client.post(f"/orders/{pending_order}/checkout", headers=auth_headers)

    response = await client.get(
        "/orders/success", params={"session_id": "cs_test_success456"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == pending_order


@pytest.mark.asyncio
async def test_payment_success_unknown_session_returns_404(client):
    response = await client.get(
        "/orders/success", params={"session_id": "cs_test_does_not_exist"}
    )

    assert response.status_code == 404