from fastapi import APIRouter, Depends, status, Response, Request, Body
from fastapi.responses import JSONResponse
from models.auth import SignUpRequest, SignInRequest, SignInResponse, SignUpResponse,ResponseModel, OtpVerificationRequest, ResendOtpRequest
from db.connection import db
from services.messaging import send_message
import random
from datetime import datetime
from models.user import User, PhoneNumber
from typing import Annotated
from bson import ObjectId
from middlewares.sessionHandler import default_cookie_config
from serializers.user import dict_user_for_db , user_data_serializer
from utils.crypto import hash as hash_otp, encrypt, decrypt

otp_transactions_collection = db["otp_transactions"]

router = APIRouter()

@router.post("/signin/verify/{transaction_id}")
def verify_signin(transaction_id: str,data: Annotated[OtpVerificationRequest, Body()]  , request: Request, response: Response):
    try:
        otp_transactions_collection = db["otp_transactions"]
        otp = data.otp
        hashed_otp = hash_otp(otp) 
        transaction = otp_transactions_collection.find_one({"_id": ObjectId(transaction_id)})
        if not transaction:
            #content = ResponseModel(status="failed", message="Otp expired or invalid login attempt")
            return JSONResponse(content = {"detail":"OTP expired or invalid login attempt","status":"failed"}, status_code=status.HTTP_410_GONE)
        else:
            phone = transaction["phone"]
            if phone != f"+{data.country_code}{data.phone}":
                return JSONResponse(content={"detail":"Invalid Request"},status_code=status.HTTP_400_BAD_REQUEST)
            stored_hashed_otp = transaction["otp"]
            if hashed_otp == stored_hashed_otp:
                phone = f"+{data.country_code}{data.phone}"
                otp_transactions_collection.delete_one({"_id": ObjectId(transaction_id)})
                users_collection = db["users"]
                user = users_collection.find_one({"phone": {"country_code": data.country_code, "number": data.phone}})
                if not user:
                    #content = ResponseModel(status="failed", message="User not found")
                    return JSONResponse(content = {"detail":"User not found","status":"failed"}  , status_code=status.HTTP_404_NOT_FOUND)
                
                session_data = {
                    "phone": phone,
                    "verified": "True",
                    "isLoggedIn": "True",
                    "user_type": user["user_type"],
                    "name": user["name"],
                    "user_id": str(user["_id"]),
                }
                user_data = user_data_serializer(user) 
                print("userdata:",user)
                request.state.session = session_data
                #content = ResponseModel(status="success", message="signin successful", user_data = user_data})
                return JSONResponse(content={"detail": "Signin successful","user_data":user_data}, status_code=200)
            else:
                #content = ResponseModel(status="failed", message="Wrong OTP")
                return JSONResponse(content = {"status":"failed","detail":"Wrong OTP"},status_code=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        print(f"Error: {e}")
        #content = ResponseModel(status="failed", message="An error occured")
        return JSONResponse(content = {"detail":"Internal sever error","status":"failed"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/signin")
async def login(credentials: SignInRequest, response : Response, request: Request):
    try:
        users_collection = db["users"]
        full_number = f"+{credentials.country_code}{credentials.phone}"
        user = users_collection.find_one({"phone": {"country_code": credentials.country_code, "number": str(credentials.phone)}})


        if user:
            match user["verified"]:
                case "False":
                    content = ResponseModel(status="error", message="User not verified")
                    response = JSONResponse(content=content.json())
                    response.status_code = status.HTTP_401_UNAUTHORIZED
                    return response
                case "True":
                    #otp = str(random.randint(100000, 999999))
                    otp = "1234"
                    message = f"Your OTP is {otp}. Valid for 5 minutes"
                    hashed_otp = hash_otp(otp)
                    # await send_message(full_number, message)
                    # expire otp after 5 minutes
                    # add created_at field to track when the otp was created in utc time
                    transaction_id =  otp_transactions_collection.insert_one({"phone": full_number, "otp": hashed_otp,"createdAt": datetime.utcnow()}).inserted_id
                    print(f"OTP sent to user with transaction id: {transaction_id} otp: {otp}  ")
                    
                    #content = ResponseModel(status="success", message="OTP sent to user",data={"transaction_id": str(transaction_id)})
                    response = JSONResponse(content={"status":"success" ,"detail":"OTP sent to user","transaction_id":str(transaction_id)})
                    response.status_code = status.HTTP_200_OK
                    return response
        else:
            #content = ResponseModel(status="error", message="User not found")
            response = JSONResponse(content={"status":"failed","detail":"User not found"})
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
    except Exception as e:
        print(f"Error: {e}")
        #content = ResponseModel(status="failed", message="An error occured")
        return JSONResponse(content = {"status":"failed","detail":"Internal server error"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/signup")
def signup(data: Annotated[SignUpRequest, Body()], response: Response):
    try:
        users_collection = db["users"]
        full_number = f"+{data.country_code}{data.phone}"
        user = users_collection.find_one({"phone": {"country_code": data.country_code, "number": data.phone}})
        if user:
            #content = ResponseModel(status="error", message="User already exists")
            response = JSONResponse(content = {"status":"failed","detail":"User already exists"},status_code=status.HTTP_409_CONFLICT)
            return response
        else:
            phone_number = PhoneNumber(country_code=data.country_code, number=data.phone)
            user_data = User(phone=phone_number, name=data.name, user_type = data.user_type)
            #user_dict = dict_user_for_db(user_data)
            user_dict = user_data.dict(by_alias=True)
            users_collection.insert_one(user_dict)
            print(f"User created successfully {user_data.dict()}")
            #otp = str(random.randint(100000, 999999)) #for testing otp=1234
            otp = "1234"
            message = f"Your OTP is {otp}. Valid for 5 minutes"
            hashed_otp = hash_otp(otp)
            # await send_message(full_number, message)
            transaction_id =  otp_transactions_collection.insert_one({"phone": full_number, "otp": hashed_otp,"createdAt": datetime.utcnow()}).inserted_id
            print(f"OTP sent to user with transaction id: {transaction_id} otp: {otp}")
            
            #content = ResponseModel(status="success", message="OTP sent to user",data={"transaction_id": str(transaction_id)})
            #response.status_code = status.HTTP_200_OK
            return JSONResponse(content={"status":"success","detail":"OTP sent to user","transaction_id":str(transaction_id)})
    except Exception as e:
        print(f"Error: {e}")
        #content = ResponseModel(status="failed", message="An error occured")
        return JSONResponse(content = {"status":"failed","detail":"Internal server error"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/signup/verify/{transaction_id}")
def verify_signup(transaction_id: str,data: Annotated[OtpVerificationRequest, Body()]  , request: Request, response: Response):
    try:
        otp_transactions_collection = db["otp_transactions"]
        otp = data.otp
        hashed_otp = hash_otp(otp) 
        transaction = otp_transactions_collection.find_one({"_id": ObjectId(transaction_id)})
        if not transaction:
            #content = ResponseModel(status="failed", message="Otp expired or invalid login attempt")
            return JSONResponse(content = {"status":"failed","detail":"OTP expired or invalid login attempt"}, status_code=status.HTTP_410_GONE)
        else:
            stored_hashed_otp = transaction["otp"]
            if hashed_otp == stored_hashed_otp:
                #phone = f"+{data.country_code}{data.phone}"
                users_collection = db["users"]
                result =  users_collection.update_one({"phone": {"country_code":data.country_code,"number":data.phone}}, {"$set": {"verified": "True"}})
                
                if result.modified_count == 0:
                    #content = ResponseModel(status="error", message="User not found")
                    return JSONResponse(content = {"status":"failed","detail":"User not found"}, status_code=status.HTTP_404_NOT_FOUND)

                otp_transactions_collection.delete_one({"_id": ObjectId(transaction_id)})
                #content = ResponseModel(status="success", message="signup successful")
                return JSONResponse(content={"status":"success","detail":"Signup successful"}, status_code=200)
            else:
                #content = ResponseModel(status="failed", message="Wrong OTP")
                return JSONResponse(content = {"status":"failed","detail":"Invalid OTP"},status_code=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        print(f"Error: {e}")
        #content = ResponseModel(status="failed", message="An error occured")
        return JSONResponse(content = {"status":"failed","detail":"Internal server error"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/signin/resendotp")
def resend_otp(data: Annotated[ResendOtpRequest, Body()], response: Response):
    try:
        users_collection = db["users"]
        phone_number = f"+{data.country_code}{data.phone}"
        user = users_collection.find_one({"phone": {"country_code": data.country_code, "number": data.phone}})

        if user:
            if user["verified"] == "False":
                #content = ResponseModel(status="error", message="User not verified")
                return JSONResponse(content={"status":"failed","detail":"User not verified"}, status_code=status.HTTP_401_UNAUTHORIZED)
            else:
                otp = str(random.randint(100000, 999999))
                message = f"Your OTP is {otp}. Valid for 5 minutes"
                hashed_otp = hash_otp(otp)
                # await send_message(phone_number, message)
                transaction_id =  otp_transactions_collection.insert_one({"phone": phone_number, "otp": hashed_otp,"createdAt": datetime.utcnow()}).inserted_id
                print(f"OTP sent to user with transaction id: {trasaction_id} otp: {otp}")
                
                content = ResponseModel(status="success", message="OTP sent to user",data={"transaction_id": str(transaction_id)})
                #response.status_code = status.HTTP_200_OK
                return JSONResponse(content={"status":"success","detail":"OTP sent to user","transaction_id":str(transaction_id)})
    except Exception as e:
        print(f"Error: {e}")
        #content = ResponseModel(status="failed", message="An error occured")
        return JSONResponse(content = {"status":"failed","detail":"Internal server error"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/signup/resendotp")
def resend_otp(data: Annotated[ResendOtpRequest, Body()], response: Response):
    try:
        users_collection = db["users"]
        phone_number = f"+{data.country_code}{data.phone}"
        user = users_collection.find_one({"phone": {"country_code": data.country_code, "number": data.phone}})

        if user:
            if user["verified"] == "True":
                #content = ResponseModel(status="error", message="User already verified")
                #response.status_code = status.HTTP_409_CONFLICT
                return JSONResponse(content={"status":"failed","detail":"User already verified"}, status_code=status.HTTP_409_CONFLICT)
            else:
                otp = str(random.randint(100000, 999999))
                message = f"Your OTP is {otp}. Valid for 5 minutes"
                hashed_otp = hash_otp(otp)
                # await send_message(phone_number, message)
                transaction_id =  otp_transactions_collection.insert_one({"phone": phone_number, "otp": hashed_otp, "createdAt": datetime.utcnow()}).inserted_id
                print(f"OTP sent to user with transaction id: {transaction_id} otp: {otp}")
                
                #content = ResponseModel(status="success", message="OTP sent to user",data={"transaction_id": str(transaction_id)})
                #response.status_code = status.HTTP_200_OK
                return JSONResponse(content={"status":"success","detail":"OTP sent to user","transaction_id":str(transaction_id)})
        else :
            #content = ResponseModel(status="error", message="User not found")
            #response.status_code = status.HTTP_404_NOT_FOUND
            return JSONResponse(content={"status":"failed","detail":"User not found"},status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error: {e}")
        #content = ResponseModel(status="failed", message="An error occured")
        return JSONResponse(content = {"status":"failed","detail":"Internal server error"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/signout")
def signout(request: Request, response: Response):
    try:
        session_collection = db["sessions"]
        session_id = decrypt(str(request.cookies.get("session_id")))
        session_collection.delete_one({"_id": ObjectId(session_id)})
        response.delete_cookie("session_id",**default_cookie_config)
        request.state.session = {"isLoggedIn": "False"}
        content = ResponseModel(status="success", message="Signout successful")
        
        return JSONResponse(content=content.json())
    except Exception as e:
        print(f"Error: {e}")
        #content = ResponseModel(status="failed", message="An error occured")
        return JSONResponse(content = {"status":"failed","detail":"Internal server error"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
