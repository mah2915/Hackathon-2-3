"""
Authentication utility functions for the Todo Web App
"""

import re
from typing import Optional
from sqlmodel import Session, select
from ..models.user import User
from .password import verify_password


def is_valid_email(email: str) -> bool:
    """
    Validates if the provided email address has a valid format.

    Args:
        email: The email address to validate

    Returns:
        True if email format is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_password(password: str) -> bool:
    """
    Validates if the provided password meets security requirements.

    Args:
        password: The password to validate

    Returns:
        True if password meets requirements, False otherwise
    """
    # At least 8 characters, maximum 128
    if len(password) < 8 or len(password) > 128:
        return False

    # Contains at least one uppercase, one lowercase, one digit
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    return has_upper and has_lower and has_digit


def get_user_by_email_sync(session: Session, email: str) -> Optional[User]:
    """
    Retrieves a user by their email address - synchronous version.

    Args:
        session: Database session
        email: Email address to search for

    Returns:
        User object if found, None otherwise
    """
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    return user


async def get_user_by_email_async(async_session, email: str) -> Optional[User]:
    """
    Retrieves a user by their email address - asynchronous version.

    Args:
        async_session: Async database session
        email: Email address to search for

    Returns:
        User object if found, None otherwise
    """
    statement = select(User).where(User.email == email)
    result = await async_session.exec(statement)
    return result.first()


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticates a user by verifying their email and password.

    Args:
        session: Database session
        email: User's email address
        password: User's password (plain text - will be hashed and compared)

    Returns:
        User object if credentials are valid, None otherwise
    """
    user = get_user_by_email(session, email)

    if not user or not verify_password(password, user.password_hash):
        return None

    return user


def is_email_unique_sync(session: Session, email: str, exclude_user_id: Optional[str] = None) -> bool:
    """
    Checks if an email address is unique (not already taken by another user) - synchronous version.

    Args:
        session: Database session
        email: Email address to check
        exclude_user_id: Optional user ID to exclude from the check (for updates)

    Returns:
        True if email is unique, False if already exists
    """
    statement = select(User).where(User.email == email)

    if exclude_user_id:
        statement = statement.where(User.id != exclude_user_id)

    user = session.exec(statement).first()
    return user is None


async def is_email_unique_async(async_session, email: str, exclude_user_id: Optional[str] = None) -> bool:
    """
    Checks if an email address is unique (not already taken by another user) - asynchronous version.

    Args:
        async_session: Async database session
        email: Email address to check
        exclude_user_id: Optional user ID to exclude from the check (for updates)

    Returns:
        True if email is unique, False if already exists
    """
    statement = select(User).where(User.email == email)

    if exclude_user_id:
        statement = statement.where(User.id != exclude_user_id)

    result = await async_session.exec(statement)
    user = result.first()
    return user is None


def sanitize_user_input(input_str: str, max_length: int = 255) -> str:
    """
    Sanitizes user input by removing potentially harmful characters.

    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    # Remove potentially dangerous characters
    sanitized = input_str.strip()

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized