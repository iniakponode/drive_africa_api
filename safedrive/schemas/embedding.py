from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class EmbeddingBase(BaseModel):
    chunk_id: UUID
    chunk_text: str
    embedding: str
    source_type: str
    source_page: int
    created_at: datetime
    synced: bool

    class Config:
        orm_mode = True

class EmbeddingCreate(BaseModel):
    chunk_text: str
    embedding: str
    source_type: str
    source_page: int
    synced: Optional[bool] = False

class EmbeddingUpdate(BaseModel):
    chunk_text: Optional[str] = None
    embedding: Optional[str] = None
    source_type: Optional[str] = None
    source_page: Optional[int] = None
    synced: Optional[bool] = None

class EmbeddingResponse(EmbeddingBase):
    pass