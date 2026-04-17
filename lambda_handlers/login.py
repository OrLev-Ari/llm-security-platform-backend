# Lambda: LoginLambdaFunction
import json
import boto3
import os
import logging
from auth_utils import get_jwt_secret, generate_jwt, verify_password

dynamo = boto3.resource("dynamodb")
USERS_TABLE = os.environ["USERS_TABLE"]
users_table = dynamo.Table(USERS_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Login request received")
    try:
        body = json.loads(event.get("body", "{}"))
        logger.debug(f"Request body parsed successfully")
        
        # Validate required fields
        if "username" not in body or "password" not in body:
            logger.warning("Missing required fields in login request")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required fields",
                    "fields": ["username", "password"] if "username" not in body and "password" not in body
                            else ["username"] if "username" not in body
                            else ["password"]
                })
            }
        
        username = body["username"].strip().lower()  # Normalize to lowercase
        password = body["password"]
        
        # Validate username is not empty
        if not username:
            logger.warning("Login attempt with empty username")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Username cannot be empty"})
            }
        
        logger.info(f"Attempting login for user: {username}")
        
        # Get user from database
        try:
            response = users_table.get_item(Key={"username": username})
            if "Item" not in response:
                # User not found - use generic error message for security
                logger.warning(f"Login failed: User not found - {username}")
                return {
                    "statusCode": 401,
                    "body": json.dumps({"error": "Invalid username or password"})
                }
            
            user = response["Item"]
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}", exc_info=True)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Internal server error"})
            }
        
        # Verify password
        password_hash = user.get("passwordHash", "")
        if not verify_password(password, password_hash):
            logger.warning(f"Login failed: Invalid password for user - {username}")
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Invalid username or password"})
            }
        
        # Get JWT secret from SSM
        try:
            jwt_secret = get_jwt_secret()
        except Exception as e:
            logger.error(f"Failed to get JWT secret: {str(e)}", exc_info=True)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Internal server error"})
            }
        
        # Generate JWT token
        is_admin = user.get("is_admin", False)
        token = generate_jwt(username, is_admin, jwt_secret)
        
        logger.info(f"User logged in successfully: {username}")
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "token": token,
                "username": username,
                "is_admin": is_admin
            })
        }
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in login request body")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON body"})
        }
    except Exception as e:
        logger.error("Login failed", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
