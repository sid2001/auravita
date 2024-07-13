from twilio.rest import Client
from dotenv import load_dotenv
import os
load_dotenv()

accountSID = os.getenv("TWILIO_ACCOUNT_SID")
authToken = os.getenv("TWILIO_AUTH_TOKEN")
senderNumber = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(accountSID, authToken)

def send_message(to, message):
    message = client.messages.create(
        to=to,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        body=message
    )
    return message.sid


