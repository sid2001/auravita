from db.connection import db
from bson import ObjectId
from fastapi import HTTPException

def connection_request_callback(
    session,
    doctor_id: str,
    patient_detail,
    additional_note: str = None
):
    user_collection = db["users"]
    connection_request_collection = db["connection_requests"]
    
    """
       ???? check if individual call to db just to check if doctor and patient exists is necessary????
    """
    doctor = user_collection.find_one({"_id": ObjectId(doctor_id),"user_type":"doctor"},{"name":1}) # doctor
    
    connection_request = db.connection_requests.find_one({"doctor_id": ObjectId(doctor_id), "patient_id": ObjectId(patient_detail["user_id"])})
    if connection_request:
        raise HTTPException(status_code=400, detail="Connection request already sent")


    if not doctor :
        raise HTTPException(status_code=404, detail="Invalid details or user not found")
    
    ################
    # connection request model
    ################
    connection_request = {
        "doctor_id": ObjectId(doctor_id),
        "patient_id": ObjectId(patient_detail["user_id"]),
        "status": "pending",
        "metadata": {
            "patient_name": patient_detail["name"],
            "doctor_name": doctor["name"],
            "additional_note": additional_note
        } 
    }
    
    result = connection_request_collection.insert_one(connection_request, session=session)
    
    update_query_patient = {
            "$inc":{
                    "pending_connection_requests": 1
                }
            }

    update_query_doctor = {
            "$inc":{
                    "connection_requests": 1   
                }
            }

    user_collection.update_one({"_id": ObjectId(doctor_id)}, update_query_doctor, session=session)
    
    user_collection.update_one({"_id": ObjectId(patient_detail["user_id"])}, update_query_patient, session=session)
    
    return

def accept_connection_request_callback(
    session,
    connection_request_id: str,
    doctor_id: str,
):
    user_collection = db["users"]
    connection_request_collection = db["connection_requests"]
    
    connection_request = connection_request_collection.find_one({"_id": ObjectId(connection_request_id), "doctor_id": ObjectId(doctor_id)})
    
    if not connection_request:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    patient_id = str(connection_request["patient_id"]) 
    
    if connection_request["status"] == "accepted":
        raise HTTPException(status_code=400, detail="Connection request already accepted")
    
    
    update_query_patient = {
            "$set":{
                f"doctors.{doctor_id}": {
                "shared_files":[],
                "other_data": {}
            }
                },
            "$inc":{
                    "doctors_count": 1,
                    "pending_connection_requests": -1
                }
            }

    update_query_doctor = {
            "$set":{
                f"patients.{patient_id}": {
                "shared_files":[],
                "other_data":{}
            }
                },
            "$inc":{
                    "patients_count": 1,
                    "connection_requests": -1
                }
            }

    user_collection.update_one({"_id": ObjectId(doctor_id)}, update_query_doctor, session=session)
    
    user_collection.update_one({"_id": ObjectId(patient_id)}, update_query_patient, session=session)
    
    connection_request_collection.delete_one({"_id": ObjectId(connection_request_id)}, session=session)
    return

def reject_connection_request_callback(session, connection_request_id: str):
    user_collection = db["users"]
    connection_request_collection = db["connection_requests"]
    
    connection_request = connection_request_collection.find_one({"_id": ObjectId(connection_request_id)})
    doctor_id = str(connection_request["doctor_id"]) #type = ObjectId
    patient_id = str(connection_request["patient_id"]) #type = ObjectId

    if not connection_request:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    if connection_request["status"] == "rejected":
        raise HTTPException(status_code=400, detail="Connection request already rejected")
    
    update_query_patient = {
            "$inc":{
                    "pending_connection_requests": -1
                }
            }

    update_query_doctor = {
            "$inc":{
                    "connection_requests": -1
                }
            }

    user_collection.update_one({"_id": ObjectId(doctor_id)}, update_query_doctor, session=session)
    
    user_collection.update_one({"_id": ObjectId(patient_id)}, update_query_patient, session=session)
    
    connection_request_collection.delete_one({"_id":ObjectId(connection_request_id)})
    
    return

def delete_pending_request(session,request_id):
    reject_connection_request_callback(session,request_id)
    return

def delete_connection_callback(
        session,
        patient_id: str,
        doctor_id: str
    ):
    user_collection = db["users"]
    patient_query = {
            "$unset": {
                f"doctors.{doctor_id}":""
                },
            "$inc": {
                "doctors_count": -1
                }
            } 
    doctor_query = {
            "$unset": {
                f"patients.{patient_id}":""
                },
            "$inc": {
                "patients_count": -1
                }
            }

    result = user_collection.find_one_and_update({"_id": ObjectId(patient_id),f"doctors.{doctor_id}":{"$exists":"true"}}, patient_query, session=session)
    user_collection.find_one_and_update({"_id": ObjectId(doctor_id),f"patients.{patient_id}":{"$exists":"true"}}, doctor_query, session=session)

    return

#def connection_request_callback_wrapper(session, doctor_id: str, patient_id: str):
#    connection_request_callback(session, doctor_id, patient_id)
#    return return
