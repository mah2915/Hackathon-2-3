"""
Authentication middleware for the Todo Web App
"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from uuid import UUID
from .jwt import verify_token
from .constants import INVALID_TOKEN_ERROR, TOKEN_EXPIRED_ERROR


# Security scheme for API docs
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials from request header

    Returns:
        Dictionary containing user information from token

    Raises:
        HTTPException: If token is invalid, expired, or missing
    """
    token = credentials.credentials

    # Verify the token
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_ERROR,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token has expired
    import time
    current_time = time.time()
    exp_time = payload.get("exp", 0)

    if exp_time < current_time:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=TOKEN_EXPIRED_ERROR,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user information from payload
    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_ERROR,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return user information
    return {
        "user_id": user_id,
        "email": email,
        "token_payload": payload
    }


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to get only the current user's ID from JWT token.

    Args:
        credentials: HTTP authorization credentials from request header

    Returns:
        User ID as a string

    Raises:
        HTTPException: If token is invalid, expired, or missing
    """
    user_data = get_current_user(credentials)
    return user_data["user_id"]


def require_authenticated_user():
    """
    Simple dependency to require authentication without returning user data.
    Use this when you just need to ensure the user is authenticated but don't need their data.
    """
    def auth_dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        return current_user
    return auth_dependency


def verify_user_owns_resource(user_id_from_token: str, user_id_from_request: str) -> bool:
    """
    Verify that the authenticated user owns the requested resource.

    Args:
        user_id_from_token: User ID extracted from JWT token
        user_id_from_request: User ID from request path parameters

    Returns:
        True if user IDs match, raises HTTPException if they don't
    """
    if user_id_from_token != user_id_from_request:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - cannot access other users' data"
        )
    return True


def get_optional_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Dependency to get the current user if authenticated, but doesn't require authentication.
    Returns None if no token is provided or if token is invalid.
    """
    try:
        token = credentials.credentials
        payload = verify_token(token)

        if payload is None:
            return None

        # Check if token has expired
        import time
        current_time = time.time()
        exp_time = payload.get("exp", 0)

        if exp_time < current_time:
            return None

        # Extract user information from payload
        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            return None

        # Return user information
        return {
            "user_id": user_id,
            "email": email,
            "token_payload": payload
        }
    except HTTPException:
        # If there's an HTTP exception (e.g., no token provided), return None
        return None
    except Exception:
        # For any other exception, return None
        return None