from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class Outbox(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    job_id: str
    payload: dict[str, Any]              # JSON blob
    published: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def from_mongo(cls, doc: dict) -> "Outbox":
        doc = dict(doc)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)