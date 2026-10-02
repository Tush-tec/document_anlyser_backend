from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Job(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    document_id: str
    type: str                            
    status: str = "queued"               
    progress: int = 0
    worker_id: Optional[str] = None
    lease_expires_at: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def from_mongo(cls, doc: dict) -> "Job":
        doc = dict(doc)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)