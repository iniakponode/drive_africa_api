from sqlalchemy import Boolean, Column, String, Integer, DateTime, BINARY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BINARY
from safedrive.database.base import Base
from uuid import uuid4, UUID
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_uuid_binary():
    return uuid4().bytes

class Embedding(Base):
    """
    Embedding model representing the text embedding table in the database.

    Attributes:
    - **chunk_id**: Primary key UUID for each text embedding.
    - **chunk_text**: The chunk of text.
    - **embedding**: Base64 encoded embedding for the text.
    - **source_type**: Source type of the chunked text (e.g., Research Article).
    - **source_page**: Page number from where the text originates.
    - **created_at**: Timestamp of creation.
    """

    __tablename__ = "embedding"

    chunk_id = Column(BINARY(16), primary_key=True, default=generate_uuid_binary)
    chunk_text = Column(String(255), nullable=False)
    embedding = Column(String(1024), nullable=False)
    source_type = Column(String(50), nullable=False)
    source_page = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    synced=Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Embedding(chunk_id={self.chunk_id.hex()}, source_type={self.source_type}, source_page={self.source_page})>"

    @property
    def id_uuid(self) -> UUID:
        return UUID(bytes=self.chunk_id)