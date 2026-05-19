from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='frontend')
CORS(app)

# Configure boto3 clients to point to the local Floci instance
aws_region = os.getenv('AWS_REGION', 'us-east-1')
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID', 'mock_key')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'mock_secret')
aws_endpoint = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')

sns = boto3.client(
    'sns',
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

# Route to serve the frontend HTML
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# Route to serve CSS/JS and other static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# The API Endpoint for the frontend to hit
@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.json
    user_id = data.get('userId', 'Unknown')
    cart_total = data.get('cartTotal', 0)
    event_type = data.get('event', 'USER_CHECKOUT')

    print(f"🚀 Received API Checkout request from {user_id}...")

    # 1. Add user profile to DynamoDB
    print("📝 Adding user profile to DynamoDB...")
    try:
        dynamodb.put_item(
            TableName='MicroserviceTable',
            Item={
                'PK': {'S': f'USER#{user_id}'},
                'SK': {'S': 'PROFILE'},
                'Name': {'S': 'Frontend Customer'}
            }
        )
        print("✅ User profile added.")
    except Exception as e:
        print(f"❌ Error adding to DynamoDB: {e}")
        return jsonify({"error": str(e)}), 500

    # 2. Publish checkout event to SNS
    print("📡 Publishing event to SNS...")
    payload = {
        "event": event_type,
        "userId": user_id,
        "cartTotal": cart_total
    }

    try:
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:000000000000:user-events-topic',
            Message=json.dumps(payload)
        )
        print("✅ Event published successfully!")
    except Exception as e:
        print(f"❌ Error publishing to SNS: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Success! Event published."}), 200

if __name__ == "__main__":
    print("🌐 Starting User Service API on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
