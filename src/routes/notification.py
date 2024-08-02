from fastapi import APIRouter, Request, FastAPI
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from services.notification import Notification_service 
from db.connection import db
from bson import ObjectId
router = APIRouter()

@router.get("/notify")
async def notify(request: Request):
    subscriber_id = request.state.session["user_id"]
    print(f"Subscriber id: {subscriber_id}")
    notify_instance = Notification_service(subscriber_id)

    return EventSourceResponse(notify_instance.generator())

@router.post("/readNotification/{notification_id}")
def read_notification(notification_id:str, req:Request):
    try:
        user_id = req.state.session["user_id"]
        result = db["notifications"].delete_one({"_id":ObjectId(notification_id),"subscriberId":user_id})
        print(f"result: {result}")
        print(f"Deleted count: {result.deleted_count}")
        print(f"user_id: {user_id}")
        return JSONResponse(status_code=200, content={"message": "Notification read successfully"})
    except Exception as e:
        print(f"error: ", (e))
        return JSONResponse(status_code=500, content={"message": "Internal server error"})
