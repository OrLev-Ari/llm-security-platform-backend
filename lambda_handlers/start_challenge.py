import json
import boto3
import os
import logging
from datetime import datetime
import uuid
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# DynamoDB setup
dynamo = boto3.resource("dynamodb")
CHALLENGES_TABLE = os.environ['CHALLENGES_TABLE']
CHALLENGE_SESSIONS_TABLE = os.environ['CHALLENGE_SESSIONS_TABLE']

challenges_table = dynamo.Table(CHALLENGES_TABLE)
sessions_table = dynamo.Table(CHALLENGE_SESSIONS_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Authenticate user
    try:
        jwt_secret = get_jwt_secret()
        token = extract_token_from_event(event)
        username, is_admin = validate_jwt(token, jwt_secret)
    except Exception as e:
        logger.warning(f"Authentication failed: {str(e)}")
        return {
            "statusCode": 401,
            "body": json.dumps({"error": str(e)})
        }
    
    try:
        # Use username from JWT as user_id
        user_id = username

        # ------------------ Extract challenge_id from path ------------------
        challenge_id = event["pathParameters"].get("challenge_id")
        if not challenge_id:
            logger.warning("Start challenge request missing challenge_id")
            return {"statusCode": 400, "body": json.dumps({"error": "Missing challenge_id"})}

        logger.info(f"User {user_id} starting challenge {challenge_id}")

        # ------------------ Fetch challenge from DB ------------------
        resp = challenges_table.get_item(Key={"challenge_id": challenge_id})
        challenge = resp.get("Item")
        if not challenge:
            logger.warning(f"Challenge not found: {challenge_id}")
            return {"statusCode": 404, "body": json.dumps({"error": "Challenge not found"})}

        # Only return title + description to client
        challenge_info = {
            "title": challenge.get("title"),
            "description": challenge.get("description")
        }

        # ------------------ Create a new challenge session ------------------
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        logger.info(f"Creating new session {session_id} for user {user_id} and challenge {challenge_id}")
        sessions_table.put_item(
            Item={
                "session_id": session_id,
                "challenge_id": challenge_id,
                "user_id": user_id,
                "started_at": now,
                "updated_at": now,
                "status": "active"  # could be active/completed
            }
        )

        logger.info(f"Session created successfully: {session_id}")

        # ------------------ Return session info ------------------
        return {
            "statusCode": 200,
            "body": json.dumps({
                "session_id": session_id,
                "challenge": challenge_info
            })
        }

    except Exception as e:
        logger.error(f"Error starting challenge {challenge_id} for user {user_id}: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
