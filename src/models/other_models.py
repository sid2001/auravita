from pydantic import BaseModel
from typing import Dict, List

class Notification(BaseModel):
    id: str
    data: str | Dict[str,str] | List[str] | None = None
