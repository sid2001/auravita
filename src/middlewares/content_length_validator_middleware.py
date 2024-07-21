from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status 
from fastapi.responses import JSONResponse
class ContentLengthValidatorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_content_length: int = 1024*1024*5):
        super().__init__(app)
        self.max_content_length = max_content_length

    async def dispatch(self, request: Request, call_next):
        print("Content Length Validator Middleware")
        try:
            if(request.url.path == "/resource/uploadFile" and request.method == "POST"):
                content_size = request.headers.get("Content-Length")
                if content_size:
                    if int(content_size) > self.max_content_length:
                        print("File size is too large")
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size is too large")
                       # return JSONResponse(
                       #     status_code=status.HTTP_400_BAD_REQUEST,
                       #     content={"detail": "File size is too large"},
                       # )
            return await call_next(request)
        except Exception as e:
            print(f"Error: {e}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
            )

    
