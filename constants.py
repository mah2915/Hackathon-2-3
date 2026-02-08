"""
Authentication constants and configuration for the Todo Web App
"""

# JWT Configuration
JWT_ALGORITHM = "HS256"
DEFAULT_JWT_EXPIRATION_HOURS = 24
REFRESH_TOKEN_EXPIRATION_DAYS = 7

# Password Configuration
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# User Configuration
MAX_EMAIL_LENGTH = 254
MIN_EMAIL_LENGTH = 5

# Rate Limiting
LOGIN_ATTEMPTS_LIMIT = 5
LOGIN_ATTEMPTS_WINDOW = 900  # 15 minutes in seconds

# Token Types
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# Error Messages
INVALID_CREDENTIALS_ERROR = "Invalid email or password"
ACCOUNT_LOCKED_ERROR = "Account temporarily locked due to multiple failed login attempts"
TOKEN_EXPIRED_ERROR = "Token has expired"
INVALID_TOKEN_ERROR = "Invalid token"
INSUFFICIENT_PERMISSIONS_ERROR = "Insufficient permissions"