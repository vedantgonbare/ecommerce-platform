import time


from app.core.celery_app import celery_app


@celery_app.task(name="orders.send_order_confirmation")
def send_order_confirmation(order_id: str):
    time.sleep(3)  # simulate network latency to an email provider
    print(f"[order confirmation] Simulated email sent for order {order_id}")
    return {"order_id": order_id, "status": "sent"}