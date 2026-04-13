import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key

# DynamoDB setup
dynamo = boto3.resource("dynamodb")
CHALLENGE_SESSIONS_TABLE = os.environ['CHALLENGE_SESSIONS_TABLE']
challenge_sessions_table = dynamo.Table(CHALLENGE_SESSIONS_TABLE)

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
        logger.info(f"Listing sessions for user {user_id}")

        # ------------------ Query GSI on user_id with started_at sort ------------------
        response = challenge_sessions_table.query(
            IndexName="UserIdIndex", 
            KeyConditionExpression=Key("user_id").eq(user_id),
            ScanIndexForward=False  # latest sessions first
        )
        items = response.get("Items", [])

        # ------------------ Prepare response ------------------
        completed_challenge_ids = {
            s["challenge_id"]
            for s in items
            if s["status"] == "completed"
        }

        completed_challenges_ids = list(completed_challenge_ids)
        return {
            "statusCode": 200,
            "body": json.dumps({"completed challenges": completed_challenges_ids})
        }

    except Exception as e:
        logger.error(f"Error listing challenges for user {user_id}: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
