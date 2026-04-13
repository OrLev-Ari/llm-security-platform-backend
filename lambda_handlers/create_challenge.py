# Lambda: CreateChallengeLambdaFunction
import json
import boto3
import os
import logging
from datetime import datetime
import uuid

dynamo = boto3.resource("dynamodb")
CHALLENGES_TABLE = os.environ["CHALLENGES_TABLE"]
challenges_table = dynamo.Table(CHALLENGES_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        required_fields = ["title", "description", "system_prompt"]
        missing_fields = [f for f in required_fields if f not in body]
        if missing_fields:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required fields",
                    "fields": missing_fields
                })
            }
        challenge_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        challenges_table.put_item(
            Item={
                "challenge_id": challenge_id,
                "title": body["title"],
                "description": body["description"],
                "system_prompt": body["system_prompt"],
                "created_at": now
            },
            ConditionExpression="attribute_not_exists(challenge_id)"
        )
        return {
            "statusCode": 201,
            "body": json.dumps({
                "challenge_id": challenge_id,
                "created_at": now
            })
        }
    except challenges_table.meta.client.exceptions.ConditionalCheckFailedException:
        return {
            "statusCode": 409,
            "body": json.dumps({"error": "Challenge already exists"})
        }
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON body"})
        }
    except Exception as e:
        logger.error("Create challenge failed", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
