from fastapi import APIRouter,Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware

class IsLoggedIn(BaseHTTPMiddleware):
    def __init__(self, app: Callable):
        super().__init__(app)

    async def dispatch(self, request:Request, call_next):
        try:
            session = request.state.session
            if not session["isLoggedIn"]=="True":
                print("Not authenticated")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
                #return JSONResponse(content={"error":"Not authenticated"},status_code=401)
            print("Authenticated")
            return await call_next(request)
        except Exception as e:
            print(f"Error: {e}")
            return JSONResponse(content={"detail":e.detail},status_code=e.status_code if hasattr(e,"status_code") else status.HTTP_500_INTERNAL_SERVER_ERROR)
