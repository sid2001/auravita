from fastapi import APIRouter, Depends, status, Response, Request, Body, HTTPException
from fastapi.responses import JSONResponse
from serializers.user import user_session_serializer, user_data_serializer
from serializers.resource import response_serializer
from db.connection import db, client
from db.transactions.user import  connection_request_callback, accept_connection_request_callback, reject_connection_request_callback, delete_connection_callback 
from bson import ObjectId
from typing import Optional, Annotated
import traceback

router = APIRouter()

@router.get("/sessionDetail")
def get_session_details(request: Request):
    session_data = request.state.session
    session_data = user_session_serializer(session_data)
    print(f"Session data: {session_data}\n")
    
    return JSONResponse(content=session_data)

#@router.post("/updateProfile")
#def update_profile(request: Request, data: dict = Body(...)):
#    print(f"Data: {data}")
#    return JSONResponse(content={"error": None}, status_code=200)

@router.post("/deleteProfile")
def delete_profile(req:Request):
    try:
        user_id = req.state.session["user_id"]
        user_collection = db["users"]
        with client.start_session() as session:
            with session.start_transaction():
                user_collection.delete_one({"_id": ObjectId(user_id)},session=session)
                db["delete_users"].insert_one({"_id":ObjectId(user_id)},session=session)
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"detail": "Internal Server Error"}, status_code=500)

@router.post("/connectionRequest/{doctor_id}")
def send_connection_request(doctor_id: str,request:Request, additional_note: Annotated[str | None,Body(max_length=200)]=None, null: str = Body(None)):
    try:
        if(request.state.session["user_type"] != "patient"):
            raise HTTPException(detail = "Invalid request", status_code=400)
        with client.start_session() as session:
            patient_detail = request.state.session
            session.with_transaction(lambda s: connection_request_callback(s, doctor_id, patient_detail, additional_note))
        return JSONResponse(content={"detail": "Connection request sent"}, status_code=200)
    except Exception as e:
        print(f"Error: {e}")
        default_status_code = 500
        default_error_detail = "Internal Server Error"

        return JSONResponse(content = {'detail': e.detail if hasattr(e, 'detail') else default_error_detail}, status_code = e.status_code if hasattr(e, 'status_code') else default_status_code)


@router.post("/acceptConnectionRequest/{request_id}")
def accept_connection_request(request_id: str,request:Request):
    try:
        # check if the user is a doctor
        if request.state.session["user_type"] != "doctor":
            raise HTTPException(detail = "Invalid request", status_code=400)

        with client.start_session() as session:
            doctor_id = request.state.session["user_id"]
            session.with_transaction(lambda s: accept_connection_request_callback(s, request_id,doctor_id))
        return JSONResponse(content={"detail": "Connection request accepted"}, status_code=200)
    except Exception as e:
        print(f"Error: {e}")
        default_status_code = 500
        default_error_detail = "Internal Server Error"

        return JSONResponse(content = {'detail': e.detail if hasattr(e, 'detail') else default_error_detail}, status_code = e.status_code if hasattr(e, 'status_code') else default_status_code)

@router.post("/rejectConnectionRequest/{request_id}")
def reject_connection_request(request_id: str, request:Request):
    try:
        # check if the user is a doctor
        if request.state.session["user_type"] != "doctor":
            raise HTTPException(detail = "Invalid request", status_code=400)

        with client.start_session() as session:
            doctor_id = request.state.session["user_id"]
            session.with_transaction(lambda s: reject_connection_request_callback(s, request_id))
        return JSONResponse(content={"detail": "Connection request rejected"}, status_code=200)
    except Exception as e:
        print(f"Error: {e}")
        default_status_code = 500
        default_error_detail = "Internal Server Error"

        return JSONResponse(content = {'detail': e.detail if hasattr(e, 'detail') else default_error_detail}, status_code = e.status_code if hasattr(e, 'status_code') else default_status_code)



#@router.get("/getDoctorDetails/{doctor_id}")
@router.get("/getConnectionRequests")
def get_connection_requests(req:Request):
    try:
        user_id = req.state.session["user_id"]
        user_type = req.state.session["user_type"]
        if(user_type=="doctor"):
            connection_requests = db["connection_requests"].find({"doctor_id": ObjectId(user_id)},{"_id":1,"metadata.patient_name":1,"patient_id":1,"metadata.additional_note":1})
            connection_requests = list(connection_requests)
            connection_requests = response_serializer(connection_requests)
            return JSONResponse(content={"connection_requests": connection_requests}, status_code=200)
        elif(user_type=="patient"):
            connection_requests = db["connection_requests"].find({"patient_id": ObjectId(user_id)},{"_id:":1,"metadata.doctor_name":1,"doctor_id":1,"metadata.additional_note":1})
            connection_requests = list(connection_requests)
            connection_requests = response_serializer(connection_requests)
            return JSONResponse(content={"connection_requests": connection_requests}, status_code=200)
        else:
            raise HTTPException(detail="Invalid request", status_code=400)
    except Exception as e:
        print(f"Error: {e}")
        default_status_code = 500
        default_error_detail = "Internal Server Error"
        return JSONResponse(content = {'detail': e.detail if hasattr(e, 'detail') else default_error_detail}, status_code = e.status_code if hasattr(e, 'status_code') else default_status_code)


