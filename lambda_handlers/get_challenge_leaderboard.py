import json
import boto3
import os
import logging
import base64
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# DynamoDB setup
dynamo = boto3.resource("dynamodb")
CHALLENGE_SCORES_TABLE = os.environ['CHALLENGE_SCORES_TABLE']
challenge_scores_table = dynamo.Table(CHALLENGE_SCORES_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def convert_decimal(obj):
    """Convert Decimal objects to int or float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def lambda_handler(event, context):
    logger.info("Get challenge leaderboard request received")
    
    # Authenticate user
    try:
        jwt_secret = get_jwt_secret()
        token = extract_token_from_event(event)
        username, is_admin = validate_jwt(token, jwt_secret)
        logger.info(f"Authenticated user: {username}")
    except Exception as e:
        logger.warning(f"Authentication failed: {str(e)}")
        return {
            "statusCode": 401,
            "body": json.dumps({"error": str(e)})
        }
    
    try:
        # Extract challenge_id from path parameters
        challenge_id = event.get("pathParameters", {}).get("id")
        if not challenge_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "challenge_id is required"})
            }
        
        # Extract optional limit from query parameters
        query_params = event.get("queryStringParameters") or {}
        limit = query_params.get("limit")
        
        logger.info(f"Fetching leaderboard for challenge: {challenge_id}, limit: {limit}")
        
        # Query GSI "ChallengeLeaderboardIndex" with challenge_id as PK
        query_params_ddb = {
            "IndexName": "ChallengeLeaderboardIndex",
            "KeyConditionExpression": Key("challenge_id").eq(challenge_id)
        }
        
        response = challenge_scores_table.query(**query_params_ddb)
        items = response.get("Items", [])
        
        logger.info(f"Retrieved {len(items)} scores for challenge {challenge_id}")
        
        # Sort by score descending in Python
        sorted_items = sorted(items, key=lambda x: x.get("score", 0), reverse=True)
        
        # Apply limit if provided
        if limit:
            try:
                limit_int = int(limit)
                sorted_items = sorted_items[:limit_int]
            except ValueError:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "limit must be a valid integer"})
                }
        
        # Build leaderboard with ranks
        leaderboard = []
        for rank, item in enumerate(sorted_items, start=1):
            leaderboard.append({
                "rank": rank,
                "user_id": item["user_id"],
                "score": convert_decimal(item["score"]),
                "prompt_count": convert_decimal(item["prompt_count"]),
                "time_seconds": convert_decimal(item["time_seconds"]),
                "completed_at": item["completed_at"]
            })
        
        return {
            "statusCode": 200,
            "body": json.dumps({"users": leaderboard})
        }
    
    except Exception as e:
        logger.error(f"Error fetching challenge leaderboard: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
