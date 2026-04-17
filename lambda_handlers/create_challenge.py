# Lambda: CreateChallengeLambdaFunction
import json
import boto3
import os
import logging
from datetime import datetime
import uuid
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

dynamo = boto3.resource("dynamodb")
CHALLENGES_TABLE = os.environ["CHALLENGES_TABLE"]
challenges_table = dynamo.Table(CHALLENGES_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Create challenge request received")
    # Authenticate and authorize (admin only)
    try:
        jwt_secret = get_jwt_secret()
        token = extract_token_from_event(event)
        username, is_admin = validate_jwt(token, jwt_secret)
        logger.info(f"Authenticated user: {username}, is_admin: {is_admin}")
        
        if not is_admin:
            logger.warning(f"Non-admin user {username} attempted to create challenge")
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Forbidden: Admin access required"})
            }
    except Exception as e:
        logger.warning(f"Authentication failed: {str(e)}")
        return {
            "statusCode": 401,
            "body": json.dumps({"error": str(e)})
        }
    
    try:
        body = json.loads(event.get("body", "{}"))
        required_fields = ["title", "description", "system_prompt"]
        missing_fields = [f for f in required_fields if f not in body]
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required fields",
                    "fields": missing_fields
                })
            }
        challenge_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        logger.info(f"Creating challenge with ID: {challenge_id}, title: {body['title']}")
        challenges_table.put_item(
            Item={
                "challenge_id": challenge_id,
                "title": body["title"],
                "description": body["description"],
                "system_prompt": body["system_prompt"],
                "created_at": now
            },
            ConditionExpression="attribute_not_exists(challenge_id)"
        )
        logger.info(f"Challenge created successfully: {challenge_id}")
        return {
            "statusCode": 201,
            "body": json.dumps({
                "challenge_id": challenge_id,
                "created_at": now
            })
        }
    except challenges_table.meta.client.exceptions.ConditionalCheckFailedException:
        logger.error(f"Challenge already exists: {challenge_id}")
        return {
            "statusCode": 409,
            "body": json.dumps({"error": "Challenge already exists"})
        }
    except json.JSONDecodeError:
        logger.error("Invalid JSON in create challenge request body")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON body"})
        }
    except Exception as e:
        logger.error("Create challenge failed", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
