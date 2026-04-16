import boto3
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# We will read from env vars or prompt the user
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-2")
INPUT_BUCKET = os.getenv("INPUT_BUCKET", "data-sanitization-input-bucket")
OUTPUT_BUCKET = os.getenv("OUTPUT_BUCKET", "data-sanitization-output-bucket")

from botocore.client import Config

# Initializing boto3 client
# It will use the credentials stored in ~/.aws/credentials by default
# If AWS is not configured, it will raise an error when trying to upload.
# For local testing without AWS, we can wrap in try/except or add a local fallback
try:
    s3_client = boto3.client(
        's3', 
        region_name=AWS_REGION, 
        config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'})
    )
except Exception as e:
    print(f"Warning: AWS credentials not found or invalid. AWS integration will fail. {e}")
    s3_client = None

def upload_to_s3(file_bytes, bucket_name, object_name):
    """
    Uploads a file (in bytes) to an S3 bucket
    """
    if not s3_client:
        return None
        
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_name,
            Body=file_bytes
        )
        return True
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return False

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """
    Generate a presigned URL to share an S3 object
    """
    if not s3_client:
        # Fallback to a mock URL for local testing without AWS
        return f"http://localhost:8000/mock-s3-url/{bucket_name}/{object_name}"
        
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
        return response
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None
