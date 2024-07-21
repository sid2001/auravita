from fastapi import APIRouter, Request, FastAPI
from sse_starlette.sse import EventSourceResponse
from services.notification import Notification_service 

router = APIRouter()

@router.get("/notify")
async def notify(request: Request):
    subscriber_id = request.state.session["user_id"]
    print(f"Subscriber id: {subscriber_id}")
    notify_instance = Notification_service(subscriber_id)

    return EventSourceResponse(notify_instance.generator())
    
