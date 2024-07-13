from sse_starlette.sse import EventSourceResponse
from db.connection import db, notifications_collection
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime
from models.other_models import Notification
import queue
from typing import Dict, List
import asyncio
load_dotenv()

class Notification_service:
    message_queue:Dict[str, queue.Queue ] = {}
    #subscribers: Dict[str,str]  = {} 

    def __init__(self, subscriberId: str):
        self.subscriberId = subscriberId
        #self.db_access_time = datetime.utcnow()
        Notification_service.message_queue = {**Notification_service.message_queue, **{self.subscriberId: queue.Queue()}} 
        self.get_notifications_from_db()
        
        #Notification_service.subscribers[self.subscriberId] = "online"
    #def delete_notifications_from_db(self):
    #    notifications_collection.delete_many({"subscriberId": self.subscriberId, "createdAt": {"$lt": self.db_access_time}}) # delete notifications that are sent to the subscriber

    def get_notifications_from_db(self) -> None:
        try:
            notifications = notifications_collection.find({"subscriberId": self.subscriberId})
            for notification in notifications:
                notificationId = str(notification["_id"])
                data = notification["data"]
                payload = Notification(id=notificationId, data=data).dict()
                Notification_service.message_queue[self.subscriberId].put(payload)
        except Exception as e:
            print(f"Error while fetching notifications from db:", str(e))

    def subscribe(self):
        return EventSourceResponse(self.generator())

    def subscriber_status(self):
        return self.subscriberId in Notification_service.message_queue

    async def generator(self):
        try:
            while True:
                if self.subscriber_status():
                    while not Notification_service.message_queue[self.subscriberId].empty():
                        data = Notification_service.message_queue[self.subscriberId].get()
                        print(f"sending notification to {self.subscriberId} message: {data}")
                        yield {"event": "notification", "data": data}  
                    await asyncio.sleep(int(os.getenv("NOTIFICATION_INTERVAL")))
        except asyncio.CancelledError:
            if(Notification_service.message_queue[self.subscriberId].empty()):
                print("Client disconnected")
            else:
                print("Client disconnected with pending messages")
        finally:        
            del Notification_service.message_queue[self.subscriberId]
    
    @classmethod
    def delete_notification_from_db(cls, notificationId: str):
        notifications_collection.delete_one({"_id": ObjectId(notificationId)})
