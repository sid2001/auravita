from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Response, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Annotated
from db.connection import db,client
from bson import ObjectId
from models.resource import UploadFileRequest, File as FileModel
router = APIRouter()

@router.get("/userFiles")
async def get_file():
    try:
        file_collection = db["files"]
        owner_id = req.state.session["user_id"]
        files = {}
        try:
            files = file_collection.find({owner_id: owner_id})
        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(detail="Error in fetching files", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payload = []
        for file in files:
            data = {
                    fileId: str(file["_id"]), 
                    metadata: file["metadata"], 
                    data: file["data"],
                
                    }
            payload.append(data)
        return JSONResponse(content={"files": payload, "error": None}, status_code=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"files": None, "error": e.__str__()}, status_code=e.status_code if hasattr(e, "status_code") else status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/file/{file_id}")
async def get_file():
    user_id = req.state.session["user_id"]

@router.post("/uploadFile")
async def upload_file(req: Request,tags: list[str] = Form(...) , file: UploadFile = File(...)):
    file_data = {
                "file_name": file.filename,
                "content_type": file.content_type,
            }

    print(tags)
    print(req.headers)
    chunk = 0
    while content := await file.read(1024*1024):
        #print(f'chunk: {chunk}')
        chunk += 1
    print(f'file_data: {file_data}\n')

#@router.post("/createFileAccess/{file_id}")
#async def create_file_access(file_id:str, req:Request, p:str):
#    try:
#        user_id = req.state.session["user_id"]
#        access_id = ''
#        with client.start_session() as session:
#            access_id = session.with_transaction(lambda s: create_file_access_callback(s,file_id, user_id,peer_id))
#        return JSONResponse(content={"detail":"File access generated for 1hr","access_id":access_id},status_code = 200)
#    except Exception as e:
#        print(f"Error: {e}")
#        
#        return JSONResponse(content = {'detail': e.detail if hasattr(e,'detail') else "Internal server error"}, status_code = e.status_code if hasattr(e,'status_code') else 500)

@router.post("/tempFileShare/{file_id}")
async def temp_file_share(file_id:str, req:Request, p:str):
    try:
        user_id = req.state.session["user_id"]
        access_id = ''
        peer_id = p
        with client.start_session() as session:
            access_id = session.with_transaction(lambda s: temp_file_share_callback(s,file_id, user_id,peer_id))
        return JSONResponse(content={"detail":"File access generated for 30 minutes","access_id":access_id},status_code = 200)
    except Exception as e:
        print(f"Error: {e}")
        
        return JSONResponse(content = {'detail': e.detail if hasattr(e,'detail') else "Internal server error"}, status_code = e.status_code if hasattr(e,'status_code') else 500)

#@router.get("/viewFile/{file_id}")
#def view_file
