provider "aws" {
  region                      = "us-east-1"
  access_key                  = "mock_key"
  secret_key                  = "mock_secret"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    apigateway = "http://localhost:4566"
    dynamodb   = "http://localhost:4566"
    sns        = "http://localhost:4566"
    sqs        = "http://localhost:4566"
  }
}

# =============================================================================
# 1. STORAGE & BUS TIERS
# =============================================================================
resource "aws_dynamodb_table" "microservice_db" {
  name         = "MicroserviceTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }
}

resource "aws_sns_topic" "user_events" {
  name = "user-events-topic"
}

# =============================================================================
# 2. RESILIENT QUEUE TIER (Main Queue + Dead Letter Queue)
# =============================================================================
resource "aws_sqs_queue" "order_service_dlq" {
  name = "order-service-dlq"
}

resource "aws_sqs_queue" "order_service_queue" {
  name                      = "order-service-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 86400
  
  # If a message fails processing 3 times, route it to the DLQ automatically
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.order_service_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sns_topic_subscription" "user_to_order_subscription" {
  topic_arn = aws_sns_topic.user_events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.order_service_queue.arn
}

