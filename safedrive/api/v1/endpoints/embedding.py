from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from safedrive.database.db import get_db
from safedrive.schemas.embedding import EmbeddingCreate, EmbeddingUpdate, EmbeddingResponse
from safedrive.crud.embedding import embedding_crud
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/embeddings/", response_model=EmbeddingResponse)
def create_embedding(*, db: Session = Depends(get_db), embedding_in: EmbeddingCreate) -> EmbeddingResponse:
    try:
        new_embedding = embedding_crud.create(db=db, obj_in=embedding_in)
        logger.info(f"Created Embedding with ID: {new_embedding.chunk_id.hex()}")
        return EmbeddingResponse(chunk_id=new_embedding.id_uuid, **embedding_in.dict(), created_at=new_embedding.created_at)
    except Exception as e:
        logger.error(f"Error creating Embedding: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating embedding")

@router.get("/embeddings/{embedding_id}", response_model=EmbeddingResponse)
def get_embedding(embedding_id: UUID, db: Session = Depends(get_db)) -> EmbeddingResponse:
    embedding = embedding_crud.get(db=db, id=embedding_id)
    if not embedding:
        logger.warning(f"Embedding with ID {embedding_id} not found.")
        raise HTTPException(status_code=404, detail="Embedding not found")
    logger.info(f"Retrieved Embedding with ID: {embedding_id}")
    return EmbeddingResponse(chunk_id=embedding.id_uuid, chunk_text=embedding.chunk_text, embedding=embedding.embedding, source_type=embedding.source_type, source_page=embedding.source_page, created_at=embedding.created_at)

@router.get("/embeddings/", response_model=List[EmbeddingResponse])
def get_all_embeddings(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)) -> List[EmbeddingResponse]:
    embeddings = embedding_crud.get_all(db=db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(embeddings)} Embeddings.")
    return [EmbeddingResponse(chunk_id=embed.id_uuid, chunk_text=embed.chunk_text, embedding=embed.embedding, source_type=embed.source_type, source_page=embed.source_page, created_at=embed.created_at) for embed in embeddings]

@router.put("/embeddings/{embedding_id}", response_model=EmbeddingResponse)
def update_embedding(embedding_id: UUID, *, db: Session = Depends(get_db), embedding_in: EmbeddingUpdate) -> EmbeddingResponse:
    embedding = embedding_crud.get(db=db, id=embedding_id)
    if not embedding:
        logger.warning(f"Embedding with ID {embedding_id} not found for update.")
        raise HTTPException(status_code=404, detail="Embedding not found")
    updated_embedding = embedding_crud.update(db=db, db_obj=embedding, obj_in=embedding_in)
    logger.info(f"Updated Embedding with ID: {embedding_id}")
    return EmbeddingResponse(chunk_id=updated_embedding.id_uuid, chunk_text=updated_embedding.chunk_text, embedding=updated_embedding.embedding, source_type=updated_embedding.source_type, source_page=updated_embedding.source_page, created_at=updated_embedding.created_at)

@router.delete("/embeddings/{embedding_id}", response_model=EmbeddingResponse)
def delete_embedding(embedding_id: UUID, db: Session = Depends(get_db)) -> EmbeddingResponse:
    embedding = embedding_crud.get(db=db, id=embedding_id)
    if not embedding:
        logger.warning(f"Embedding with ID {embedding_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Embedding not found")
    deleted_embedding = embedding_crud.delete(db=db, id=embedding_id)
    logger.info(f"Deleted Embedding with ID: {embedding_id}")
    return EmbeddingResponse(chunk_id=deleted_embedding.id_uuid, chunk_text=deleted_embedding.chunk_text, embedding=deleted_embedding.embedding, source_type=deleted_embedding.source_type, source_page=deleted_embedding.source_page, created_at=deleted_embedding.created_at)