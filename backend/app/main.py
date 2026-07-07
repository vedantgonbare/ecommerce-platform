from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title="E-Commerce Platform")

@app.get("/health")
def health_check():
    return {"status":"ok","app": settings.app_name}