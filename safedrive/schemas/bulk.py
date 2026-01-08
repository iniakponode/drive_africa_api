from typing import List

from pydantic import BaseModel, Field


class BulkOperationResult(BaseModel):
    total: int
    succeeded: int
    failed: int
    errors: List[str] = Field(default_factory=list)
