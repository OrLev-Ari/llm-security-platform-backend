import json
import boto3
import os
import logging
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# ---------- Setup ----------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo = boto3.resource("dynamodb")
CHALLENGES_TABLE = os.environ["CHALLENGES_TABLE"]
challenges_table = dynamo.Table(CHALLENGES_TABLE)

def lambda_handler(event, context):
    logger.info("Get challenge request received")
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
        # ---------- Extract path param ----------
        path_params = event.get("pathParameters") or {}
        challenge_id = path_params.get("challenge_id")

        if not challenge_id:
            logger.warning("Missing challenge_id in pathParameters")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing challenge_id"})
            }

        logger.info(f"Fetching challenge {challenge_id}")

        # ---------- Fetch challenge ----------
        response = challenges_table.get_item(
            Key={"challenge_id": challenge_id}
        )

        item = response.get("Item")
        if not item:
            logger.info(f"Challenge not found: {challenge_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Challenge not found"})
            }

        # ---------- Filter response ----------
        public_challenge = {
            "title": item.get("title"),
            "description": item.get("description")
        }

        return {
            "statusCode": 200,
            "body": json.dumps(public_challenge)
        }

    except Exception as e:
        logger.exception(f"Failed to get challenge {challenge_id}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
