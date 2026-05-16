import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key
from auth_utils import get_jwt_secret, extract_token_from_event, validate_jwt

# DynamoDB setup
dynamo = boto3.resource("dynamodb")
CHALLENGE_SESSIONS_TABLE = os.environ['CHALLENGE_SESSIONS_TABLE']
PROMPTS_TABLE = os.environ['PROMPTS_TABLE']
challenge_sessions_table = dynamo.Table(CHALLENGE_SESSIONS_TABLE)
prompts_table = dynamo.Table(PROMPTS_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Get session chat history request received")
    
    # Authenticate and authorize (admin only)
    try:
        jwt_secret = get_jwt_secret()
        token = extract_token_from_event(event)
        username, is_admin = validate_jwt(token, jwt_secret)
        logger.info(f"Authenticated user: {username}, is_admin: {is_admin}")
        
        if not is_admin:
            logger.warning(f"Non-admin user {username} attempted to get session chat history")
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
        # Extract challenge_id and session_id from path parameters
        path_params = event.get("pathParameters", {})
        challenge_id = path_params.get("challenge_id")
        session_id = path_params.get("session_id")
        
        if not challenge_id or not session_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "challenge_id and session_id are required"})
            }
        
        logger.info(f"Fetching chat history for challenge: {challenge_id}, session: {session_id}")
        
        # Verify session exists and belongs to the specified challenge
        try:
            session_response = challenge_sessions_table.get_item(
                Key={"session_id": session_id}
            )
            session_item = session_response.get("Item")
            
            if not session_item:
                logger.warning(f"Session {session_id} not found")
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": "Session not found"})
                }
            
            # Verify session belongs to the specified challenge
            if session_item.get("challenge_id") != challenge_id:
                logger.warning(f"Session {session_id} does not belong to challenge {challenge_id}")
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": "Session not found for the specified challenge"})
                }
            
            logger.info(f"Session verified: {session_id} belongs to challenge {challenge_id}")
            
        except Exception as e:
            logger.error(f"Error fetching session: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Error verifying session"})
            }
        
        # Query PromptsTable for all prompts in this session
        response = prompts_table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ScanIndexForward=True  # ascending order by timestamp (chronological)
        )
        
        items = response.get("Items", [])
        logger.info(f"Retrieved {len(items)} prompts for session {session_id}")
        
        # Format chat history
        chat_history = []
        for item in items:
            chat_history.append({
                "prompt_id": item.get("prompt_id"),
                "prompt_text": item.get("prompt_text"),
                "response_text": item.get("response_text"),
                "verified_response": item.get("verified_response"),
                "timestamp": item.get("timestamp")
            })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "challenge_id": challenge_id,
                "session_id": session_id,
                "user_id": session_item.get("user_id"),
                "status": session_item.get("status"),
                "started_at": session_item.get("started_at"),
                "completed_at": session_item.get("completed_at"),
                "chat_history": chat_history,
                "message_count": len(chat_history)
            })
        }
    
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
