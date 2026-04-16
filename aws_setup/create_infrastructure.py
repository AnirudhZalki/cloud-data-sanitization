import boto3
import argparse
import sys

def setup_aws_infra(region, input_bucket, output_bucket):
    try:
        s3 = boto3.client('s3', region_name=region)
        
        print(f"Creating Input Bucket: {input_bucket}...")
        try:
            if region == 'us-east-1':
                s3.create_bucket(Bucket=input_bucket)
            else:
                s3.create_bucket(Bucket=input_bucket, CreateBucketConfiguration={'LocationConstraint': region})
            print(f"✅ Created {input_bucket}")
        except s3.exceptions.BucketAlreadyOwnedByYou:
            print(f"ℹ️ Bucket {input_bucket} already exists and is owned by you.")
            
        print(f"Creating Output Bucket: {output_bucket}...")
        try:
            if region == 'us-east-1':
                s3.create_bucket(Bucket=output_bucket)
            else:
                s3.create_bucket(Bucket=output_bucket, CreateBucketConfiguration={'LocationConstraint': region})
            print(f"✅ Created {output_bucket}")
        except s3.exceptions.BucketAlreadyOwnedByYou:
            print(f"ℹ️ Bucket {output_bucket} already exists and is owned by you.")

        print("\n🎉 AWS S3 buckets have been created successfully!")
        print("Note: Lambda function setup requires packaging the code and OpenCV/Tesseract dependencies.")
        print("For this prototype, the FastAPI backend will act as the processor, handling API requests directly.")
        print("Set up your .env file in the backend directory with these bucket names.")
        
    except Exception as e:
        print(f"❌ Failed to set up AWS resources: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create AWS S3 Buckets for Data Sanitization System")
    parser.add_argument("--region", default="us-east-1", help="AWS Region")
    parser.add_argument("--input-bucket", default="data-sanitization-input-bucket-demo", help="Input Bucket Name")
    parser.add_argument("--output-bucket", default="data-sanitization-output-bucket-demo", help="Output Bucket Name")
    
    args = parser.parse_args()
    setup_aws_infra(args.region, args.input_bucket, args.output_bucket)
