from db.connection import client, db
from bson import ObjectId
from models.resource import TemporarilySharedFile
from fastapi import HTTPException
from services.s3 import S3Client

def file_access_callback(
    session,
    file_id: str,
    owner_id: str,
    access_type: str,
    accessor_id: str,
):
    user_collection = db["users"]
    file_collection = db["files"]

    doctor = user_collection.find_one({"_id": ObjectId(accessor_id)}) # doctor
    #patient = user_collection.find_one({"_id": ObjectId(owner_id)}) # patient
    file = file_collection.find_one({"_id": ObjectId(file_id)}) # file

    if not doctor or not patient or not file:
        raise HTTPException(status_code="400",detail="Invalid details or file not found")
    
    # add file to doctor's shared_files
    filter_query = {
            "_id": ObjectId(accessor_id),
            f"patients.{owner_id}.shared_files.file_id": ObjectId(file_id)
            }
    update_query = {
            "$set": {
                    f"patients.{owner_id}.shared_files.$[elem].access_type": access_type
                },
            "$addToSet":{
                f"patients.{owner_id}.shared_files" : {
                    "file_id": ObjectId(file_id),
                    "access_type": access_type
                    }
                }
            }
    array_filters = [{"elem.file_id": ObjectId(file_id)}]

    result = user_collection.update_one(filter_query, update_query, array_filters=array_filters,session=session)

    if result.modified_count == 0:
        raise Exception("Failed to update access")

    # add doctor id to file document
    access_list = file.get("access_list", []) 
    access_list.append(accessor_id)

    result = file_collection.update_one({"_id": ObjectId(file_id)}, {"$set": {"access_list": access_list}}, session=session)
    
    if result.modified_count == 0:
        raise Exception("Failed to update access")
    
    return

def revoke_file_access_callback(
    session,
    file_id: str,
    owner_id: str,
    accessor_id: str,
):
    user_collection = db["users"]
    file_collection = db["files"]

    doctor = user_collection.find_one({"_id": ObjectId(accessor_id)}) # doctor
    #patient = user_collection.find_one({"_id": ObjectId(owner_id)}) # patient
    file = file_collection.find_one({"_id": ObjectId(file_id)}) # file

    if not doctor or not patient or not file:
        raise Exception("Invalid details or file not found")
    
    # remove file from doctor's shared_files
    filter_query = {
            "_id": ObjectId(accessor_id),
            f"patients.{owner_id}.shared_files.file_id": ObjectId(file_id)
            }
    update_query = {
            "$pull":{
                f"patients.{owner_id}.shared_files" : {
                    "file_id": ObjectId(file_id)
                    }
                }
            }
    array_filters = [{"elem.file_id": ObjectId(file_id)}]

    result = user_collection.update_one(filter_query, update_query, array_filters=array_filters,session=session)

    if result.modified_count == 0:
        raise Exception("Failed to update access")

    # remove doctor id from file document
    access_list = file.get("access_list", []) 
    access_list.remove(accessor_id)

    result = file_collection.update_one({"_id": ObjectId(file_id)}, {"$set": {"access_list": access_list}}, session=session)
    
    if result.modified_count == 0:
        raise Exception("Failed to update access")
    
    return

def temp_file_share_callback(session,file_id,owner_id,accessor_id,access_type="r"):
    
    user_collection = db["users"]
    file_collection = db["files"]
    temporarily_shared_files_collection = db["temporarily_shared_files"]

    accessor = user_collection.find_one({"_id": ObjectId(accessor_id)},{"_id":1})
    if not accessor:
        raise HTTPException(status_code=404,detail="Recepient user not found")
    
    file = file_collection.find_one({"_id": ObjectId(file_id),owner_id:ObjectId(owner_id)},{"metadata":1})
    if not file:
        raise HTTPException(status_code=404,detail="File not found")
    
    existing_access = temporarily_shared_files_collection.find_one({"file_id": ObjectId(file_id),"accessor_id": ObjectId(accessor_id)},{"_id":1})
    if existing_access:
        raise HTTPException(status_code=400,detail="File already shared")
    
    s3_client = S3Client()
    url_params = {
            "object_key":file.metadata.object_key,
            "client_method":"get_object",
            "expiration": 1800 #add to constants later
            }

    [presigned_url,err] = s3_client.generate_presigned_url(**url_params)
    
    if err is not None:
        raise HTTPException(status_code=500,detail=err)

    temporary_shared_file = TemporarilySharedFile(
            owner_id = ObjectId(owner_id),
            file_id = ObjectId(file_id),
            access_type = access_type,
            accessor_id = accessor_id,
            presigned_url = presigned_url
            )
    temporary_shared_file = temporary_shared_file.dict(by_alias=True)
    result = temporarily_shared_files_collection.insert_one(temporary_shared_file,session=session)
    
    if not result:
        raise HTTPException(status_code=500,detail="Internal server error")
    
    return
    


def file_access_callback_wrapper(s,file_id,owner_id,access_type,accessor_id ):
    file_access_callback(
            s,
            file_id,
            owner_id,
            access_type,
            accessor_id
            )
    return

def revoke_file_access_callback_wrapper(s,file_id,owner_id,accessor_id ):
    revoke_file_access_callback(
            s,
            file_id,
            owner_id,
            accessor_id
            )
    return
    
