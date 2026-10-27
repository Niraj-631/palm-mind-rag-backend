
from typing import Literal

from pydantic import BaseModel, Field


class IngestionResponse(BaseModel):
    document_id: str
    filename: str
    strategy: Literal["fixed_size", "recursive"]
    character_count: int
    chunk_count: int
    status: str
    message: str


class IngestionOptions(BaseModel):
    strategy: Literal["fixed_size", "recursive"] = "recursive"
    chunk_size: int = Field(default=1000, ge=100, le=5000)
    chunk_overlap: int = Field(default=150, ge=0, le=1000)
