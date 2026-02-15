"""
Simplified Auth Routes for SQLite
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import Auth, DbSession, Encryption
from app.api.schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from app.models.database import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserCreate,
    db: DbSession,
    auth: Auth,
    encryption: Encryption,
):
    """Register a new user account."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Validate password
    is_valid, error = auth.validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # Create user
    user = User(
        email=request.email,
        password_hash=auth.hash_password(request.password),
        encryption_key_salt=encryption.generate_salt(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLogin,
    db: DbSession,
    auth: Auth,
):
    """Authenticate user and return JWT token."""
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not auth.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = auth.create_access_token(str(user.id), user.email)
    token_data = auth.verify_token(token)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_at=token_data.exp,
    )
