import json
import boto3
import os
import logging
from datetime import datetime
import uuid

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

    # ------------------ Path param ------------------
    session_id = event.get("pathParameters", {}).get("session_id")
    if not session_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing session_id in path"})
        }

    # ------------------ Body ------------------
    body = json.loads(event.get("body", "{}"))
    prompt = body.get("prompt")

    if not prompt:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing prompt"})
        }

    now = datetime.utcnow().isoformat()

    # ------------------ Validate session ------------------
    session = challenge_sessions_table.get_item(
        Key={"session_id": session_id}
    ).get("Item")

    if not session:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Session not found"})
        }

    if session["status"] != "active":
        return {
            "statusCode": 409,
            "body": json.dumps({"error": "Session is not active"})
        }


    # ------------------ Store prompt ------------------
    prompt_id = str(uuid.uuid4())

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

    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps({
            "session_id": session_id,
            "prompt_id": prompt_id,
            "prompt": prompt,
            "timestamp": now
        })
    )

    logger.info(f"Prompt {prompt_id} enqueued for session {session_id}")


    return {
        "statusCode": 201,
        "body": json.dumps({"prompt_id": prompt_id})
    }
