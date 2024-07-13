from pydantic import BaseModel, conint, Field 
from typing import Literal

class SignUpRequest(BaseModel):
    country_code: int
    phone: str = Field(..., min_length=10, max_length=10, pattern="^[0-9]*$")
    name: str
    user_type: Literal["doctor", "patient"]

class SignInRequest(BaseModel):
    country_code: int
    phone: str = Field(..., min_length=10, max_length=10, pattern="^[0-9]*$")


class SignInResponse(BaseModel):
    token: str

class SignUpResponse(BaseModel):
    message: str

class ResponseModel(BaseModel):
    status: str
    message: str
    data: dict | None = None

class ResendOtpRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=10, pattern="^[0-9]*$")
    country_code: int

class OtpVerificationRequest(BaseModel):
    otp: str
    phone: str = Field(..., min_length=10, max_length=10, pattern="^[0-9]*$")
    country_code: int

