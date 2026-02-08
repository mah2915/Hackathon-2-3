"""
JWT token creation and verification utilities.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from uuid import UUID
from app.config import get_settings


settings = get_settings()


def create_access_token(user_id: UUID, email: str) -> str:
    """
    Create a JWT access token for authenticated user.

    Args:
        user_id: User's unique identifier
        email: User's email address

    Returns:
        Encoded JWT token string
    """
    expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": str(user_id),  # Subject (user ID)
        "email": email,
        "exp": expire,  # Expiration time
        "iat": datetime.utcnow()  # Issued at
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        Decoded token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
