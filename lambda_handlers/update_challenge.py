import json
import boto3
import os
import logging
from datetime import datetime
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# AWS clients
dynamo = boto3.resource("dynamodb")

# Env vars
CHALLENGES_TABLE = os.environ["CHALLENGES_TABLE"]
challenges_table = dynamo.Table(CHALLENGES_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Update challenge request received")
    # Authenticate and authorize (admin only)
    try:
        jwt_secret = get_jwt_secret()
        token = extract_token_from_event(event)
        username, is_admin = validate_jwt(token, jwt_secret)
        logger.info(f"Authenticated user: {username}, is_admin: {is_admin}")
        
        if not is_admin:
            logger.warning(f"Non-admin user {username} attempted to update challenge")
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
        challenge_id = None

        if event.get("pathParameters") and event["pathParameters"].get("challenge_id"):
            challenge_id = event["pathParameters"]["challenge_id"]

        body = json.loads(event.get("body", "{}"))

        if not challenge_id:
            logger.warning("Update challenge request missing challenge_id")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "challenge_id is required"})
            }

        logger.info(f"Updating challenge: {challenge_id}")

        # Allowed fields to update
        allowed_fields = ["title", "description", "system_prompt"]

        update_expressions = []
        expression_values = {}
        expression_names = {}

        for field in allowed_fields:
            if field in body:
                update_expressions.append(f"#{field} = :{field}")
                expression_values[f":{field}"] = body[field]
                expression_names[f"#{field}"] = field

        if not update_expressions:
            logger.warning(f"No valid fields to update for challenge: {challenge_id}")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No valid fields to update"})
            }


        logger.info(f"Executing update for challenge {challenge_id} with fields: {list(expression_names.values())}")
        challenges_table.update_item(
            Key={"challenge_id": challenge_id},
            UpdateExpression="SET " + ", ".join(update_expressions),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names,
            ConditionExpression="attribute_exists(challenge_id)",
            ReturnValues="ALL_NEW"
        )

        logger.info(f"Challenge updated successfully: {challenge_id}")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Challenge updated successfully"})
        }

    except challenges_table.meta.client.exceptions.ConditionalCheckFailedException:
        logger.warning(f"Challenge not found for update: {challenge_id}")
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Challenge not found"})
        }

    except Exception as e:
        logger.error(str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
