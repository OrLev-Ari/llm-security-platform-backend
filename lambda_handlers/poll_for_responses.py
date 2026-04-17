import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# DynamoDB setup
dynamo = boto3.resource("dynamodb")
PROMPTS_TABLE = os.environ['PROMPTS_TABLE']
prompts_table = dynamo.Table(PROMPTS_TABLE)

def lambda_handler(event, context):
    # Logger
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
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

        # ------------------ Extract session_id from path ------------------
        session_id = None
        if event.get("pathParameters"):
            session_id = event["pathParameters"].get("session_id")
        
        if not session_id:
            logger.warning("Poll request missing session_id")
            return {
                'statusCode': 400,
                'body': json.dumps({"error": "Missing session_id in path"})
            }

        logger.info(f"Polling messages for session_id: {session_id}")

        # ------------------ Query prompts table ------------------
        logger.debug(f"Querying prompts table for session: {session_id}")
        response = prompts_table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ScanIndexForward=True  # ascending by timestamp
        )
        items = response.get("Items", [])
        logger.debug(f"Retrieved {len(items)} total items from prompts table")

        # ------------------ Filter verified and not sent ------------------
        new_messages = [
            item for item in items
            if item.get("verified_response") != "None" and not item.get("sent_to_ui", False)
        ]

        logger.info(f"Found {len(new_messages)} new verified messages for session {session_id}")

        # ------------------ Mark as sent_to_ui ------------------
        if new_messages:
            logger.info(f"Marking {len(new_messages)} messages as sent_to_ui")
        for item in new_messages:
            prompts_table.update_item(
                Key={
                    "session_id": item["session_id"],
                    "timestamp": item["timestamp"]
                },
                UpdateExpression="SET sent_to_ui = :s",
                ExpressionAttributeValues={":s": True}
            )

        logger.info(f"Returning {len(new_messages)} messages to client")
        # ------------------ Return to UI ------------------
        return {
            'statusCode': 200,
            'body': json.dumps({
                "session_id": session_id,
                "messages": [
                    {
                        "prompt_text": msg["prompt_text"],
                        "response_text": msg["response_text"],
                        "timestamp": msg["timestamp"],
                        "verified_response": msg["verified_response"]
                    } for msg in new_messages
                ]
            })
        }

    except Exception as e:
        logger.error(f"Error polling session {session_id}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }
