from pydantic import BaseModel
import uuid
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    parent_id: uuid.UUID | None = None

class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None
    created_at: datetime

    class Config:
        from_attributes = True