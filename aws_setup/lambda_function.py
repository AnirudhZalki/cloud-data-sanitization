import json
import urllib.parse
import boto3
import os

print('Loading function')

s3 = boto3.client('s3')

# In a real deployed environment, you'd trigger the FastAPI backend 
# or process the image directly if this Lambda had OpenCV/Tesseract layers installed.
# For this prototype simulation, we demonstrate how it would trigger.
BACKEND_URL = os.environ.get("BACKEND_URL", "http://your-ec2-ip:8000/process-s3")

def lambda_handler(event, context):
    """
    AWS Lambda function that triggers when a file is uploaded to the Input S3 Bucket.
    """
    try:
        # Get the bucket and object key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        
        response = s3.get_object(Bucket=bucket, Key=key)
        print("CONTENT TYPE: " + response['ContentType'])
        print(f"File {key} uploaded to bucket {bucket}")
        
        # Simulated invocation of the internal API to process the file
        # import requests
        # response = requests.post(BACKEND_URL, json={"bucket": bucket, "key": key})
        # print("Backend processing triggered:", response.status_code)
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully triggered processing for {key}')
        }
    except Exception as e:
        print(e)
        print(f'Error processing object {key} from bucket {bucket}.')
        raise e
