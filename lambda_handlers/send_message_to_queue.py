import json
import boto3
import os
import logging
from datetime import datetime
import uuid
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# AWS clients
sqs = boto3.client('sqs')
dynamo = boto3.resource("dynamodb")

# Env vars
QUEUE_URL = os.environ['SQS_QUEUE_URL']
CHALLENGE_SESSIONS_TABLE = os.environ['CHALLENGE_SESSIONS_TABLE']
PROMPTS_TABLE = os.environ['PROMPTS_TABLE']

challenge_sessions_table = dynamo.Table(CHALLENGE_SESSIONS_TABLE)
prompts_table = dynamo.Table(PROMPTS_TABLE)

def lambda_handler(event, context):
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
    
    # Use username from JWT as user_id
    user_id = username

    # ------------------ Path param ------------------
    session_id = event.get("pathParameters", {}).get("session_id")
    if not session_id:
        logger.warning("Send message request missing session_id")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing session_id in path"})
        }

    logger.info(f"Processing message for session {session_id} from user {user_id}")

    # ------------------ Body ------------------
    body = json.loads(event.get("body", "{}"))
    prompt = body.get("prompt")

    if not prompt:
        logger.warning(f"Missing prompt in request for session {session_id}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing prompt"})
        }

    now = datetime.utcnow().isoformat()

    # ------------------ Validate session ------------------
    logger.debug(f"Validating session: {session_id}")
    session = challenge_sessions_table.get_item(
        Key={"session_id": session_id}
    ).get("Item")

    if not session:
        logger.warning(f"Session not found: {session_id}")
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Session not found"})
        }
    
    # Validate session belongs to authenticated user
    if session.get("user_id") != user_id:
        logger.warning(f"User {user_id} attempted to access session {session_id} belonging to {session.get('user_id')}")
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Forbidden: Session does not belong to user"})
        }

    if session["status"] != "active":
        logger.warning(f"Attempted to send message to inactive session: {session_id}")
        return {
            "statusCode": 409,
            "body": json.dumps({"error": "Session is not active"})
        }


    # ------------------ Store prompt ------------------
    prompt_id = str(uuid.uuid4())
    logger.info(f"Storing prompt {prompt_id} for session {session_id}")

    prompts_table.put_item(
        Item={
            "session_id": session_id,
            "prompt_id": prompt_id,
            "prompt_text": prompt,
            "response_text": None,
            "verified_response": None,
            "timestamp": now,
            "sent_to_ui": False
        }
    )

    logger.info(f"Sending message to SQS queue for prompt {prompt_id}")
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps({
            "session_id": session_id,
            "prompt_id": prompt_id,
            "prompt": prompt,
            "timestamp": now
        })
    )

    logger.info(f"Prompt {prompt_id} successfully enqueued for session {session_id}")


    return {
        "statusCode": 201,
        "body": json.dumps({"prompt_id": prompt_id})
    }
