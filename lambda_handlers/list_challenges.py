import json
import boto3
import os
import logging

# ---------- Setup ----------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo = boto3.resource("dynamodb")
CHALLENGES_TABLE = os.environ["CHALLENGES_TABLE"]
challenges_table = dynamo.Table(CHALLENGES_TABLE)

def lambda_handler(event, context):
    try:
        logger.info("Listing challenges")

        # ---------- Scan table ----------
        response = challenges_table.scan(
            ProjectionExpression="title, description, challenge_id"
        )

        items = response.get("Items", [])

        return {
            "statusCode": 200,
            "body": json.dumps({
                "items": items
            })
        }

    except Exception as e:
        logger.exception("Failed to list challenges" + str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
