import json
import boto3
import os
import logging
from datetime import datetime
import uuid

# DynamoDB setup
dynamo = boto3.resource("dynamodb")
CHALLENGES_TABLE = os.environ['CHALLENGES_TABLE']
CHALLENGE_SESSIONS_TABLE = os.environ['CHALLENGE_SESSIONS_TABLE']

challenges_table = dynamo.Table(CHALLENGES_TABLE)
sessions_table = dynamo.Table(CHALLENGE_SESSIONS_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        try:
            # ------------------ Extract user info from Cognito JWT ------------------
            claims = event["requestContext"]["authorizer"]["claims"]
            user_id = claims.get("sub")
            if not user_id:
                return {"statusCode": 403, "body": json.dumps({"error": "Unauthorized"})}
        except:
            user_id = "randomly because no auth yet"

        # ------------------ Extract challenge_id from path ------------------
        challenge_id = event["pathParameters"].get("challenge_id")
        if not challenge_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing challenge_id"})}

        logger.info(f"User {user_id} starting challenge {challenge_id}")

        # ------------------ Fetch challenge from DB ------------------
        resp = challenges_table.get_item(Key={"challenge_id": challenge_id})
        challenge = resp.get("Item")
        if not challenge:
            return {"statusCode": 404, "body": json.dumps({"error": "Challenge not found"})}

        # Only return title + description to client
        challenge_info = {
            "title": challenge.get("title"),
            "description": challenge.get("description")
        }

        # ------------------ Create a new challenge session ------------------
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

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

        logger.info(f"Created session {session_id} for user {user_id} and challenge {challenge_id}")

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
