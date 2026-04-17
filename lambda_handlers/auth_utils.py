"""
Authentication utilities for JWT token management and password handling.

This module provides shared functions for:
- JWT token generation and validation
- Password hashing and verification
- Token extraction from API Gateway events
- AWS SSM Parameter Store integration for JWT secret
"""

import json
import boto3
import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
from typing import Tuple

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cache for JWT secret to avoid repeated SSM calls
_jwt_secret_cache = None

def get_jwt_secret() -> str:
    """
    Fetch JWT secret from AWS SSM Parameter Store.
    Caches the secret after first retrieval to minimize SSM calls.
    
    Returns:
        str: The JWT secret key
        
    Raises:
        Exception: If unable to fetch secret from SSM
    """
    global _jwt_secret_cache
    
    if _jwt_secret_cache is not None:
        return _jwt_secret_cache
    
    try:
        ssm = boto3.client('ssm', region_name='us-east-1')
        response = ssm.get_parameter(
            Name='/llmplatformsecurity/jwtsecret',
            WithDecryption=True
        )
        _jwt_secret_cache = response['Parameter']['Value']
        return _jwt_secret_cache
    except Exception as e:
        logger.error(f"Failed to fetch JWT secret from SSM: {str(e)}", exc_info=True)
        raise Exception("Failed to retrieve JWT secret")


def extract_token_from_event(event: dict) -> str:
    """
    Extract JWT token from API Gateway event Authorization header.
    
    Args:
        event: API Gateway Lambda proxy integration event
        
    Returns:
        str: The JWT token (without "Bearer " prefix)
        
    Raises:
        Exception: If Authorization header is missing or malformed
    """
    try:
        headers = event.get('headers', {})
        # Handle case-insensitive header names
        auth_header = headers.get('Authorization') or headers.get('authorization')
        
        if not auth_header:
            raise Exception("Missing authorization header")
        
        # Expected format: "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise Exception("Invalid authorization header format")
        
        return parts[1]
    except Exception as e:
        logger.warning(f"Token extraction failed: {str(e)}")
        raise Exception("Missing or invalid authorization header")


def validate_jwt(token: str, jwt_secret: str) -> Tuple[str, bool]:
    """
    Validate JWT token and extract user claims.
    
    Args:
        token: The JWT token to validate
        jwt_secret: The secret key for JWT validation
        
    Returns:
        Tuple[str, bool]: (username, is_admin)
        
    Raises:
        Exception: If token is invalid, expired, or malformed
    """
    try:
        # Decode and validate token
        # PyJWT automatically checks expiration and signature
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        
        username = payload.get('username')
        is_admin = payload.get('is_admin', False)
        
        if not username:
            raise Exception("Invalid token payload: missing username")
        
        return username, is_admin
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise Exception("Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise Exception("Invalid token")
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}", exc_info=True)
        raise Exception("Token validation failed")


def generate_jwt(username: str, is_admin: bool, jwt_secret: str) -> str:
    """
    Generate a new JWT token with 1-hour expiration.
    
    Args:
        username: The username to include in the token
        is_admin: Whether the user has admin privileges
        jwt_secret: The secret key for JWT signing
        
    Returns:
        str: The generated JWT token
    """
    try:
        now = datetime.utcnow()
        payload = {
            'username': username,
            'is_admin': is_admin,
            'iat': now,  # Issued at
            'exp': now + timedelta(hours=1)  # Expires in 1 hour
        }
        
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        return token
        
    except Exception as e:
        logger.error(f"JWT generation failed: {str(e)}", exc_info=True)
        raise Exception("Failed to generate token")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with default rounds (12).
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The bcrypt hashed password
    """
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing failed: {str(e)}", exc_info=True)
        raise Exception("Failed to hash password")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its bcrypt hash.
    
    Args:
        password: The plain text password to verify
        password_hash: The bcrypt hash to check against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}", exc_info=True)
        return False
