from fastapi import FastAPI
from app.core.config import settings
from app.db.session import engine
from sqlalchemy import text
from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router


app = FastAPI(title="E-Commerce Platform")

@app.get("/health")
def health_check():
    return {"status":"ok","app": settings.app_name}

@app.get("/db-check")
async def db_check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        return{"db_connected": result.scalar() == 1}
    
app.include_router(categories_router)