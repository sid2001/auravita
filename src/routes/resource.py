from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Response, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from db.connection import db,client, async_client
from bson import ObjectId
from models.resource import UploadFileRequest, File as FileModel
from serializers.resource import user_files_serializer
from utils.resource import  s3_object_key_generator
from db.transactions.resource import upload_file_callback, file_access_callback, revoke_file_access_callback
from services.aws_s3 import S3Client
from enum import Enum
from services.notification import Notification_service as Notify
import traceback
router = APIRouter()

@router.get("/userFiles")
async def get_file(req:Request,q:int | None=Query(default=1)):
    try:
        print("query: ",q)
        file_collection = db["files"]
        owner_id = req.state.session["user_id"]
        print("owner_id: ",owner_id)    
        
        try:
            files = file_collection.find({"owner_id": ObjectId(owner_id)},{"_id":1,"metadata":1}).skip((int(q)-1)*10).limit(10)
        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(detail="Error in fetching files", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        files = list(files)
        print("files: ",files)
        files = user_files_serializer(files)
        payload = []
        for file in files:
            payload.append(file)
        return JSONResponse(content={"files": payload}, status_code=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error: {traceback.format_exception(type(e), e, e.__traceback__)}")
        return JSONResponse(content={"files": None, "error": e.__str__()}, status_code=e.status_code if hasattr(e, "status_code") else status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/file/{file_id}")
async def get_file():
    user_id = req.state.session["user_id"]

@router.post("/uploadFile")
async def upload_file(req: Request,tags: list[str] = Form(...) , file: UploadFile = File(...)):

    try:

        user_id = req.state.session["user_id"]
         
        file_data = {
                    "file_name": file.filename,
                    "content_type": file.content_type,
                }
        dummy_data = {
            "report_type": "doctor_prescription",
            "report_date": "2021-09-15",
            "tags": tags,
        }
        async with await async_client.start_session() as session:
            async with session.start_transaction():
                await upload_file_callback(session,file,dummy_data,user_id)        
        return JSONResponse(content={"detail":"File uploaded successfully"},status_code = 200)

        #chunk = 0
        #while content := await file.read(1024*1024):
        #    #print(f'chunk: {chunk}')
        #    chunk += 1
        #print(f'file_data: {file_data}\n')
    except Exception as e:
        tb_str = traceback.format_exception(type(e), e, e.__traceback__)
        print(f"Error: {''.join(tb_str)}")
        return JSONResponse(content = {'detail': e.detail if hasattr(e,'detail') else "Internal server error"}, status_code = e.status_code if hasattr(e,'status_code') else 500)

@router.post("/createFileAccess/{file_id}")
async def create_file_access(file_id:str, req:Request, p:str=Query(...),t:str = Query(default='r')):
    try:
        user_id = req.state.session["user_id"]
        user_name = req.state.session["name"]
        with client.start_session() as session:
            session.with_transaction(lambda s: file_access_callback(session=s,file_id=file_id,owner_id=user_id,access_type=t,accessor_id=p))
        
        notify_data = f"{user_name} gave you file access!"
        Notify.add_to_db(p,notify_data)
        Notify.add_notification(p,notify_data)

        return JSONResponse(content={"detail":"File access granted"},status_code = 200)
    except Exception as e:
        print(f"Error: {traceback.format_exception(type(e), e, e.__traceback__)}")
        
        return JSONResponse(content = {'detail': e.detail if hasattr(e,'detail') else "Internal server error"}, status_code = e.status_code if hasattr(e,'status_code') else 500)


@router.post("/revokeFileAccess/{file_id}")
def revoke_file_access(file_id:str, req:Request, p:str=Query(...)):
    try:
        user_id = req.state.session["user_id"]
        with client.start_session() as session:
            session.with_transaction(lambda s: revoke_file_access_callback(s,file_id,user_id,p))
        return JSONResponse(content={"detail":"File access revoked"},status_code=200)
    except Exception as e:
        print(f"Error: {e}")
        
        return JSONResponse(content = {'detail': e.detail if hasattr(e,'detail') else "Internal server error"}, status_code = e.status_code if hasattr(e,'status_code') else 500)



@router.post("/tempFileShare/{file_id}")
async def temp_file_share(file_id:str, req:Request, p:str):
    try:
        user_id = req.state.session["user_id"]
        user_name = req.state.session["name"]
        access_id = ''
        peer_id = p
        with client.start_session() as session:
            access_id = session.with_transaction(lambda s: temp_file_share_callback(s,file_id, user_id,peer_id))
        
        notify_data = f"{user_name} shared a file!"
        result = Notify.add_to_db(p,data)
        if(result not in None):
            Notify.add_notification(p,result)
        return JSONResponse(content={"detail":"File access generated for 30 minutes","access_id":access_id},status_code = 200)
    except Exception as e:
        print(f"Error: {e}")
        
        return JSONResponse(content = {'detail': e.detail if hasattr(e,'detail') else "Internal server error"}, status_code = e.status_code if hasattr(e,'status_code') else 500)

@router.get("/fileURL/{file_id}")
def get_file_url(req: Request,file_id:str,o:Enum(value='validator',names={'t':'1','f':'0'}) = Query(...)):
    try:
        print("o: ",o.value)
        if o.value=='1':
            #get file url for owner
            user_id = req.state.session['user_id']
            file_collection = db['files']
            file_data = file_collection.find_one({"_id":ObjectId(file_id),"owner_id":ObjectId(user_id)},{"metadata.object_key":1})
            print("file_data: ",file_data)
            if file_data:
                object_key = file_data["metadata"]["object_key"]
                print("object key: ",object_key)
                s3 = S3Client()
                file_url = s3.generate_presigned_url(object_key,'get_object',120)
                return JSONResponse(content={"url":file_url,"detail":'File access granted for 2 minutes'},status_code=200)
            else:
                raise HTTPException(detail='File not found',status_code=404)
        else:
            #get file url for other user
            user_id = req.state.session["user_id"]
            file_collection = db['files']
            file_data = file_collection.find_one({"_id":ObjectId(file_id),"access_list":user_id},{"metadata.object_key":1})
            if file_data:
                object_key = file_data["metadata"]["object_key"]
                s3 = S3Client()
                file_url = s3.generate_presigned_url(object_key,'get_object',120)
                return JSONResponse(content={"url":file_url,"detail":'File access granted for 2 minutes'},status_code=200)
            else:
                raise HTTPException(detail='File not found',status_code=404)
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content = {'detail': e.detail if hasattr(e,'detail') else "Internal server error"}, status_code = e.status_code if hasattr(e,'status_code') else status.HTTP_500_INTERNAL_SERVER_ERROR)



