import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# DynamoDB setup
dynamo = boto3.resource("dynamodb")
CHALLENGE_SESSIONS_TABLE = os.environ['CHALLENGE_SESSIONS_TABLE']
challenge_sessions_table = dynamo.Table(CHALLENGE_SESSIONS_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("List user successful challenges request received")
    # Authenticate user
    try:
        jwt_secret = get_jwt_secret()
        token = extract_token_from_event(event)
        username, is_admin = validate_jwt(token, jwt_secret)
        logger.info(f"Authenticated user: {username}")
    except Exception as e:
        logger.warning(f"Authentication failed: {str(e)}")
        return {
            "statusCode": 401,
            "body": json.dumps({"error": str(e)})
        }
    
    try:
        # Use username from JWT as user_id
        user_id = username
        logger.info(f"Querying sessions for user: {user_id}")

        # ------------------ Query GSI on user_id with started_at sort ------------------
        response = challenge_sessions_table.query(
            IndexName="UserIdIndex", 
            KeyConditionExpression=Key("user_id").eq(user_id),
            ScanIndexForward=False  # latest sessions first
        )
        items = response.get("Items", [])
        logger.info(f"Retrieved {len(items)} sessions for user {user_id}")

        # ------------------ Prepare response ------------------
        completed_challenge_ids = {
            s["challenge_id"]
            for s in items
            if s["status"] == "completed"
        }

        completed_challenges_ids = list(completed_challenge_ids)
        logger.info(f"User {user_id} has completed {len(completed_challenges_ids)} challenges")
        return {
            "statusCode": 200,
            "body": json.dumps({"completed challenges": completed_challenges_ids})
        }

    except Exception as e:
        logger.error(f"Error listing challenges for user {user_id}: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
