from db.connection import client, db
from bson import ObjectId

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
        raise Exception("Invalid details or file not found")
    
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
    
