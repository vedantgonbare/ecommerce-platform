import time

from app.core.celery_app import celery_app


@celery_app.task(name="payments.send_payment_confirmation")
def send_payment_confirmation(order_id: str):
    time.sleep(3)  # simulate network latency to an email provider
    print(f"[payment confirmation] Simulated email sent for order {order_id}")
    return {"order_id": order_id, "status": "sent"}