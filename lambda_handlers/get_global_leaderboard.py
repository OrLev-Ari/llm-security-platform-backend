import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# DynamoDB setup
dynamo = boto3.resource("dynamodb")
GLOBAL_SCORES_TABLE = os.environ['GLOBAL_SCORES_TABLE']
global_scores_table = dynamo.Table(GLOBAL_SCORES_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Get global leaderboard request received")
    
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
        # Extract optional limit from query parameters
        query_params = event.get("queryStringParameters") or {}
        limit = query_params.get("limit")
        
        logger.info(f"Fetching global leaderboard, limit: {limit}")
        
        # Scan the GlobalScoresTable to get all users
        response = global_scores_table.scan()
        items = response.get("Items", [])
        
        logger.info(f"Retrieved {len(items)} users for global leaderboard")
        
        # Sort by total_score descending in Python
        sorted_items = sorted(items, key=lambda x: x.get("total_score", 0), reverse=True)
        
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
                "total_score": item["total_score"],
                "challenges_completed": item["challenges_completed"],
                "last_updated": item["last_updated"]
            })
        
        return {
            "statusCode": 200,
            "body": json.dumps({"users": leaderboard})
        }
    
    except Exception as e:
        logger.error(f"Error fetching global leaderboard: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
