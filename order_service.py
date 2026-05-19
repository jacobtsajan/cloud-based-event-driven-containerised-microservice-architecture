import boto3
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

aws_region = os.getenv('AWS_REGION', 'us-east-1')
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID', 'mock_key')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'mock_secret')
aws_endpoint = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')

# Configure the AWS clients to talk to your local Floci instance
sqs = boto3.client(
    'sqs',
    region_name=aws_region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    endpoint_url=aws_endpoint
)

dynamodb = boto3.client(
    'dynamodb',
    region_name=aws_region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    endpoint_url=aws_endpoint
)

QUEUE_URL = f'{aws_endpoint}/000000000000/order-service-queue'

print("📦 Order Service Worker started. Listening for checkout events... (Ctrl+C to exit)")

while True:
    try:
        # Poll the local queue for messages
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=2  # Long polling
        )

        if 'Messages' in response:
            for message in response['Messages']:
                # Parse the SNS outer envelope
                sns_envelope = json.loads(message['Body'])
                # Extract the actual inner message payload sent by the User Service
                actual_payload = json.loads(sns_envelope['Message'])
                user_id = actual_payload.get('userId')
                
                print("\n🔔 [EVENT RECEIVED] New checkout notification from User Service!")
                print(f"   👤 User ID:    {user_id}")
                print(f"   🛒 Cart Total: ${actual_payload.get('cartTotal')}")
                print(f"   ⚡ Event Type: {actual_payload.get('event')}")

                # POISON PILL TESTING: Test the DLQ circuit breaker
                if user_id == "CRASH":
                    print("☠️ POISON PILL DETECTED! Simulating catastrophic worker failure...")
                    raise Exception("Intentional Poison Pill crash to test Dead Letter Queue.")

                # Success path: Update DynamoDB
                print("📝 Updating order status in DynamoDB...")
                try:
                    dynamodb.put_item(
                        TableName='MicroserviceTable',
                        Item={
                            'PK': {'S': f'USER#{user_id}'},
                            'SK': {'S': 'ORDER_FULFILLED'},
                            'Status': {'S': 'SUCCESS'}
                        }
                    )
                    print("✅ Order recorded in DynamoDB.")
                except Exception as db_err:
                    print(f"⚠️ Failed to write to DynamoDB: {db_err}")

                # Delete the message from the queue so it isn't processed again
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=message['ReceiptHandle']
                )
                print("✅ Message processed and cleared from queue.")

    except Exception as e:
        print(f"❌ Error processing message: {e}")
    
    time.sleep(1)
