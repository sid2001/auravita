from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime as dt

class Metadata(BaseModel):
    object_key: str # Bucket object key
    file_name: str
    tags: list[str] = [] # Sugar, BP, etc.
    ext: str
    file_type:str # Report or Prescription

class File(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    owner_id: ObjectId
    metadata: Metadata
    access_list: list[str] = []
    data: dict = {}
    uploaded_at: dt = dt.utcnow()
    updated_at: str | None = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UploadFileRequest(BaseModel):
    file_name: str
    ext: str
    tags: list[str]

class TemporarilySharedFile(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    owner_id: ObjectId
    file_id: ObjectId
    access_type: str = "r"
    accessor_id: ObjectId
    created_at: str = dt.utcnow()
    presigned_url: str
    
    class Config():
        arbitrary_types_allowed = True
        populate_by_name = True


