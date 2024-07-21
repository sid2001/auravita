from pydantic import BaseModel, Field
from datetime import datetime as dt
from bson import ObjectId

class PhoneNumber(BaseModel):
    country_code: int 
    number: str = Field(..., min_length=10, max_length=10, pattern="^[0-9]*$")

    @property
    def full_number(self):
        return f"+{self.country_code}{self.number}"

class Metadata(BaseModel):
    files: list[str] = []   
class User(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    phone: PhoneNumber
    name: str
    user_type: str
    verified: bool = False # default value
    health_id: str | None = None
    created_at: str = str(dt.now().isoformat())
    updated_at: str | None = None
    metadata : Metadata | None = None 
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        #json_encoders = {ObjectId: str}

class SharedFiles(BaseModel):
    file_id: str
    access_type: str

class PatientsData(BaseModel):
    shared_files: list[SharedFiles]

class Doctor(User):
    specialization: str | None = None
    experience: int | None = None
    qualification: str | None = None
    registration_number: str | None = None
    patients: dict[str, PatientsData] = {}
    connection_requests: list[str] = []

class Patient(User):
    files: list[str] = []
    connected_doctors: list[str] = []
    pending_requests: list[str] = []

