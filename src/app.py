from fastapi import FastAPI, Request 
from fastapi.responses import JSONResponse
import time
from fastapi.middleware.cors import CORSMiddleware
from middlewares.sessionHandler import SessionHandler
from dotenv import load_dotenv
from middlewares.content_length_validator_middleware import ContentLengthValidatorMiddleware
from routes.auth import router as auth_router
from routes.resource import router as resource_router
from routes.user import router as user_router
from routes.notification import router as notification_router
import uvicorn
import os
from middlewares.auth import IsLoggedIn 
# Load environment variables
load_dotenv()

sub_app = FastAPI()
app = FastAPI(title="Mediaura Rest API", version="0.1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500","http://127.0.0.1:5500","http://localhost:5173","http://127.0.0.1:5173","http://localhost:8080","http://127.0.0.1:8080","http://localhost"],
    allow_credentials="true",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/protected", sub_app)
app.add_middleware(SessionHandler)
sub_app.add_middleware(ContentLengthValidatorMiddleware)
sub_app.add_middleware(IsLoggedIn)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
sub_app.include_router(user_router, prefix="/user", tags=["user"])
sub_app.include_router(notification_router, prefix="/notification", tags=["user"])
#sub_app.include_router(resource_router, prefix="/resource", tags=["resource"])
sub_app.include_router(resource_router, prefix="/resource", tags=["resource"])



@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run("app:app", host=os.getenv("HOST"), port=int(os.getenv("PORT")),reload=True)
