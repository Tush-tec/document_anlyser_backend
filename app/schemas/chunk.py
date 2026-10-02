from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Chunk(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None            # str(ObjectId) — set from Mongo's _id
    document_id: str
    page: int
    char_start: int
    char_end: int
    text: str
    token_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def from_mongo(cls, doc: dict) -> "Chunk":
        doc = dict(doc)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)