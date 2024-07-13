from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime as dt

class Metadata(BaseModel):
    object_key: str
    file_name: str
    tags: list[str]
    ext: str

class File(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    owner_id: str
    metadata: Metadata
    access_list: list[str]
    data: dict
    uploaded_at: dt = dt.utcnow()
    updated_at: str | None = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UploadFileRequest(BaseModel):
    file_name: str
    ext: str
    tags: list[str]

