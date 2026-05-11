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
        
        # Query GSI "GlobalLeaderboardIndex" with fixed PK "GLOBAL", sorted by total_score descending
        query_params_ddb = {
            "IndexName": "GlobalLeaderboardIndex",
            "KeyConditionExpression": Key("leaderboard_type").eq("GLOBAL"),
            "ScanIndexForward": False  # Descending order by total_score
        }
        
        # Apply limit if provided
        if limit:
            try:
                query_params_ddb["Limit"] = int(limit)
            except ValueError:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "limit must be a valid integer"})
                }
        
        response = global_scores_table.query(**query_params_ddb)
        items = response.get("Items", [])
        
        logger.info(f"Retrieved {len(items)} users for global leaderboard")
        
        # Build leaderboard with ranks
        leaderboard = []
        for rank, item in enumerate(items, start=1):
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
