"""
FastAPI Dependency Injection

Common dependencies for authentication, database, and services.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthService, TokenData, get_auth_service
from app.core.config import DevSettings, get_settings
from app.core.database import get_db
from app.core.encryption import EncryptionService, get_encryption_service


# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenData:
    """
    Validate JWT token and return current user data.
    """
    try:
        token_data = auth_service.verify_token(credentials.credentials)
        return token_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Type aliases for dependency injection
CurrentUser = Annotated[TokenData, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[DevSettings, Depends(get_settings)]
Encryption = Annotated[EncryptionService, Depends(get_encryption_service)]
Auth = Annotated[AuthService, Depends(get_auth_service)]
