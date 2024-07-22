from db.connection import client, db, async_client, async_db
from bson import ObjectId
from models.resource import TemporarilySharedFile
from fastapi import HTTPException
from utils.resource import s3_object_key_generator
from services.aws_s3 import S3Client
from models.resource import File as FileModel, Metadata

def file_access_callback(
    session,
    file_id: str,
    owner_id: str,
    access_type: str,
    accessor_id: str,
):
    user_collection = db["users"]
    file_collection = db["files"]

    #doctor = user_collection.find_one({"_id": ObjectId(accessor_id)}) # doctor
    #patient = user_collection.find_one({"_id": ObjectId(owner_id)}) # patient
    file = file_collection.find_one({"_id": ObjectId(file_id)}) # file

    if not file:
        raise HTTPException(status_code="400",detail="Invalid details or file not found")
    
    # add file to doctor's shared_files
    filter_query = {
            "_id": ObjectId(accessor_id),
            f"patients.{owner_id}": {"$exists":True}
            }
    
    result = user_collection.find_one(filter_query,{"_id":1,f"patients.{owner_id}.shared_files":1},session=session);
    
    if(result is None or result == {}):
       raise HTTPException(status_code="400",detail="User does not exists or user is not connected")
    else:
        print("result: ",result)
        shared_files = result["patients"][owner_id]["shared_files"]
        exists = False
        for indx,file in enumerate(shared_files):
            if(file["file_id"]==file_id):
                exists = True
                shared_files[indx]["access_type"] = access_type
        if exists == False:
            data = {
                "access_type":access_type,
                "file_id": file_id
            }

            shared_files.append(data)
        update_query = {
            "$set": {
                f"patients.{owner_id}.shared_files": shared_files
            }
        }
        user_collection.update_one(filter_query,update_query,session=session)
    #update_query = {
    #        "$set": {
    #        f"patients.{owner_id}.shared_files.$[elem].access_type": access_type
    #            },
    #        "$addToSet":{
    #            f"patients.{owner_id}.shared_files" : {
    #                "file_id": ObjectId(file_id),
    #                "access_type": access_type
    #                }
    #            }
    #        }
    #array_filters = [{"elem.file_id": ObjectId(file_id)}]

    #result = user_collection.update_one(filter_query, update_query, array_filters=array_filters,session=session)

    #if result.modified_count == 0:
    #    raise Exception("Failed to update access")

    # add doctor id to file document
    #access_list = file.get("access_list", []) 
    #print("access list ", access_list)
    #access_list.append(accessor_id)
    #print("access list ",access_list)
    print("accessor_id: ",accessor_id)
    file_collection.update_one({"_id": ObjectId(file_id)}, {"$addToSet": {"access_list": accessor_id}}, session=session)
    
   # if result.modified_count == 0:
   #     raise Exception("Failed to update access")
    
    return


def revoke_file_access_callback(
    session,
    file_id: str,
    owner_id: str,
    accessor_id: str,
):
    user_collection = db["users"]
    file_collection = db["files"]

    # Fetch the file document
    file = file_collection.find_one({"_id": ObjectId(file_id)}, session=session)

    if not file:
        raise HTTPException(status_code=400, detail="Invalid details or file not found")

    # Define the filter query for the user
    filter_query = {
        "_id": ObjectId(accessor_id),
        f"patients.{owner_id}": {"$exists": True}
    }

    # Find the user document
    result = user_collection.find_one(filter_query, {"_id": 1, f"patients.{owner_id}.shared_files": 1}, session=session)

    if not result:
        raise HTTPException(status_code=400, detail="User does not exist or user is not connected")

    # Update the shared files array
    shared_files = result["patients"][owner_id]["shared_files"]
    updated_shared_files = [file for file in shared_files if file["file_id"] != file_id]

    # Update the user's document
    update_query = {
        "$set": {
            f"patients.{owner_id}.shared_files": updated_shared_files
        }
    }
    user_collection.update_one(filter_query, update_query, session=session)

    # Remove the accessor_id from the file document's access list
    file_collection.update_one({"_id": ObjectId(file_id)}, {"$pull": {"access_list": accessor_id}}, session=session)

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
    

async def upload_file_callback(
        session,
        file,
        file_data,
        user_id,
):

    file_collection = async_db["files"]

    file_name = file.filename.split(".")[0]
    owner_id = user_id;
    content_type =file.content_type;
    tags = file_data["tags"];
    file_type = file_data["report_type"];
    file_date = file_data["report_date"];
    ext = content_type.split("/")[-1]
    file_id = ObjectId()

    print(f"file_type:{ext} content_type:{content_type}")
    
    object_key = s3_object_key_generator(ext,user_id,file_type,str(file_id))

    file_object = FileModel(
        id=file_id,
        owner_id=ObjectId(owner_id),
        metadata=Metadata(
            object_key=object_key,
            file_name=file_name,
            tags=tags,
            ext=ext,
            file_type=file_type,
            date=file_date
        )
    )
    file_object = file_object.dict(by_alias=True)

    await file_collection.insert_one(file_object,session=session)
    
    s3 = S3Client()
    #file_content = await file.read()
    #print("file_conte")
    #print(f"type of file:{type(file)}")
    res = await s3.put_object(file,object_key)
    if res is not None:
       raise HTTPException(detail="Failed file upload",status_code=503)
        
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
    
