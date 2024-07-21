from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from db.connection import db
from utils.crypto import encrypt, decrypt
from bson import ObjectId
from typing import Callable
from fastapi import HTTPException, status
from fastapi.responses  import JSONResponse
from datetime import datetime, timedelta

guest_session = {"name":"Anonymous","isLoggedIn": "False"}
default_cookie_config = {
    "max_age": 3600,
    "expires": (datetime.utcnow() + timedelta(hours = 1)).strftime('%a, %d %b %Y %H:%M:%S GMT'),
    "path": "/",
    "domain": None,
    "secure": False,
    "httponly": True,
    "samesite": "lax",
}    

def save_session(session: dict) -> str:
    session_collection = db["sessions"]
    session_id = session_collection.insert_one(session).inserted_id
    return str(session_id)

class SessionHandler(BaseHTTPMiddleware):
    def __init__(self, app: Callable, config: dict | None = None):
        super().__init__(app)
        self.config = config

    async def dispatch(self, request: Request, call_next):
        try:
            print("Session Handler Middleware 1\n")
            cookies = request.cookies
            print(f"Cookies: {cookies}\n")
            session_id = cookies.get("session_id")
            if session_id:
                print(f"Session ID found: {session_id}\n")
                session_collection = db["sessions"]
                session_id = decrypt(session_id)
                session = session_collection.find_one({"_id": ObjectId(session_id)})
                if session:
                    print(f"Session found: {session}\n")
                    request.state.session = session
                    user_collection = db["users"]
                    user = user_collection.find_one({"_id": ObjectId(session["user_id"])})
                    if not user:
                        raise HTTPException(status_code=404, detail="User not found")
                else:
                    request.state.session = guest_session
            else:
                request.state.session = guest_session
            
            current_session = request.state.session
            print(f"Before request: {request.state.session}\n")
            response = await call_next(request)
            print(f"After request: {request.state.session}\n")
            
            if current_session != request.state.session:
                print(f"Session changed\n")
                session_id = encrypt(save_session(request.state.session))
                config = self.config or default_cookie_config
                response.set_cookie(key = "session_id",value = session_id, **config)

            return response
        except Exception as e:
            print(f"Error: {e}")
            return JSONResponse(content={"detail": e.detail if hasattr(e,"detail") else "Internal server error"}, status_code=e.status_code if hasattr(e, "status_code") else status.HTTP_500_INTERNAL_SERVER_ERROR)
