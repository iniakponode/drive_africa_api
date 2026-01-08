from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from safedrive.models.embedding import Embedding, generate_uuid_binary
from safedrive.schemas.embedding import EmbeddingCreate, EmbeddingUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDEmbedding:
    def __init__(self, model):
        self.model = model

    def create(self, db: Session, obj_in: EmbeddingCreate) -> Embedding:
        db_obj = self.model(**obj_in.dict(), chunk_id=generate_uuid_binary())
        db.add(db_obj)
        try:
            db.commit()
            logger.info(f"Created Embedding with ID: {db_obj.chunk_id.hex()}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating Embedding: {str(e)}")
            raise e
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: UUID) -> Optional[Embedding]:
        embedding = db.query(self.model).filter(self.model.chunk_id == id.bytes).first()
        if embedding:
            logger.info(f"Retrieved Embedding with ID: {id}")
        else:
            logger.warning(f"Embedding with ID {id} not found.")
        return embedding

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Embedding]:
        embeddings = db.query(self.model).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(embeddings)} Embeddings.")
        return embeddings

    def update(self, db: Session, db_obj: Embedding, obj_in: EmbeddingUpdate) -> Embedding:
        obj_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        db.add(db_obj)
        try:
            db.commit()
            logger.info(f"Updated Embedding with ID: {db_obj.chunk_id.hex()}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating Embedding: {str(e)}")
            raise e
        db.refresh(db_obj)
        return db_obj

    def batch_create(self, db: Session, objs_in: List[EmbeddingCreate]) -> List[Embedding]:
        db_objs = []
        for obj_in in objs_in:
            db_obj = self.model(**obj_in.dict(), chunk_id=generate_uuid_binary())
            db.add(db_obj)
            db_objs.append(db_obj)
        try:
            db.commit()
            logger.info("Batch created %s Embedding records.", len(db_objs))
        except Exception as e:
            db.rollback()
            logger.error(f"Error batch creating Embeddings: {str(e)}")
            raise e
        for db_obj in db_objs:
            db.refresh(db_obj)
        return db_objs

    def delete(self, db: Session, id: UUID) -> Optional[Embedding]:
        obj = db.query(self.model).filter(self.model.chunk_id == id.bytes).first()
        if obj:
            db.delete(obj)
            try:
                db.commit()
                logger.info(f"Deleted Embedding with ID: {id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error deleting Embedding: {str(e)}")
                raise e
        else:
            logger.warning(f"Embedding with ID {id} not found for deletion.")
        return obj

    def batch_delete(self, db: Session, ids: List[UUID]) -> int:
        try:
            id_bytes = [item.bytes for item in ids]
            deleted = (
                db.query(self.model)
                .filter(self.model.chunk_id.in_(id_bytes))
                .delete(synchronize_session=False)
            )
            db.commit()
            logger.info("Batch deleted %s Embedding records.", deleted)
            return deleted
        except Exception as e:
            db.rollback()
            logger.error(f"Error batch deleting Embeddings: {str(e)}")
            raise e

embedding_crud = CRUDEmbedding(Embedding)
