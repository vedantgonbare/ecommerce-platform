from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    parent_id: uuid.UUID | None = None

class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None
    created_at: datetime


class CategoryUpdate(BaseModel):
    name: str | None = None
    parent_id: uuid.UUID | None = None