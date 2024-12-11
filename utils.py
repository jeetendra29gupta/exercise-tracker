import logging
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from dotenv import load_dotenv
from flask import session, redirect, url_for, request, flash

from log_config import setup_logging

# Load environment variables from a .env file
load_dotenv()

# Constants for JWT handling and security
SECRET_KEY = os.getenv("SECRET_KEY", "Secret_Key-2024")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# JWT Claim Keys
SUBJECT_KEY = "sub"
EXPIRATION_KEY = "exp"

setup_logging()
logger = logging.getLogger(__name__)


# Utility functions for password hashing and verification
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.

    Args:
        plain_password (str): The password to verify.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the password is valid, False otherwise.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_token(subject: str) -> dict:
    """
    Create both access and refresh JWT tokens for a given subject.

    Args:
        subject (str): The subject (typically a user ID or username).

    Returns:
        dict: A dictionary containing the access token and refresh token.
    """
    now = datetime.now(timezone.utc)
    expiration_time_access = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expiration_time_refresh = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    # Create access token
    access_token = jwt.encode(
        {SUBJECT_KEY: subject, EXPIRATION_KEY: expiration_time_access},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    # Create refresh token
    refresh_token = jwt.encode(
        {SUBJECT_KEY: subject, EXPIRATION_KEY: expiration_time_refresh},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "token_type": "bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def get_current_user(token: str) -> str:
    """
    Extract the current user from the JWT token.

    Args:
        token (str): The JWT token.

    Returns:
        str: The username (subject) embedded in the token.

    Raises:
        ValueError: If the token is invalid or expired.
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get(SUBJECT_KEY)

        if not username:
            raise ValueError("Invalid token: No subject found")

        return username

    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def session_token_required(func):
    """
        Decorator to validate session and token before accessing the route.
        Validate session and token to ensure the user is authenticated.

        Args:
            - func: The route function to be decorated.

        Returns:
            - The original function if valid session and token; otherwise, redirects to login page.
        """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('user_name'):
            flash("Invalid session: Attempt to access with no session.", "Error")
            logger.error("Invalid session: Attempt to access with no session.")
            return redirect(url_for('user.login'))

        token = request.cookies.get('token')
        if not token:
            flash("Invalid token: Attempt to access with no token.", "Error")
            logger.error("Invalid token: Attempt to access with no token.")
            return redirect(url_for('user.login'))

        try:
            cookies_username = get_current_user(token)
            if cookies_username != session.get('user_name'):
                flash(f"Token mismatch: Attempt to access with invalid token for user {session.get('user_name')}",
                      "Error")
                logger.error(
                    f"Token mismatch: Attempt to access with invalid token for user {session.get('user_name')}")
                return redirect(url_for('user.login'))
        except Exception as e:
            flash(f"Token validation error: {str(e)}", "Error")
            logger.error(f"Token validation error: {str(e)}")
            session.pop('user_name', None)
            return redirect(url_for('user.login'))

        logger.info(f"Session and token validated successfully for user {session.get('user_name')}.")
        return func(*args, **kwargs)

    return wrapper
