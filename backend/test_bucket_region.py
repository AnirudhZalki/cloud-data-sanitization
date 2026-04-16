import boto3
import os
from dotenv import load_dotenv

load_dotenv(override=True)

bucket1 = os.getenv("INPUT_BUCKET", "data-sanitization-input-bucket")
bucket2 = os.getenv("OUTPUT_BUCKET", "data-sanitization-output-bucket")

s3 = boto3.client('s3')
try:
    print(f"{bucket1} location: ", s3.get_bucket_location(Bucket=bucket1))
except Exception as e:
    print("Error getting bucket1:", e)

try:
    print(f"{bucket2} location: ", s3.get_bucket_location(Bucket=bucket2))
except Exception as e:
    print("Error getting bucket2:", e)
