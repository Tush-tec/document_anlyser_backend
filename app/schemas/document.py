from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Document(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: Optional[str] = None           
    user_id: Optional[str] = None      
    filename: str                      
    original_name: str                 
    text_content: str                  
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    storage_key: Optional[str] = None
    status: str = "queued"
    page_count: Optional[int] = 0
    word_count: Optional[int] = 0
    token_count: Optional[int] = None
    sha256: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ready_at: Optional[datetime] = None

    @classmethod
    def from_mongo(cls, doc: dict) -> "Document":
        doc = dict(doc)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)