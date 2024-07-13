from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

key = os.getenv("FERNET_KEY")

if isinstance(key,str):
    key = key.encode()

cipher_suite = Fernet(key)

def encrypt(data: str) -> str:
    encrypted_data = cipher_suite.encrypt(data.encode())
    return encrypted_data.decode()

def decrypt(data: str) -> str:
    decrypted_data = cipher_suite.decrypt(data.encode())
    return decrypted_data.decode()

def hash(data: str) -> str:
    salt = os.getenv("SALT")
    data_bytes = data.encode("utf-8")
    salt_bytes = salt.encode("utf-8")

    hashed_data = hashlib.sha256(data_bytes + salt_bytes).hexdigest()

    return hashed_data
