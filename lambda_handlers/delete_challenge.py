import json
import boto3
import os
import logging
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# AWS clients
dynamo = boto3.resource("dynamodb")

# Env vars
CHALLENGES_TABLE = os.environ["CHALLENGES_TABLE"]
challenges_table = dynamo.Table(CHALLENGES_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Delete challenge request received")
    # Authenticate and authorize (admin only)
    try:
        jwt_secret = get_jwt_secret()
        token = extract_token_from_event(event)
        username, is_admin = validate_jwt(token, jwt_secret)
        logger.info(f"Authenticated user: {username}, is_admin: {is_admin}")
        
        if not is_admin:
            logger.warning(f"Non-admin user {username} attempted to delete challenge")
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
        # Try to get challenge_id from path parameters first
        challenge_id = None
        challenge_id = event["pathParameters"]["challenge_id"]
        
        if not challenge_id:
            logger.warning("Delete challenge request missing challenge_id")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "challenge_id is required"})
            }

        logger.info(f"Deleting challenge: {challenge_id}")

        # Delete item
        challenges_table.delete_item(
            Key={"challenge_id": challenge_id},
            ConditionExpression="attribute_exists(challenge_id)"
        )

        logger.info(f"Challenge deleted successfully: {challenge_id}")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Challenge deleted successfully"})
        }

    except challenges_table.meta.client.exceptions.ConditionalCheckFailedException:
        logger.warning(f"Challenge not found for deletion: {challenge_id}")
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Challenge not found"})
        }

    except Exception as e:
        logger.error("fail because" + str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
