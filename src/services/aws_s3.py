import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv
import os
import base64
load_dotenv()

ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
SECRET_KEY = os.getenv("AWS_SECRET_KEY")
REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_SSE_KEY = os.getenv("AWS_SSE_KEY")
AWS_SSE_ALGORITHM = os.getenv("AWS_SSE_ALGORITHM")
AWS_SSE_KEY_MD5 = os.getenv('AWS_SSE_KEY_MD5')

class S3Client:
    def __init__(self,bucket_name=None):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=REGION
        )
        if bucket_name is not None:
            self.bucket_name = bucket_name
        else:
            self.bucket_name = BUCKET_NAME

    async def put_object(self,file, key: str, bucket_name : str = None):
        # handles multipart uploads for large files automatically
        # use put_object for small files
        # file_name: name of the file
        # bucket_name: name of the bucket
        try:
            content = await file.read()
            #print(f"Content: {content}")
            print(f"Key: {key}")
            if bucket_name is None:
                bucket_name = self.bucket_name
            self.client.put_object(
                    Body=content,
                    Bucket="auravita", 
                    Key=key,
                    #SSECustomerKey=AWS_SSE_KEY,
                    #SSECustomerAlgorithm=AWS_SSE_ALGORITHM,
                    #SSECustomerKeyMD5=AWS_SSE_KEY_MD5
            )
            return None
        except NoCredentialsError:
            return "Credentials not available"
            print("Credentials not available")
        except PartialCredentialsError:
            return "Partial credentials available"
            print("Partial credentials available")

    def get_object(self, file_name: str, bucket_name: str = None):
        # file_name: name of the file
        # bucket_name: name of the bucket
        # returns the file object
        try:
            if bucket_name is None:
                bucket_name = self.bucket_name
            response = self.client.get_object(
                    Bucket=bucket_name, 
                    key=file_name, 
                    #SSECustomerKey=AWS_SSE_KEY,
                    #SSECustomerAlgorithm=AWS_SSE_ALGORITHM,
                    #SSECustomerKeyMD5= AWS_SSE_KEY_MD5    
                    )
            return [response,None]
        except NoCredentialsError:
            print("Credentials not available")
            return [None,"Credentials not available"]
        except PartialCredentialsError:
            print("Partial credentials available")
            return [None, "Partial credentials available"]

    ##uncomment this section when delete file mechanism is added.
    #def delete_object(self, file_name: str, bucket_name: str = None):
    #    # file_name: name of the file
    #    # bucket_name: name of the bucket
    #    # returns the file object
    #    try:
    #        if bucket_name is None:
    #        bucket_name = self.bucket_name
    #        response = self.client.delete_object(
    #            Bucket=bucket_name, 
    #            key=file_name, 
    #            SSECustomerKey=AWS_SSE_KEY,
    #            SSECustomerAlgorithm=AWS_SSE_ALGORITHM,
    #            SSECustomerKeyMD5= AWS_SSE_KEY_MD5    
    #            )
    #        return [response,None]
    #    except NoCredentialsError:
    #        print("Credentials not available")
    #        return [None,"Credentials not available"]
    #    except PartialCredentialsError:
    #        print("Partial credentials available")
    #        return [None, "Partial credentials available"]

    def generate_presigned_url(self, object_key: str, client_method: str, expiration: int) -> str :
        # client_method: "get_object" or "put_object"
        # expiration: time in seconds
        # file_name: name of the file
        # returns a presigned url
        try:
            #print("MD5: ",AWS_SSE_KEY_MD5)
            url = self.client.generate_presigned_url(
                ClientMethod=client_method,
                Params={
                    "Bucket": BUCKET_NAME,
                    "Key": object_key,
                    #"SSECustomerKey":AWS_SSE_KEY,
                    #"SSECustomerAlgorithm": AWS_SSE_ALGORITHM,
                    #'SSECustomerKeyMD5': AWS_SSE_KEY_MD5
                },
                ExpiresIn=expiration
            )
            return [url,None]
        except NoCredentialsError:
            print("Credentials not available")
            return [None,"Credentials not available"]
        except PartialCredentialsError:
            print("Partial credentials available")
            return [None, "Partial credentials available"]
        except ClientError as e:
            print(f"Error: {e}")
            return [None, f"Error: {e}"]

