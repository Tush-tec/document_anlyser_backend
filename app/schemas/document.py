from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from slugify import slugify


class Document(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: Optional[str] = None           
    user_id: Optional[str] = None      
    filename: str          
    title: str | None =None       
    original_name: str                 
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
    slug : Optional[str] | None = None

    @classmethod
    def from_mongo(cls, doc: dict) -> "Document":
        doc = dict(doc)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
    
    
    
    @model_validator(mode="after")
    def generate_slug(self) -> "Document":
        if not self.slug and self.title:
            self.slug = slugify(self.title, algorithm="modern")
        return self
