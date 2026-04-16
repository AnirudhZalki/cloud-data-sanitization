import boto3
import os
from dotenv import load_dotenv
from botocore.client import Config

load_dotenv(override=True)

AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-2")
bucket1 = os.getenv("INPUT_BUCKET", "data-sanitization-input-bucket")

# Client 1
s1 = boto3.client('s3', region_name=AWS_REGION, endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com", config=Config(signature_version='s3v4'))
url1 = s1.generate_presigned_url('get_object', Params={'Bucket': bucket1, 'Key': "test.pdf"}, ExpiresIn=3600)
print("URL 1:", url1)

# Client 2
s2 = boto3.client('s3', region_name=AWS_REGION, config=Config(signature_version='s3v4'))
url2 = s2.generate_presigned_url('get_object', Params={'Bucket': bucket1, 'Key': "test.pdf"}, ExpiresIn=3600)
print("URL 2:", url2)

# Client 3
s3_client = boto3.client('s3', region_name=AWS_REGION, config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'}))
url3 = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket1, 'Key': "test.pdf"}, ExpiresIn=3600)
print("URL 3:", url3)

