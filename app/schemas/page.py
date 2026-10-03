from pydantic import BaseModel,ConfigDict, Field
from datetime import datetime
from typing import Optional


class Page(BaseModel):
    id : str
    doc_id : str
    user_id :str
    page_number : int
    text_content : str
    word_count : int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def from_mong(cls, doc:dict) -> "Page":
        doc = dict(doc)
        
        if  "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
    
    
