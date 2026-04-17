# Lambda: RegisterLambdaFunction
import json
import boto3
import os
import logging
import re
from datetime import datetime
from auth_utils import hash_password

dynamo = boto3.resource("dynamodb")
USERS_TABLE = os.environ["USERS_TABLE"]
users_table = dynamo.Table(USERS_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def validate_password(password):
    """
    Validate password meets requirements:
    - Minimum 7 characters
    - At least 6 letters
    - At least 1 number
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 7:
        return False, "Password must be at least 7 characters long"
    
    letter_count = sum(1 for c in password if c.isalpha())
    number_count = sum(1 for c in password if c.isdigit())
    
    if letter_count < 6:
        return False, "Password must contain at least 6 letters"
    
    if number_count < 1:
        return False, "Password must contain at least 1 number"
    
    return True, None


def lambda_handler(event, context):
    logger.info("Registration request received")
    try:
        body = json.loads(event.get("body", "{}"))
        logger.debug("Request body parsed successfully")
        
        # Validate required fields
        required_fields = ["username", "password", "email", "country", "dateOfBirth"]
        missing_fields = [f for f in required_fields if f not in body]
        if missing_fields:
            logger.warning(f"Missing required fields in registration: {missing_fields}")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required fields",
                    "fields": missing_fields
                })
            }
        
        username = body["username"].strip().lower()  # Normalize to lowercase
        password = body["password"]
        email = body["email"].strip()
        country = body["country"].strip()
        date_of_birth = body["dateOfBirth"]
        
        # Validate username is not empty after stripping
        if not username:
            logger.warning("Registration attempt with empty username")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Username cannot be empty"})
            }
        
        logger.info(f"Attempting registration for username: {username}")
        
        # Validate password requirements
        is_valid, error_message = validate_password(password)
        if not is_valid:
            logger.warning(f"Password validation failed for {username}: {error_message}")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_message})
            }
        
        # Check if username already exists
        try:
            response = users_table.get_item(Key={"username": username})
            if "Item" in response:
                logger.warning(f"Registration failed: Username already exists - {username}")
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Username already exists"})
                }
        except Exception as e:
            logger.error(f"Error checking username existence: {str(e)}", exc_info=True)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Internal server error"})
            }
        
        # Hash password
        logger.debug(f"Hashing password for user: {username}")
        password_hash = hash_password(password)
        
        # Create user
        now = int(datetime.utcnow().timestamp())
        logger.info(f"Creating user record in database for: {username}")
        users_table.put_item(
            Item={
                "username": username,
                "passwordHash": password_hash,
                "email": email,
                "country": country,
                "dateOfBirth": date_of_birth,
                "is_admin": False,  # Regular users are never admins
                "createdAt": now
            }
        )
        
        logger.info(f"User registered successfully: {username}")
        
        return {
            "statusCode": 201,
            "body": json.dumps({
                "message": "User registered successfully",
                "username": username
            })
        }
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in registration request body")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON body"})
        }
    except Exception as e:
        logger.error("Registration failed", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
