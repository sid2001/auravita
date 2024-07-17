from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pymongo
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")
print(f"mongodb uri: {uri}")

client = MongoClient(uri, server_api=ServerApi("1"))

try:
    print("Trying to connect to MongoDB uri: ",uri)
    client.admin.command("ping")
    print("Successfully pinged. Connected to MongoDB")
except Exception as e:
    print(f"failed to connect to MongoDB\nERROR: {e}")


db = client[db_name]

User = db["users"]
User.create_index([("phone",pymongo.ASCENDING)], unique=True)# unique index on phone number
#User.create_index([('health_id', pymongo.ASCENDING)], unique=True)# unique index on health_id

otp_transactions_collection = db["otp_transactions"]
# ttl index on otp_transactions collection
# after 5 minutes, the document will be automatically deleted
otp_transactions_collection.create_index([("createdAt", pymongo.ASCENDING)], expireAfterSeconds=300)
temporarily_shared_files_collection = db["temporarily_shared_files"]
# ttl index on temporarily_shared_files collection
# after 30 minutes, the document will be automatically deleted
temporarily_shared_files_collection.create_index([("createdAt", pymongo.ASCENDING)], expireAfterSeconds=1800)

notifications_collection = db["notifications"]
notifications_collection.create_index([("subscriberId", pymongo.ASCENDING)])
