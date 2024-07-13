from hashlib import sha256
from bson import ObjectId

def generate_id(phone: str) -> str:
    phone = str(phone)
    return sha256(phone.encode('utf-8')).hexdigest()

def dict_user_for_db(self) -> dict:
    id : str = generate_id(self.phone.number)
    # implement this everywhere
    # id : ObjectId = ObjectId()
    return {
        "_id": self._id,
        "user_type": self.user_type,
        "phone": str(self.phone.full_number),
        "name": self.name,
        "verified": str(self.verified),
        "health_id": self.health_id,
        "created_at": self.created_at,
        "updated_at": self.updated_at,
    }

def user_session_serializer(data) -> dict:
    for key in data:
        if key == "_id" or key == "id":
            data.pop(key)
        data[key] = str(data[key])
    return data

def user_data_serializer(data) -> dict:
    if isinstance(data, dict):
        for key in data:
            data[key] = user_data_serializer(data[key])
        return data
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = user_data_serializer(data[i])
        return data
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, int):
        return str(data)
    else: 
        return data
