"""
Authentication Service

Handles password hashing with Argon2id and JWT token management.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings


class TokenData(BaseModel):
    """JWT token payload."""
    user_id: str
    email: str
    exp: datetime


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthService:
    """
    Authentication service using Argon2id for password hashing
    and JWT for session tokens.
    
    Security Notes:
    - Argon2id is the winner of the Password Hashing Competition
    - JWT tokens are short-lived (24h default)
    - Passwords are never stored in plaintext
    """

    def __init__(self):
        self.settings = get_settings()
        self.password_hasher = PasswordHasher(
            time_cost=3,      # Number of iterations
            memory_cost=65536, # 64 MB memory usage
            parallelism=4,     # Parallel threads
            hash_len=32,       # Output hash length
            salt_len=16,       # Salt length
        )

    def hash_password(self, password: str) -> str:
        """
        Hash a password using Argon2id.
        
        Args:
            password: Plaintext password
            
        Returns:
            Argon2id hash string (includes salt and parameters)
        """
        return self.password_hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plaintext password to verify
            password_hash: Stored Argon2id hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            self.password_hasher.verify(password_hash, password)
            return True
        except VerifyMismatchError:
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        """
        Check if password hash needs updating due to parameter changes.
        
        Args:
            password_hash: Current stored hash
            
        Returns:
            True if hash should be updated with new parameters
        """
        return self.password_hasher.check_needs_rehash(password_hash)

    def create_access_token(
        self, 
        user_id: str, 
        email: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User's UUID
            email: User's email
            expires_delta: Token lifetime (default from settings)
            
        Returns:
            Encoded JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=self.settings.jwt_expiration_hours)

        expire = datetime.now(timezone.utc) + expires_delta

        payload: dict[str, Any] = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        return jwt.encode(
            payload,
            self.settings.secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def verify_token(self, token: str) -> TokenData:
        """
        Verify and decode a JWT token.
        
        Args:
            token: Encoded JWT token
            
        Returns:
            TokenData with user information
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            
            user_id = payload.get("sub")
            email = payload.get("email")
            exp = payload.get("exp")
            
            if user_id is None or email is None:
                raise AuthenticationError("Invalid token payload")

            return TokenData(
                user_id=user_id,
                email=email,
                exp=datetime.fromtimestamp(exp, tz=timezone.utc),
            )

        except JWTError as e:
            raise AuthenticationError(f"Token verification failed: {e}")

    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """
        Validate password meets minimum requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < self.settings.password_min_length:
            return False, f"Password must be at least {self.settings.password_min_length} characters"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        return True, ""


# Singleton instance
_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    """Get or create auth service singleton."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
