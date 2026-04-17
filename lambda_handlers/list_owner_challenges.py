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
    logger.info("List owner challenges request received")
    # Authenticate and authorize (admin only)
    try:
        jwt_secret = get_jwt_secret()
        token = extract_token_from_event(event)
        username, is_admin = validate_jwt(token, jwt_secret)
        logger.info(f"Authenticated user: {username}, is_admin: {is_admin}")
        
        if not is_admin:
            logger.warning(f"Non-admin user {username} attempted to list owner challenges")
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
        logger.info("Scanning challenges table for all attributes")

        # ---------- Scan table without projection ----------
        response = challenges_table.scan()

        items = response.get("Items", [])
        logger.info(f"Retrieved {len(items)} owner challenges with all attributes")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "items": items
            })
        }

    except Exception as e:
        logger.exception("Failed to list challenges: " + str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
