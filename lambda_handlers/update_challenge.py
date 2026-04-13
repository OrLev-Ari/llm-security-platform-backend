import json
import boto3
import os
import logging
from datetime import datetime

# AWS clients
dynamo = boto3.resource("dynamodb")

# Env vars
CHALLENGES_TABLE = os.environ["CHALLENGES_TABLE"]
challenges_table = dynamo.Table(CHALLENGES_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        challenge_id = None

        if event.get("pathParameters") and event["pathParameters"].get("challenge_id"):
            challenge_id = event["pathParameters"]["challenge_id"]

        body = json.loads(event.get("body", "{}"))

        if not challenge_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "challenge_id is required"})
            }

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
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No valid fields to update"})
            }


        challenges_table.update_item(
            Key={"challenge_id": challenge_id},
            UpdateExpression="SET " + ", ".join(update_expressions),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names,
            ConditionExpression="attribute_exists(challenge_id)",
            ReturnValues="ALL_NEW"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Challenge updated successfully"})
        }

    except challenges_table.meta.client.exceptions.ConditionalCheckFailedException:
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
