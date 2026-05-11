import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# DynamoDB setup
dynamo = boto3.resource("dynamodb")
CHALLENGE_SCORES_TABLE = os.environ['CHALLENGE_SCORES_TABLE']
GLOBAL_SCORES_TABLE = os.environ['GLOBAL_SCORES_TABLE']
challenge_scores_table = dynamo.Table(CHALLENGE_SCORES_TABLE)
global_scores_table = dynamo.Table(GLOBAL_SCORES_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Get user scores request received")
    
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
        
        logger.info(f"Fetching scores for user: {username}, limit: {limit}")
        
        # Get global total score from GlobalScoresTable
        global_score_resp = global_scores_table.get_item(Key={"user_id": username})
        global_item = global_score_resp.get("Item")
        
        total_score = global_item.get("total_score", 0) if global_item else 0
        challenges_completed = global_item.get("challenges_completed", 0) if global_item else 0
        
        # Query ChallengeScoresTable with user_id as PK
        query_params_ddb = {
            "KeyConditionExpression": Key("user_id").eq(username)
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
        
        response = challenge_scores_table.query(**query_params_ddb)
        items = response.get("Items", [])
        
        logger.info(f"Retrieved {len(items)} scores for user {username}")
        
        # Build scores list
        scores = []
        for item in items:
            scores.append({
                "challenge_id": item["challenge_id"],
                "score": item["score"],
                "prompt_count": item["prompt_count"],
                "time_seconds": item["time_seconds"],
                "completed_at": item["completed_at"]
            })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "total_score": total_score,
                "challenges_completed": challenges_completed,
                "scores": scores
            })
        }
    
    except Exception as e:
        logger.error(f"Error fetching user scores: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