@router.post("/deletePendingRequest/{request_id}")
def delete_pending_request(request_id: str,req:Request):
    try:
        user_id = req.state.session["user_id"]
        user_type = req.state.session["user_type"]
        if user_type != "patient":
            raise HTTPException(detail="Invalid request", status_code=400)
        else:
            with client.start_session() as session:
                session.with_transaction(lambda s: reject_connection_request_callback(s, request_id))
        return JSONResponse(content={"detail": "Request deleted"}, status_code=200)
    except Exception as e:
        print(f"Error: {e}")
        default_status_code = 500
        default_error_detail = "Internal Server Error"
        return JSONResponse(content = {'detail': e.detail if hasattr(e, 'detail') else default_error_detail}, status_code = e.status_code if hasattr(e, 'status_code') else default_status_code)

@router.post("/deleteConnection/{peer_id}")
def delete_connection(peer_id: str,request:Request):
    try:
        user_type = request.state.session["user_type"]
        user_id = request.state.session["user_id"]
        with client.start_session() as session:
            if user_type == "patient":
                session.with_transaction(lambda s: delete_connection_callback(s, user_id, peer_id))
            elif user_type == "doctor":
                session.with_transaction(lambda s: delete_connection_callback(s, peer_id, user_id))
        return JSONResponse(content={"detail": "Connection deleted"}, status_code=200)
    except Exception as e:
        print(f"Error: {e}")
        default_status_code = 500
        default_error_detail = "Internal Server Error"

        return JSONResponse(content = {'detail': e.detail if hasattr(e, 'detail') else default_error_detail}, status_code = e.status_code if hasattr(e, 'status_code') else default_status_code)




@router.get("/searchDoctorByName/{doctor_name}")
def search_doctor_by_name(doctor_name: str,request: Request, p : int = 1 ):
    try:
        page = p;
        user_collection = db["users"]
        user_type = request.state.session["user_type"]
        #user_type = "patient"
        print("doctor_name: ",doctor_name) 
        if user_type != "patient":
            raise HTTPException(detail = "Only patients can search for doctors", status_code=400)
    
        #paginate the results by 10
        query = {"user_type": "doctor","name": {"$regex": f"{doctor_name}", "$options": "i"}}
        fields = {"_id":1,"name":1,"phone":1}

        doctors = user_collection.find(query, fields).skip((page-1)*10).limit(10)
        #print(f"doctors: {doctors}")
        doctors = list(doctors)
        doctors = user_data_serializer(doctors)
        #doctor_list = []
        #print(f"doctors: {doctors}")
        #for doctor in doctors:
        #    doctor["_id"] = str(doctor["_id"])
        #    doctor_list.append(doctor)

        return JSONResponse(content={"doctors":doctors},status_code=200)
    except Exception as e:
        print(f"Error: {e}")
        default_status_code = 500
        default_error_detail = "Internal Server Error"

        return JSONResponse(content = {'detail': e.detail if hasattr(e, 'detail') else default_error_detail}, status_code = e.status_code if hasattr(e, 'status_code') else default_status_code)


@router.get("/searchDoctorByNumber/{doctor_number}")
def search_doctor_by_number(doctor_number: int,request: Request, p : int = 1):
    try:
        user_collection = db["users"]
        user_type = request.state.session["user_type"]
        if user_type != "patient":
            raise HTTPException(detail = "Only patients can search for doctors", status_code=400)
    
        query = {"user_type": "doctor","phone.number": {"$regex": f"{doctor_number}", "$options": "i"}}
        fields = {"_id":1,"name":1,"phone":1}

        doctors = user_collection.find(query, fields).skip((p-1)*10).limit(10)
        print(f"doctors: {doctors}")
        doctors = list(doctors)
        doctors = user_data_serializer(doctors)
        #doctor_list = []
        #print(f"doctors: {doctors}")
        #for doctor in doctors:
        #    doctor["_id"] = str(doctor["_id"])
        #    doctor_list.append(doctor)

        return JSONResponse(content={"doctors":doctors},status_code=200)
    except Exception as e:
        print(f"Error: {e}")
        default_status_code = 500
        default_error_detail = "Internal Server Error"

        return JSONResponse(content = {'detail': e.detail if hasattr(e, 'detail') else default_error_detail}, status_code = e.status_code if hasattr(e, 'status_code') else default_status_code)
