import json
import boto3
import os
import logging

# AWS clients
dynamo = boto3.resource("dynamodb")

# Env vars
CHALLENGES_TABLE = os.environ["CHALLENGES_TABLE"]
challenges_table = dynamo.Table(CHALLENGES_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        # Try to get challenge_id from path parameters first
        challenge_id = None
        challenge_id = event["pathParameters"]["challenge_id"]
        
        if not challenge_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "challenge_id is required"})
            }

        # Delete item
        challenges_table.delete_item(
            Key={"challenge_id": challenge_id},
            ConditionExpression="attribute_exists(challenge_id)"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Challenge deleted successfully"})
        }

    except challenges_table.meta.client.exceptions.ConditionalCheckFailedException:
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
