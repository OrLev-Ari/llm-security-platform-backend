import json
import boto3
import os
import logging
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# DynamoDB setup
dynamo = boto3.resource("dynamodb")
CHALLENGE_SESSIONS_TABLE = os.environ['CHALLENGE_SESSIONS_TABLE']
CHALLENGE_SCORES_TABLE = os.environ['CHALLENGE_SCORES_TABLE']
challenge_sessions_table = dynamo.Table(CHALLENGE_SESSIONS_TABLE)
challenge_scores_table = dynamo.Table(CHALLENGE_SCORES_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def convert_decimal(obj):
    """Convert Decimal objects to int or float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def lambda_handler(event, context):
    logger.info("List completed sessions request received")
    
    # Authenticate and authorize (admin only)
    try:
        jwt_secret = get_jwt_secret()
        token = extract_token_from_event(event)
        username, is_admin = validate_jwt(token, jwt_secret)
        logger.info(f"Authenticated user: {username}, is_admin: {is_admin}")
        
        if not is_admin:
            logger.warning(f"Non-admin user {username} attempted to list completed sessions")
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Forbidden: Admin access required"})
            }
    except Exception as e:
        logger.warning(f"Authentication failed: {str(e)}")
        return {
            "statusCode": 401,
            "body": json.dumps({"error": str(e)})
        }
    
    try:
        # Extract challenge_id from path parameters
        challenge_id = event.get("pathParameters", {}).get("challenge_id")
        if not challenge_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "challenge_id is required"})
            }
        
        # Extract optional limit from query parameters
        query_params = event.get("queryStringParameters") or {}
        limit_str = query_params.get("limit", "50")
        
        try:
            limit = int(limit_str)
            # Enforce max limit of 100
            if limit > 100:
                limit = 100
            elif limit < 1:
                limit = 50
        except ValueError:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "limit must be a valid integer"})
            }
        
        logger.info(f"Fetching completed sessions for challenge: {challenge_id}, limit: {limit}")
        
        # Query ChallengeSessionsTable using ChallengeStatusIndex GSI
        response = challenge_sessions_table.query(
            IndexName="ChallengeStatusIndex",
            KeyConditionExpression=Key("challenge_id").eq(challenge_id),
            ScanIndexForward=False  # descending order by completed_at (most recent first)
        )
        
        items = response.get("Items", [])
        logger.info(f"Retrieved {len(items)} sessions for challenge {challenge_id}")
        
        # Filter for completed sessions only
        completed_sessions = [item for item in items if item.get("status") == "completed"]
        logger.info(f"Found {len(completed_sessions)} completed sessions")
        
        # Apply limit
        completed_sessions = completed_sessions[:limit]
        
        # Enrich with score data from ChallengeScoresTable
        result_sessions = []
        for session in completed_sessions:
            user_id = session.get("user_id")
            session_data = {
                "session_id": session.get("session_id"),
                "user_id": user_id,
                "completed_at": session.get("completed_at"),
                "started_at": session.get("started_at")
            }
            
            # Try to get score from ChallengeScoresTable
            if user_id:
                try:
                    score_response = challenge_scores_table.get_item(
                        Key={
                            "user_id": user_id,
                            "challenge_id": challenge_id
                        }
                    )
                    score_item = score_response.get("Item")
                    if score_item:
                        session_data["score"] = convert_decimal(score_item.get("score", 0))
                        session_data["prompt_count"] = convert_decimal(score_item.get("prompt_count", 0))
                        session_data["time_seconds"] = convert_decimal(score_item.get("time_seconds", 0))
                except Exception as e:
                    logger.warning(f"Could not fetch score for user {user_id}: {str(e)}")
                    session_data["score"] = None
                    session_data["prompt_count"] = None
                    session_data["time_seconds"] = None
            
            result_sessions.append(session_data)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "challenge_id": challenge_id,
                "sessions": result_sessions,
                "count": len(result_sessions)
            })
        }
    
    except Exception as e:
        logger.error(f"Error fetching completed sessions: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
