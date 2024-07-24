from sse_starlette.sse import EventSourceResponse
from db.connection import db, notifications_collection
from dotenv import load_dotenv
import os
from db.connection import db
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
        Notification_service.message_queue = {**Notification_service.message_queue, **{self.subscriberId: queue.Queue(maxsize=0)}} 
        self.get_notifications_from_db()
        
        #Notification_service.subscribers[self.subscriberId] = "online"
    #def delete_notifications_from_db(self):
    #    notifications_collection.delete_many({"subscriberId": self.subscriberId, "createdAt": {"$lt": self.db_access_time}}) # delete notifications that are sent to the subscriber

    def get_notifications_from_db(self) -> None:
        try:
            notifications = db["notifications"].find({"subscriberId": self.subscriberId})
            notifications = list(notifications)
            #print("Notifications from db: ",notifications)
            for notification in notifications:
                payload = {"id":str(notification["_id"]),"data":notification["data"],"createdAt":notification["createdAt"]}
               # print(f"Notification: {payload}\nfor {self.subscriberId}")
                Notification_service.message_queue[self.subscriberId].put(payload)
        except Exception as e:
            print(f"Error while fetching notifications from db:", str(e))

    def subscribe(self):
        return EventSourceResponse(self.generator())

    def subscriber_status(self):
        return self.subscriberId in Notification_service.message_queue

    async def generator(self):
        try:
            #print("Client connected")
            while True:
                #print("Checking for new notifications")
                if self.subscriber_status():
                    #print(f"Notifications available for {self.subscriberId}")
                    #print("Queue: ",Notification_service.message_queue[self.subscriberId].qsize())
                    while not Notification_service.message_queue[self.subscriberId].empty():
                        #print(f"Sending notification to {self.subscriberId}")
                        data = Notification_service.message_queue[self.subscriberId].get()
                        #print(f"sending notification to {self.subscriberId} message: {data}")
                        yield {"event": "notification", "data": data}  
                    await asyncio.sleep(int(os.getenv("NOTIFICATION_INTERVAL")))
        except asyncio.CancelledError:
            if(Notification_service.message_queue[self.subscriberId].empty()):
                print("Client disconnected")
            else:
                print("Client disconnected with pending messages")
        finally:        
            del Notification_service.message_queue[self.subscriberId]
    
    @staticmethod
    def delete_notification_from_db(notificationId: str):
        notifications_collection.delete_one({"_id": ObjectId(notificationId)})
    
    @staticmethod
    def add_to_db(sub_id,data):
        data = {
            "_id": ObjectId(),
            "subscriberId":sub_id,
            "data": data,
            "createdAt": datetime.utcnow()
        }
        try:
            db["notifications"].insert_one(data)
        except Exception as e:
            print(f"Error while adding notification to db:", str(e))
            return None
        return {"createdAt":data["createdAt"],"data":data["data"],"id":data["_id"]}

    @staticmethod
    def add_notification(id:str,data:str | None = None):
        if(id in Notification_service.message_queue and data is not None):
            Notification_service.message_queue[id].put(data)

